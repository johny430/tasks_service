from sqlalchemy import ColumnElement, delete, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.tasks.dtos import TaskDTO
from src.tasks.enums import TaskStatusEnum
from src.tasks.models import Task


class TaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user_id: int, title: str, description: str | None) -> TaskDTO:
        stmt = insert(Task).values(user_id=user_id, title=title, description=description).returning(Task)
        result = await self.session.execute(stmt)
        return TaskDTO.model_validate(result.scalar_one())

    async def get_list_by_user_id(
        self,
        user_id: int,
        *,
        status: TaskStatusEnum | None = None,
        limit: int,
        offset: int,
    ) -> list[TaskDTO]:
        """Задачи пользователя, новые первыми."""
        stmt = (
            select(Task)
            .where(*self._user_tasks_filters(user_id, status))
            .order_by(Task.id.desc())
            .limit(limit)
            .offset(offset)
        )
        tasks = await self.session.scalars(stmt)
        return [TaskDTO.model_validate(task) for task in tasks]

    async def count_by_user_id(self, user_id: int, *, status: TaskStatusEnum | None = None) -> int:
        """Количество задач пользователя с теми же фильтрами, что и get_list_by_user_id."""
        stmt = select(func.count()).select_from(Task).where(*self._user_tasks_filters(user_id, status))
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def get_count_by_status(self, user_id: int) -> dict[TaskStatusEnum, int]:
        """Количество задач пользователя по статусам. Статусы без задач в результат не попадают."""
        stmt = select(Task.status, func.count()).where(Task.user_id == user_id).group_by(Task.status)
        result = await self.session.execute(stmt)
        return dict(result.all())

    async def update_status_or_none(self, task_id: int, status: TaskStatusEnum) -> TaskDTO | None:
        """Меняет статус задачи и возвращает её. Возвращает None, если задачи нет."""
        stmt = update(Task).where(Task.id == task_id).values(status=status).returning(Task)
        task: Task | None = await self.session.scalar(stmt)
        if task:
            return TaskDTO.model_validate(task)
        return None

    async def delete(self, task_id: int) -> bool:
        """Удаляет задачу. Возвращает False, если задачи нет."""
        stmt = delete(Task).where(Task.id == task_id).returning(Task.id)
        deleted_id: int | None = await self.session.scalar(stmt)
        return deleted_id is not None

    @staticmethod
    def _user_tasks_filters(user_id: int, status: TaskStatusEnum | None) -> list[ColumnElement[bool]]:
        filters = [Task.user_id == user_id]
        if status:
            filters.append(Task.status == status)
        return filters
