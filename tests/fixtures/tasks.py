import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.tasks.enums import TaskStatusEnum
from src.tasks.models import Task
from src.users.models import User
from tests.factories import TaskFactory


@pytest.fixture
async def task(session: AsyncSession, user: User) -> Task:
    return await TaskFactory.create(session=session, user_id=user.id, title='Подготовить отчет')


@pytest.fixture
async def user_tasks(session: AsyncSession, user: User) -> list[Task]:
    """Задачи пользователя: 3 new, 2 in_progress, 4 done, 1 cancelled — в порядке создания."""
    statuses = [
        *[TaskStatusEnum.NEW] * 3,
        *[TaskStatusEnum.IN_PROGRESS] * 2,
        *[TaskStatusEnum.DONE] * 4,
        TaskStatusEnum.CANCELLED,
    ]
    return [await TaskFactory.create(session=session, user_id=user.id, status=status) for status in statuses]


@pytest.fixture
async def other_user_task(session: AsyncSession, other_user: User) -> Task:
    return await TaskFactory.create(session=session, user_id=other_user.id, status=TaskStatusEnum.DONE)
