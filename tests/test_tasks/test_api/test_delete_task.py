import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.constants import MAX_BIGINT
from src.tasks.models import Task


def get_url(task_id: int) -> str:
    return f'/tasks/{task_id}'


async def test_delete_task_returns_ok_and_removes_task(
    api_client: AsyncClient, session: AsyncSession, task: Task, other_user_task: Task
) -> None:
    """Задача удаляется, другие задачи остаются"""
    response = await api_client.delete(get_url(task.id))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'ok': True}
    assert (await session.scalars(select(Task.id))).all() == [other_user_task.id]


async def test_delete_task_returns_404_when_already_deleted(api_client: AsyncClient, task: Task) -> None:
    """Повторное удаление — 404"""
    await api_client.delete(get_url(task.id))

    response = await api_client.delete(get_url(task.id))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Задача не найдена'}


async def test_delete_task_returns_404_when_task_not_found(api_client: AsyncClient) -> None:
    """Задачи нет — 404"""
    response = await api_client.delete(get_url(MAX_BIGINT))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Задача не найдена'}


@pytest.mark.parametrize('task_id', [0, -1, MAX_BIGINT + 1, 'abc'])
async def test_delete_task_returns_422_when_task_id_invalid(api_client: AsyncClient, task_id: int | str) -> None:
    """Id задачи вне диапазона BIGINT или не число — 422"""
    response = await api_client.delete(f'/tasks/{task_id}')

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
