import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.constants import MAX_BIGINT
from src.tasks.enums import TaskStatusEnum
from src.tasks.models import Task
from src.tasks.repositories import TaskRepository
from src.users.models import User
from tests.factories import TaskFactory


@pytest.fixture
def task_repo(session: AsyncSession) -> TaskRepository:
    return TaskRepository(session)


async def test_get_count_by_status_skips_statuses_without_tasks(
    session: AsyncSession, task_repo: TaskRepository, user: User
) -> None:
    """В результат попадают только статусы, по которым есть задачи"""
    await TaskFactory.create(session=session, user_id=user.id, status=TaskStatusEnum.DONE)
    await TaskFactory.create(session=session, user_id=user.id, status=TaskStatusEnum.DONE)
    await TaskFactory.create(session=session, user_id=user.id, status=TaskStatusEnum.NEW)

    result = await task_repo.get_count_by_status(user.id)

    assert result == {TaskStatusEnum.DONE: 2, TaskStatusEnum.NEW: 1}
    assert all(type(status) is TaskStatusEnum for status in result)


@pytest.mark.usefixtures('other_user_task')
async def test_get_list_by_user_id_combines_status_filter_and_pagination(
    task_repo: TaskRepository, user: User, user_tasks: list[Task]
) -> None:
    """Фильтр по статусу и пагинация применяются вместе, сортировка от новых к старым"""
    # задачи done в фикстуре — user_tasks[5:9], от новых к старым: 8, 7, 6, 5

    result = await task_repo.get_list_by_user_id(user.id, status=TaskStatusEnum.DONE, limit=2, offset=1)

    assert [task.id for task in result] == [user_tasks[7].id, user_tasks[6].id]


@pytest.mark.usefixtures('user_tasks')
async def test_count_by_user_id_counts_with_status_filter(task_repo: TaskRepository, user: User) -> None:
    """Количество задач учитывает фильтр по статусу"""
    result = await task_repo.count_by_user_id(user.id, status=TaskStatusEnum.IN_PROGRESS)

    assert result == 2


async def test_update_status_or_none_returns_none_when_task_not_found(task_repo: TaskRepository) -> None:
    """Задачи нет — None"""
    result = await task_repo.update_status_or_none(MAX_BIGINT, TaskStatusEnum.DONE)

    assert result is None


async def test_delete_returns_false_when_task_not_found(task_repo: TaskRepository) -> None:
    """Задачи нет — False"""
    result = await task_repo.delete(MAX_BIGINT)

    assert result is False
