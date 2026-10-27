import pytest
from fastapi import status
from httpx import AsyncClient

from src.core.constants import MAX_BIGINT
from src.users.models import User


def get_url(user_id: int) -> str:
    return f'/users/{user_id}/tasks/stats'


@pytest.mark.usefixtures('user_tasks', 'other_user_task')
async def test_get_user_tasks_stats_returns_counts_by_status(api_client: AsyncClient, user: User) -> None:
    """Статистика считается по задачам пользователя, чужие задачи не учитываются"""
    response = await api_client.get(get_url(user.id))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'total': 10, 'new': 3, 'in_progress': 2, 'done': 4, 'cancelled': 1}


async def test_get_user_tasks_stats_returns_zeros_when_user_has_no_tasks(api_client: AsyncClient, user: User) -> None:
    """У пользователя нет задач — все счётчики нулевые"""
    response = await api_client.get(get_url(user.id))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'total': 0, 'new': 0, 'in_progress': 0, 'done': 0, 'cancelled': 0}


async def test_get_user_tasks_stats_returns_404_when_user_not_found(api_client: AsyncClient) -> None:
    """Пользователя нет — 404"""
    response = await api_client.get(get_url(MAX_BIGINT))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Пользователь не найден'}


@pytest.mark.parametrize('user_id', [0, -1, MAX_BIGINT + 1, 'abc'])
async def test_get_user_tasks_stats_returns_422_when_user_id_invalid(
    api_client: AsyncClient, user_id: int | str
) -> None:
    """Id пользователя вне диапазона BIGINT или не число — 422"""
    response = await api_client.get(f'/users/{user_id}/tasks/stats')

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
