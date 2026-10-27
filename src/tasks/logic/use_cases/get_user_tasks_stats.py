import typing as t

from src.core.use_cases.base import BaseSessionAsyncUseCase
from src.tasks.dtos import TaskStatsDTO
from src.tasks.enums import TaskStatusEnum
from src.tasks.repositories import TaskRepository
from src.users.exceptions import UserNotFoundError
from src.users.repositories import UserRepository


class GetUserTasksStatsUseCase(BaseSessionAsyncUseCase):
    """Подсчёт задач пользователя по статусам"""

    def __init__(
        self,
        user_id: int,
        user_repo: type[UserRepository] = UserRepository,
        task_repo: type[TaskRepository] = TaskRepository,
        *args: t.Any,
        **kwargs: t.Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.user_id = user_id
        self.user_repo = user_repo(self.session)
        self.task_repo = task_repo(self.session)

    async def execute(self) -> TaskStatsDTO:
        if not await self.user_repo.exists_by_id(self.user_id):
            raise UserNotFoundError

        count_by_status = await self.task_repo.get_count_by_status(self.user_id)
        # статусы, по которым задач нет, тоже попадают в ответ — с нулём
        counts = {status.value: count_by_status.get(status, 0) for status in TaskStatusEnum}
        return TaskStatsDTO(total=sum(counts.values()), **counts)
