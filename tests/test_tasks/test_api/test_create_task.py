from datetime import datetime

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.constants import MAX_BIGINT
from src.tasks.constants import DESCRIPTION_MAX_LENGTH, TITLE_MAX_LENGTH
from src.tasks.models import Task
from src.users.models import User


def get_url(user_id: int) -> str:
    return f'/users/{user_id}/tasks'


async def test_create_task_returns_201_with_new_task(
    api_client: AsyncClient, session: AsyncSession, user: User
) -> None:
    """Задача создаётся у пользователя со статусом new"""
    response = await api_client.post(
        get_url(user.id), json={'title': 'Подготовить отчет', 'description': 'Собрать данные за неделю'}
    )

    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data['user_id'] == user.id
    assert response_data['title'] == 'Подготовить отчет'
    assert response_data['description'] == 'Собрать данные за неделю'
    assert response_data['status'] == 'new'
    assert datetime.fromisoformat(response_data['created_at'])
    assert datetime.fromisoformat(response_data['updated_at'])
    task = await session.scalar(select(Task).where(Task.id == response_data['id']))
    assert task is not None
    assert task.user_id == user.id


async def test_create_task_without_description_returns_null_description(api_client: AsyncClient, user: User) -> None:
    """Описание необязательно"""
    response = await api_client.post(get_url(user.id), json={'title': 'Подготовить отчет'})

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()['description'] is None


@pytest.mark.parametrize('description', ['', '   '])
async def test_create_task_stores_blank_description_as_null(
    api_client: AsyncClient, user: User, description: str
) -> None:
    """Пустое описание сохраняется как null, а не как пустая строка"""
    response = await api_client.post(get_url(user.id), json={'title': 'Подготовить отчет', 'description': description})

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()['description'] is None


async def test_create_task_ignores_status_in_payload(api_client: AsyncClient, user: User) -> None:
    """Статус при создании всегда new, даже если передан в теле"""
    response = await api_client.post(get_url(user.id), json={'title': 'Подготовить отчет', 'status': 'done'})

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()['status'] == 'new'


async def test_create_task_returns_404_when_user_not_found(api_client: AsyncClient, session: AsyncSession) -> None:
    """Пользователя нет — 404, задача не создаётся"""
    response = await api_client.post(get_url(MAX_BIGINT), json={'title': 'Подготовить отчет'})

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Пользователь не найден'}
    assert await session.scalar(select(Task.id)) is None


@pytest.mark.parametrize(
    'payload',
    [
        {},
        {'description': 'Без заголовка'},
        {'title': ''},
        {'title': '   '},
        {'title': 'x' * (TITLE_MAX_LENGTH + 1)},
        {'title': None},
        {'title': 'Подготовить\x00отчет'},
        {'title': 'Подготовить отчет', 'description': 'x' * (DESCRIPTION_MAX_LENGTH + 1)},
        {'title': 'Подготовить отчет', 'description': 'Собрать\x00данные'},
    ],
)
async def test_create_task_returns_422_when_payload_invalid(api_client: AsyncClient, user: User, payload: dict) -> None:
    """Заголовок обязателен и не пустой, длина полей ограничена, NUL-символ запрещён"""
    response = await api_client.post(get_url(user.id), json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.parametrize('user_id', [0, -1, MAX_BIGINT + 1, 'abc'])
async def test_create_task_returns_422_when_user_id_invalid(api_client: AsyncClient, user_id: int | str) -> None:
    """Id пользователя вне диапазона BIGINT или не число — 422"""
    response = await api_client.post(f'/users/{user_id}/tasks', json={'title': 'Подготовить отчет'})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
