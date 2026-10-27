# Tasks Service

Backend-сервис учёта задач пользователей: пользователи, их задачи, смена статуса, удаление и статистика по статусам.

Стек: Python 3.13, FastAPI, PostgreSQL 16, async SQLAlchemy 2 (asyncpg), Alembic, Pydantic 2, pytest, Docker Compose, uv, ruff, mypy.

## Запуск

```bash
docker compose up --build
```

- API: http://localhost:8000 (корень перенаправляет на Swagger)
- Swagger: http://localhost:8000/docs
- OpenAPI-схема: http://localhost:8000/openapi.json

Нужен Docker Compose 2.24+: в `env_file` используется опциональный файл (`required: false`).

Ручная настройка не нужна. Compose берёт переменные из `.env.example`, а если рядом лежит `.env`, его значения имеют приоритет. Сервисы стартуют по порядку:

1. `postgres` — ждём, пока пройдёт healthcheck `pg_isready`;
2. `migrations` — `alembic upgrade head`, после чего контейнер завершается;
3. `api` — стартует только после успешного завершения миграций и имеет собственный healthcheck на `/healthcheck`.

Postgres публикуется на хост на порту `5440` (`DB_PORT`): стандартный 5432 часто уже занят локальной базой.

Остановить и удалить данные: `docker compose down -v`.

### Локально, без Docker для приложения

Нужен [uv](https://docs.astral.sh/uv/).

```bash
uv sync          # зависимости, включая dev
make prepare     # .env из .env.example
make up          # postgres в docker
make migrate     # alembic upgrade head
make runserver   # uvicorn с --reload на :8000
```

## Тесты

Тесты работают с настоящим PostgreSQL. Только через Docker:

```bash
make test-docker          # = docker compose run --rm --build tests
```

Локально:

```bash
uv sync                   # зависимости, включая dev
make prepare              # .env из .env.example (без него настройки не загрузятся)
make up                   # postgres в docker, если ещё не запущен
make test                 # = uv run pytest -vv --cov
```

Как устроена тестовая БД:

- **Отдельная база.** Перед прогоном тесты создают базу `<DB_NAME>_test`, а после удаляют её. Рабочую базу тесты не трогают.
- **Схема.** Строится через `Base.metadata.create_all`. Соответствие миграций моделям проверяет `alembic check` в CI.
- **Изоляция.** Каждый тест выполняется во внешней транзакции, которая откатывается в конце. Коммиты внутри use case'ов попадают в savepoint (`join_transaction_mode='create_savepoint'`).
- **Подключение приложения.** Сессия подменяется через `app.dependency_overrides`, запросы идут через `httpx.AsyncClient` с `ASGITransport`.

Линтеры: `make lint` (ruff check, ruff format --check, mypy); автоисправление: `make format`.

## Переменные окружения

| Переменная         | Описание                                    | Значение в `.env.example` |
|--------------------|---------------------------------------------|---------------------------|
| `DB_HOST`          | хост PostgreSQL                             | `localhost`               |
| `DB_PORT`          | порт PostgreSQL                             | `5440`                    |
| `DB_NAME`          | имя базы                                    | `tasks`                   |
| `DB_USERNAME`      | пользователь PostgreSQL                     | `postgres`                |
| `DB_PASSWORD`      | пароль PostgreSQL                           | `postgres`                |
| `LOG_LEVEL`        | `DEBUG` / `INFO` / `WARNING` / `ERROR`      | `INFO`                    |
| `APPLICATION_NAME` | имя приложения в `pg_stat_activity`, опционально | `tasks_service` (по умолчанию) |

Внутри compose-сети `DB_HOST` и `DB_PORT` переопределяются на `postgres:5432`. Значения `DB_PORT`, `DB_NAME`, `DB_USERNAME` и `DB_PASSWORD` из `.env` compose подставляет и в контейнер postgres.

## API

| Метод    | Путь                            | Успех | Ошибки          |
|----------|---------------------------------|-------|-----------------|
| `POST`   | `/users`                        | 201   | 409, 422        |
| `GET`    | `/users/{user_id}`              | 200   | 404, 422        |
| `POST`   | `/users/{user_id}/tasks`        | 201   | 404, 422        |
| `GET`    | `/users/{user_id}/tasks`        | 200   | 404, 422        |
| `GET`    | `/users/{user_id}/tasks/stats`  | 200   | 404, 422        |
| `PATCH`  | `/tasks/{task_id}/status`       | 200   | 404, 422        |
| `DELETE` | `/tasks/{task_id}`              | 200   | 404, 422        |
| `GET`    | `/healthcheck`                  | 200   | —               |

Ошибки возвращаются в стандартном формате FastAPI `{"detail": "..."}`. При ошибке валидации (422) `detail` содержит список ошибок по полям. Все ответы с ошибками описаны в OpenAPI.

### Примеры запросов

Примеры идут сценарием: если выполнить их по порядку на пустой базе, ответы совпадут с показанными, кроме дат.

Создать пользователя:

```bash
curl -X POST http://localhost:8000/users \
  -H 'Content-Type: application/json' \
  -d '{"email": "user@example.com", "name": "Ivan"}'
```
```json
{"id": 1, "email": "user@example.com", "name": "Ivan", "created_at": "2026-10-27T12:26:15.285231Z"}
```

Повторный email (в любом регистре) — `409`:

```json
{"detail": "Пользователь с таким email уже существует"}
```

Получить пользователя (если его нет — `404 {"detail": "Пользователь не найден"}`):

```bash
curl http://localhost:8000/users/1
```

Создать задачу:

```bash
curl -X POST http://localhost:8000/users/1/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title": "Подготовить отчет", "description": "Собрать данные за неделю"}'
```
```json
{
  "id": 1,
  "user_id": 1,
  "title": "Подготовить отчет",
  "description": "Собрать данные за неделю",
  "status": "new",
  "created_at": "2026-10-27T12:26:15.321014Z",
  "updated_at": "2026-10-27T12:26:15.321014Z"
}
```

Обновить статус (неизвестный статус — `422`, задачи нет — `404`):

```bash
curl -X PATCH http://localhost:8000/tasks/1/status \
  -H 'Content-Type: application/json' \
  -d '{"status": "done"}'
```
```json
{
  "id": 1,
  "user_id": 1,
  "title": "Подготовить отчет",
  "description": "Собрать данные за неделю",
  "status": "done",
  "created_at": "2026-10-27T12:26:15.321014Z",
  "updated_at": "2026-10-27T12:26:15.329854Z"
}
```

Список задач с фильтром по статусу и пагинацией:

```bash
curl 'http://localhost:8000/users/1/tasks?status=done&limit=10&offset=0'
```
```json
{
  "items": [
    {
      "id": 1,
      "user_id": 1,
      "title": "Подготовить отчет",
      "description": "Собрать данные за неделю",
      "status": "done",
      "created_at": "2026-10-27T12:26:15.321014Z",
      "updated_at": "2026-10-27T12:26:15.329854Z"
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

Параметры списка:

- `status` — необязательный, одно из `new`, `in_progress`, `done`, `cancelled`;
- `limit` — от 1 до 100, по умолчанию 10;
- `offset` — от 0, по умолчанию 0;
- `total` — сколько всего задач подходит под фильтр.

Задачи отсортированы от новых к старым.

Статистика (статусы без задач приходят с нулём):

```bash
curl http://localhost:8000/users/1/tasks/stats
```
```json
{"total": 1, "new": 0, "in_progress": 0, "done": 1, "cancelled": 0}
```

Удалить задачу:

```bash
curl -X DELETE http://localhost:8000/tasks/1
```
```json
{"ok": true}
```

Повторное удаление той же задачи вернёт `404 {"detail": "Задача не найдена"}`.

## Архитектура

Код разбит на доменные пакеты, внутри каждого — слои `api → logic (use cases) → repositories`:

```
src/
├── main.py                 # FastAPI-приложение, lifespan, подключение роутеров
├── core/                   # общая инфраструктура
│   ├── api/routers.py      # сборка роутеров доменов
│   ├── database/           # Base + naming convention + mixins, engine, get_db_session/SessionDep
│   ├── schemas/            # BaseFromAttrsModel, ErrorResponseSchema
│   ├── settings/           # pydantic-settings, structlog
│   ├── use_cases/base.py   # BaseSessionAsyncUseCase
│   └── constants.py
├── healthcheck/api.py
├── users/
│   ├── api/users.py        # эндпоинты: HTTP ⇄ use case, маппинг доменных ошибок в HTTP-коды
│   ├── logic/use_cases/    # сценарии: CreateUserUseCase, GetUserUseCase
│   ├── repositories/       # запросы к БД, возвращают DTO
│   ├── models/             # SQLAlchemy-модели
│   ├── dtos/               # данные между репозиторием и логикой
│   ├── schemas/            # контракты API (вход/выход, валидация)
│   ├── exceptions.py
│   └── constants.py
├── tasks/                  # та же структура + enums.py (TaskStatusEnum)
└── migrations/             # Alembic (async env.py), versions/001_initial_*.py
tests/
├── factories.py            # factory-boy фабрики моделей
├── fixtures/               # общие фикстуры (клиент, пользователи, задачи)
├── test_users/test_api/
├── test_tasks/test_api/ и test_repositories/
├── test_core/              # настройки (сборка URL БД)
├── test_healthcheck/
└── test_main.py            # редирект с корня
conftest.py                 # тестовая БД, сессия с откатом, подмена зависимостей
```

Как устроен запрос:

1. **Эндпоинт** принимает провалидированную Pydantic-схему, создаёт use case и вызывает `execute()`. Доменное исключение он превращает в `HTTPException` с нужным кодом.
2. **Use case** содержит бизнес-логику (проверку существования пользователя, подсчёт статистики) и **единолично управляет транзакцией**: коммит делается только здесь.
3. **Репозиторий** выполняет запросы и возвращает DTO, а не ORM-объекты. Поэтому ленивые загрузки за пределами слоя данных невозможны.

### Ключевые решения

- **Уникальность email без гонок.** Email нормализуется к нижнему регистру, вставка идёт через `INSERT ... ON CONFLICT (email) DO NOTHING RETURNING`. Если строка не вернулась, email занят, и сервис отвечает 409. Предварительного SELECT нет, поэтому параллельные запросы дубля не создадут, а сессию не нужно откатывать после `IntegrityError`.
- **Изменения одним запросом.** Смена статуса — это `UPDATE ... RETURNING`, удаление — `DELETE ... RETURNING id`. Отдельный SELECT перед изменением не нужен; если запрос не вернул строк, задачи нет, и сервис отвечает 404. `updated_at` проставляется через `onupdate=func.now()` в том же UPDATE.
- **Статус задачи.** Колонка описана как `sa.Enum(TaskStatusEnum, native_enum=False)`: в БД это `VARCHAR` с `CHECK (status IN (...))`, а не PG ENUM, поэтому новый статус добавляется простой миграцией ограничения, без `ALTER TYPE`. Из БД значение читается как `TaskStatusEnum`, а неизвестный статус в запросе отсекается валидацией с кодом 422.
- **Индекс `(user_id, status)`.** Покрывает фильтрацию списка и `GROUP BY status` в статистике.
- **Именование ограничений.** У `MetaData` задан `naming_convention`, поэтому все ограничения имеют предсказуемые имена (`uq_users_email`, `fk_tasks_user_id_users`, `ck_tasks_status`). Миграции не зависят от автоматически сгенерированных имён.
- **Время.** Даты хранятся как `timestamptz`, проставляются на стороне БД и отдаются в UTC.
- **Подключение к БД.** URL собирается через `sqlalchemy.URL.create`, поэтому спецсимволы в логине и пароле (`@`, `/`, `:`, `%`) не ломают подключение.
- **NUL-символ в строках.** PostgreSQL не хранит `\u0000` в текстовых полях, поэтому `name`, `title` и `description` с ним отклоняются валидацией (422, ограничение `pattern` видно в OpenAPI), а не падают в БД с ошибкой 500.
- **Границы id.** Id хранятся как `BIGINT`, path-параметры ограничены диапазоном `1..2^63-1`. Слишком большой id возвращает 422; без ограничения asyncpg упал бы на переполнении, и запрос завершился бы ошибкой 500.
- **Миграции.** Выполняются отдельным compose-сервисом до старта API, а не при старте приложения. Несколько реплик API не будут конкурировать за миграции, а их ошибка не даст подняться API.

## Допущения

- Для несуществующего пользователя `GET /users/{id}/tasks` и `GET /users/{id}/tasks/stats` возвращают 404, а не пустой результат. Так клиент отличает «нет задач» от «нет пользователя».
- Дублирующийся email возвращает `409 Conflict`. Сравнение email не зависит от регистра: адрес целиком хранится в нижнем регистре.
- Список задач возвращается конвертом `{"items": [...], "total", "limit", "offset"}`, а не голым массивом: так клиент знает общее количество задач для пагинации.
- `name` и `title` обрезаются по краям; строка из одних пробелов считается пустой (422). Пустой `description` (в т.ч. из одних пробелов) сохраняется как `null`. Ограничения длины: `name` и `title` — 255 символов, `description` — 5000, `email` — 254.
- Лишние поля в теле запроса игнорируются.
- Поле `status` в теле `POST /users/{id}/tasks` игнорируется: новая задача всегда создаётся в статусе `new`, статус меняется только через `PATCH /tasks/{id}/status`.
- Переход между любыми статусами разрешён: в ТЗ нет правил переходов.
- `DELETE /tasks/{id}` возвращает `200 {"ok": true}`, как в ТЗ, а не `204`.
- Аутентификация не реализована: её нет в ТЗ.

## Makefile

| Команда                    | Что делает                                    |
|----------------------------|-----------------------------------------------|
| `make prepare`             | копирует `.env.example` в `.env`              |
| `make sync`                | `uv sync`                                     |
| `make up` / `make down`    | поднять postgres / остановить compose         |
| `make migrate`             | `alembic upgrade head`                        |
| `make revision msg=002_x`  | создать миграцию (autogenerate)               |
| `make down-migrate cnt=1`  | откатить N миграций                           |
| `make runserver`           | запустить API локально с автоперезагрузкой    |
| `make test`                | тесты с покрытием                             |
| `make test-docker`         | тесты в Docker                                |
| `make lint`                | ruff check, ruff format --check, mypy         |
| `make format`              | автоисправление и форматирование ruff         |

## CI

`.github/workflows/ci.yml` запускается на push и pull request:

- **lint:** ruff check, ruff format --check, mypy;
- **tests:** PostgreSQL в виде service-контейнера, затем по шагам:
  - `alembic upgrade head`;
  - `alembic check` — проверка, что миграции соответствуют моделям;
  - откат и повторное применение миграций;
  - pytest с покрытием;
- **docker:** `docker compose up --build --wait` без `.env`, как в разделе «Запуск», и smoke-запросы к API (healthcheck, создание пользователя, статистика).

Версия Python для uv зафиксирована в `.python-version` (3.13), как и в Docker-образе.
