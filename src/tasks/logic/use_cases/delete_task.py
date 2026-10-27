import typing as t

from structlog import get_logger

from src.core.use_cases.base import BaseSessionAsyncUseCase
from src.tasks.exceptions import TaskNotFoundError
from src.tasks.repositories import TaskRepository

logger = get_logger(__name__)


class DeleteTaskUseCase(BaseSessionAsyncUseCase):
    """Удаление задачи"""

    def __init__(
        self,
        task_id: int,
        task_repo: type[TaskRepository] = TaskRepository,
        *args: t.Any,
        **kwargs: t.Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.task_id = task_id
        self.task_repo = task_repo(self.session)

    async def execute(self) -> None:
        if not await self.task_repo.delete(self.task_id):
            raise TaskNotFoundError

        await self.session.commit()
        logger.info('Задача удалена', task_id=self.task_id)
