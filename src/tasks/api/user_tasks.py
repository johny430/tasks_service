import typing as t

from fastapi import APIRouter, HTTPException, Path, Query, status

from src.core.constants import MAX_BIGINT
from src.core.database.di import SessionDep
from src.core.schemas import ErrorResponseSchema
from src.tasks.constants import DEFAULT_LIMIT, MAX_LIMIT
from src.tasks.dtos import TaskDTO, TaskListDTO, TaskStatsDTO
from src.tasks.enums import TaskStatusEnum
from src.tasks.logic.use_cases import CreateTaskUseCase, GetUserTasksStatsUseCase, GetUserTasksUseCase
from src.tasks.schemas import TaskCreateSchema, TaskListSchema, TaskSchema, TaskStatsSchema
from src.users.exceptions import UserNotFoundError

user_tasks_router = APIRouter(prefix='/users/{user_id}/tasks', tags=['Tasks'])

UserIdPath = t.Annotated[int, Path(description='ID пользователя', ge=1, le=MAX_BIGINT)]

USER_NOT_FOUND_RESPONSES: dict[int | str, dict[str, t.Any]] = {
    status.HTTP_404_NOT_FOUND: {'model': ErrorResponseSchema, 'description': 'Пользователь не найден'},
}


def _user_not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Пользователь не найден')


@user_tasks_router.post(
    '',
    summary='Создаёт задачу пользователя',
    status_code=status.HTTP_201_CREATED,
    response_model=TaskSchema,
    responses=USER_NOT_FOUND_RESPONSES,
)
async def create_user_task(session: SessionDep, user_id: UserIdPath, task_data: TaskCreateSchema) -> TaskDTO:
    use_case = CreateTaskUseCase(
        session=session,
        user_id=user_id,
        title=task_data.title,
        description=task_data.description,
    )
    try:
        return await use_case.execute()
    except UserNotFoundError as err:
        raise _user_not_found() from err


@user_tasks_router.get(
    '',
    summary='Возвращает задачи пользователя',
    description='Задачи отсортированы от новых к старым. Поддерживает фильтр по статусу и пагинацию limit/offset.',
    response_model=TaskListSchema,
    responses=USER_NOT_FOUND_RESPONSES,
)
async def get_user_tasks(
    session: SessionDep,
    user_id: UserIdPath,
    task_status: t.Annotated[TaskStatusEnum | None, Query(alias='status', description='Фильтр по статусу')] = None,
    limit: t.Annotated[int, Query(description='Размер страницы', ge=1, le=MAX_LIMIT)] = DEFAULT_LIMIT,
    offset: t.Annotated[int, Query(description='Смещение от начала списка', ge=0, le=MAX_BIGINT)] = 0,
) -> TaskListDTO:
    use_case = GetUserTasksUseCase(session=session, user_id=user_id, status=task_status, limit=limit, offset=offset)
    try:
        return await use_case.execute()
    except UserNotFoundError as err:
        raise _user_not_found() from err


@user_tasks_router.get(
    '/stats',
    summary='Возвращает статистику задач пользователя по статусам',
    response_model=TaskStatsSchema,
    responses=USER_NOT_FOUND_RESPONSES,
)
async def get_user_tasks_stats(session: SessionDep, user_id: UserIdPath) -> TaskStatsDTO:
    use_case = GetUserTasksStatsUseCase(session=session, user_id=user_id)
    try:
        return await use_case.execute()
    except UserNotFoundError as err:
        raise _user_not_found() from err
