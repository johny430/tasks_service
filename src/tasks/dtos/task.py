from datetime import datetime

from pydantic import BaseModel

from src.core.schemas.base import BaseFromAttrsModel
from src.tasks.enums import TaskStatusEnum


class TaskDTO(BaseFromAttrsModel):
    """DTO для работы с задачей"""

    id: int
    user_id: int
    title: str
    description: str | None
    status: TaskStatusEnum
    created_at: datetime
    updated_at: datetime


class TaskListDTO(BaseModel):
    """Страница задач пользователя"""

    items: list[TaskDTO]
    total: int
    limit: int
    offset: int


class TaskStatsDTO(BaseModel):
    """Количество задач пользователя по статусам"""

    total: int
    new: int
    in_progress: int
    done: int
    cancelled: int
