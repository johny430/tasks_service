from datetime import datetime

import pytest
from fastapi import status
from httpx import AsyncClient

from src.core.constants import MAX_BIGINT
from src.users.models import User


def get_url(user_id: int | str) -> str:
    return f'/users/{user_id}'


async def test_get_user_returns_user(api_client: AsyncClient, user: User) -> None:
    """Возвращается пользователь по id"""
    response = await api_client.get(get_url(user.id))

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert datetime.fromisoformat(response_data.pop('created_at')) == user.created_at
    assert response_data == {'id': user.id, 'email': 'ivan@example.com', 'name': 'Ivan'}


async def test_get_user_returns_404_when_user_not_found(api_client: AsyncClient) -> None:
    """Пользователя нет — 404"""
    response = await api_client.get(get_url(MAX_BIGINT))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Пользователь не найден'}


@pytest.mark.parametrize('user_id', [0, -1, MAX_BIGINT + 1, 'abc'])
async def test_get_user_returns_422_when_id_invalid(api_client: AsyncClient, user_id: int | str) -> None:
    """Id вне диапазона BIGINT или не число — 422, а не 500"""
    response = await api_client.get(get_url(user_id))

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
