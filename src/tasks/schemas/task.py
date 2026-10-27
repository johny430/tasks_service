import typing as t
from datetime import datetime

from pydantic import AfterValidator, BaseModel, Field, StringConstraints

from src.core.constants import NO_NUL_PATTERN
from src.core.schemas.base import BaseFromAttrsModel
from src.tasks.constants import DESCRIPTION_MAX_LENGTH, TITLE_MAX_LENGTH
from src.tasks.enums import TaskStatusEnum


def _blank_to_none(value: str) -> str | None:
    """Пустое описание (в т.ч. из одних пробелов) хранится как None, а не как пустая строка."""
    return value or None


TaskTitle = t.Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=TITLE_MAX_LENGTH, pattern=NO_NUL_PATTERN)
]
TaskDescription = t.Annotated[
    str,
    StringConstraints(strip_whitespace=True, max_length=DESCRIPTION_MAX_LENGTH, pattern=NO_NUL_PATTERN),
    AfterValidator(_blank_to_none),
]


class TaskCreateSchema(BaseModel):
    """Данные для создания задачи"""

    title: TaskTitle = Field(description='Заголовок задачи', examples=['Подготовить отчет'])
    description: TaskDescription | None = Field(
        None, description='Описание задачи', examples=['Собрать данные за неделю']
    )


class TaskStatusUpdateSchema(BaseModel):
    """Новый статус задачи"""

    status: TaskStatusEnum = Field(description='Статус задачи')


class TaskSchema(BaseFromAttrsModel):
    """Задача"""

    id: int = Field(description='ID задачи')
    user_id: int = Field(description='ID пользователя-владельца')
    title: str = Field(description='Заголовок задачи')
    description: str | None = Field(description='Описание задачи')
    status: TaskStatusEnum = Field(description='Статус задачи')
    created_at: datetime = Field(description='Дата создания')
    updated_at: datetime = Field(description='Дата обновления')


class TaskListSchema(BaseFromAttrsModel):
    """Страница задач пользователя"""

    items: list[TaskSchema] = Field(description='Задачи текущей страницы, новые первыми')
    total: int = Field(description='Общее количество задач с учётом фильтра')
    limit: int = Field(description='Размер страницы')
    offset: int = Field(description='Смещение от начала списка')


class TaskStatsSchema(BaseFromAttrsModel):
    """Количество задач пользователя по статусам"""

    total: int = Field(description='Всего задач')
    new: int = Field(description='Задач в статусе new')
    in_progress: int = Field(description='Задач в статусе in_progress')
    done: int = Field(description='Задач в статусе done')
    cancelled: int = Field(description='Задач в статусе cancelled')


class OkResponseSchema(BaseModel):
    """Результат успешной операции без данных"""

    ok: bool = Field(True, description='Операция выполнена')
