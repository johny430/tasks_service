from datetime import UTC, datetime

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.constants import MAX_BIGINT
from src.tasks.enums import TaskStatusEnum
from src.tasks.models import Task
from src.users.models import User
from tests.factories import TaskFactory

OLD_UPDATED_AT = datetime(2020, 1, 1, tzinfo=UTC)


def get_url(task_id: int) -> str:
    return f'/tasks/{task_id}/status'


@pytest.fixture
async def old_task(session: AsyncSession, user: User) -> Task:
    """Задача, которая давно не обновлялась"""
    return await TaskFactory.create(session=session, user_id=user.id, updated_at=OLD_UPDATED_AT)


@pytest.mark.parametrize('new_status', list(TaskStatusEnum))
async def test_update_task_status_changes_status(
    api_client: AsyncClient, session: AsyncSession, task: Task, new_status: TaskStatusEnum
) -> None:
    """Статус меняется на любой допустимый и сохраняется в БД"""
    response = await api_client.patch(get_url(task.id), json={'status': new_status})

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['id'] == task.id
    assert response.json()['status'] == new_status
    assert await session.scalar(select(Task.status).where(Task.id == task.id)) == new_status


async def test_update_task_status_refreshes_updated_at(api_client: AsyncClient, old_task: Task) -> None:
    """При смене статуса обновляется updated_at"""
    response = await api_client.patch(get_url(old_task.id), json={'status': 'in_progress'})

    assert response.status_code == status.HTTP_200_OK
    assert datetime.fromisoformat(response.json()['updated_at']) > OLD_UPDATED_AT


async def test_update_task_status_returns_404_when_task_not_found(api_client: AsyncClient) -> None:
    """Задачи нет — 404"""
    response = await api_client.patch(get_url(MAX_BIGINT), json={'status': 'done'})

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Задача не найдена'}


@pytest.mark.parametrize(
    'payload',
    [
        {'status': 'unknown'},
        {'status': 'DONE'},
        {'status': ''},
        {'status': None},
        {},
    ],
)
async def test_update_task_status_returns_422_when_status_invalid(
    api_client: AsyncClient, session: AsyncSession, task: Task, payload: dict
) -> None:
    """Некорректный статус — 422, задача не меняется"""
    response = await api_client.patch(get_url(task.id), json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert await session.scalar(select(Task.status).where(Task.id == task.id)) == TaskStatusEnum.NEW


@pytest.mark.parametrize('task_id', [0, -1, MAX_BIGINT + 1, 'abc'])
async def test_update_task_status_returns_422_when_task_id_invalid(api_client: AsyncClient, task_id: int | str) -> None:
    """Id задачи вне диапазона BIGINT или не число — 422"""
    response = await api_client.patch(f'/tasks/{task_id}/status', json={'status': 'done'})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
