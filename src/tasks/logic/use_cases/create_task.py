import typing as t

from structlog import get_logger

from src.core.use_cases.base import BaseSessionAsyncUseCase
from src.tasks.dtos import TaskDTO
from src.tasks.repositories import TaskRepository
from src.users.exceptions import UserNotFoundError
from src.users.repositories import UserRepository

logger = get_logger(__name__)


class CreateTaskUseCase(BaseSessionAsyncUseCase):
    """Создание задачи для пользователя"""

    def __init__(
        self,
        user_id: int,
        title: str,
        description: str | None,
        user_repo: type[UserRepository] = UserRepository,
        task_repo: type[TaskRepository] = TaskRepository,
        *args: t.Any,
        **kwargs: t.Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.user_id = user_id
        self.title = title
        self.description = description
        self.user_repo = user_repo(self.session)
        self.task_repo = task_repo(self.session)

    async def execute(self) -> TaskDTO:
        if not await self.user_repo.exists_by_id(self.user_id):
            raise UserNotFoundError

        task_dto = await self.task_repo.create(user_id=self.user_id, title=self.title, description=self.description)
        await self.session.commit()
        logger.info('Задача создана', task_id=task_dto.id, user_id=self.user_id)
        return task_dto
