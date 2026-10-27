import typing as t

from structlog import get_logger

from src.core.use_cases.base import BaseSessionAsyncUseCase
from src.tasks.dtos import TaskDTO
from src.tasks.enums import TaskStatusEnum
from src.tasks.exceptions import TaskNotFoundError
from src.tasks.repositories import TaskRepository

logger = get_logger(__name__)


class UpdateTaskStatusUseCase(BaseSessionAsyncUseCase):
    """Изменение статуса задачи"""

    def __init__(
        self,
        task_id: int,
        status: TaskStatusEnum,
        task_repo: type[TaskRepository] = TaskRepository,
        *args: t.Any,
        **kwargs: t.Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.task_id = task_id
        self.status = status
        self.task_repo = task_repo(self.session)

    async def execute(self) -> TaskDTO:
        task_dto = await self.task_repo.update_status_or_none(self.task_id, self.status)
        if not task_dto:
            raise TaskNotFoundError

        await self.session.commit()
        logger.info('Статус задачи изменён', task_id=self.task_id, status=self.status)
        return task_dto
