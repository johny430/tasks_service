from datetime import datetime

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.constants import NAME_MAX_LENGTH
from src.users.models import User

URL = '/users'


async def test_create_user_returns_201_with_user(api_client: AsyncClient, session: AsyncSession) -> None:
    """Пользователь создаётся и возвращается вместе с id и датой создания"""
    response = await api_client.post(URL, json={'email': 'user@example.com', 'name': 'Ivan'})

    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data['email'] == 'user@example.com'
    assert response_data['name'] == 'Ivan'
    assert datetime.fromisoformat(response_data['created_at'])
    user = await session.scalar(select(User).where(User.id == response_data['id']))
    assert user is not None
    assert user.email == 'user@example.com'


async def test_create_user_normalizes_email_and_name(api_client: AsyncClient) -> None:
    """Email приводится к нижнему регистру, пробелы вокруг имени отбрасываются"""
    response = await api_client.post(URL, json={'email': 'User@Example.COM', 'name': '  Ivan  '})

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()['email'] == 'user@example.com'
    assert response.json()['name'] == 'Ivan'


@pytest.mark.parametrize('email', ['ivan@example.com', 'IVAN@example.com'])
@pytest.mark.usefixtures('user')
async def test_create_user_returns_409_when_email_exists(
    api_client: AsyncClient, session: AsyncSession, email: str
) -> None:
    """Email уже занят (в т.ч. в другом регистре) — 409, второй пользователь не создаётся"""
    response = await api_client.post(URL, json={'email': email, 'name': 'Another Ivan'})

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {'detail': 'Пользователь с таким email уже существует'}
    users = (await session.scalars(select(User).where(User.email == 'ivan@example.com'))).all()
    assert len(users) == 1


@pytest.mark.parametrize(
    'payload',
    [
        {'email': 'not-an-email', 'name': 'Ivan'},
        {'email': 'user@', 'name': 'Ivan'},
        {'email': 'user@example.com', 'name': ''},
        {'email': 'user@example.com', 'name': '   '},
        {'email': 'user@example.com', 'name': 'x' * (NAME_MAX_LENGTH + 1)},
        {'email': 'user@example.com', 'name': 'Iv\x00an'},
        {'email': 'us\x00er@example.com', 'name': 'Ivan'},
        {'email': 'user@example.com'},
        {'name': 'Ivan'},
        {},
    ],
)
async def test_create_user_returns_422_when_payload_invalid(api_client: AsyncClient, payload: dict) -> None:
    """Некорректный email, пустое или слишком длинное имя, NUL-символ — 422"""
    response = await api_client.post(URL, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
