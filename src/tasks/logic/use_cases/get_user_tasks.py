import typing as t

from src.core.use_cases.base import BaseSessionAsyncUseCase
from src.tasks.dtos import TaskListDTO
from src.tasks.enums import TaskStatusEnum
from src.tasks.repositories import TaskRepository
from src.users.exceptions import UserNotFoundError
from src.users.repositories import UserRepository


class GetUserTasksUseCase(BaseSessionAsyncUseCase):
    """Получение страницы задач пользователя с фильтром по статусу"""

    def __init__(
        self,
        user_id: int,
        status: TaskStatusEnum | None,
        limit: int,
        offset: int,
        user_repo: type[UserRepository] = UserRepository,
        task_repo: type[TaskRepository] = TaskRepository,
        *args: t.Any,
        **kwargs: t.Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.user_id = user_id
        self.status = status
        self.limit = limit
        self.offset = offset
        self.user_repo = user_repo(self.session)
        self.task_repo = task_repo(self.session)

    async def execute(self) -> TaskListDTO:
        if not await self.user_repo.exists_by_id(self.user_id):
            raise UserNotFoundError

        items = await self.task_repo.get_list_by_user_id(
            self.user_id, status=self.status, limit=self.limit, offset=self.offset
        )
        total = await self.task_repo.count_by_user_id(self.user_id, status=self.status)
        return TaskListDTO(items=items, total=total, limit=self.limit, offset=self.offset)
