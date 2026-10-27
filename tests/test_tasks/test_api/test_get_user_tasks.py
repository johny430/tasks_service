import pytest
from fastapi import status
from httpx import AsyncClient

from src.core.constants import MAX_BIGINT
from src.tasks.constants import DEFAULT_LIMIT, MAX_LIMIT
from src.tasks.models import Task
from src.users.models import User


def get_url(user_id: int) -> str:
    return f'/users/{user_id}/tasks'


@pytest.mark.usefixtures('other_user_task')
async def test_get_user_tasks_returns_only_user_tasks_newest_first(
    api_client: AsyncClient, user: User, user_tasks: list[Task]
) -> None:
    """Возвращаются только задачи пользователя, от новых к старым"""
    response = await api_client.get(get_url(user.id))

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert [item['id'] for item in response_data['items']] == [task.id for task in reversed(user_tasks)]
    assert response_data['total'] == len(user_tasks)
    assert response_data['limit'] == DEFAULT_LIMIT
    assert response_data['offset'] == 0


async def test_get_user_tasks_returns_task_fields(api_client: AsyncClient, user: User, task: Task) -> None:
    """Задача в списке содержит все поля"""
    response = await api_client.get(get_url(user.id))

    assert response.status_code == status.HTTP_200_OK
    item = response.json()['items'][0]
    assert set(item) == {'id', 'user_id', 'title', 'description', 'status', 'created_at', 'updated_at'}
    assert item['id'] == task.id
    assert item['title'] == 'Подготовить отчет'


async def test_get_user_tasks_returns_empty_list_when_user_has_no_tasks(api_client: AsyncClient, user: User) -> None:
    """У пользователя нет задач — пустой список"""
    response = await api_client.get(get_url(user.id))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'items': [], 'total': 0, 'limit': DEFAULT_LIMIT, 'offset': 0}


@pytest.mark.parametrize(
    ('task_status', 'expected_count'),
    [
        ('new', 3),
        ('in_progress', 2),
        ('done', 4),
        ('cancelled', 1),
    ],
)
@pytest.mark.usefixtures('user_tasks', 'other_user_task')
async def test_get_user_tasks_filters_by_status(
    api_client: AsyncClient, user: User, task_status: str, expected_count: int
) -> None:
    """Фильтр по статусу возвращает только задачи с этим статусом, total считается с учётом фильтра"""
    response = await api_client.get(get_url(user.id), params={'status': task_status})

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert {item['status'] for item in response_data['items']} == {task_status}
    assert len(response_data['items']) == expected_count
    assert response_data['total'] == expected_count


@pytest.mark.parametrize(
    ('limit', 'offset', 'expected_slice'),
    [
        (3, 0, slice(0, 3)),
        (3, 3, slice(3, 6)),
        (3, 9, slice(9, 10)),
        (10, 0, slice(0, 10)),
        (5, 10, slice(10, 10)),
        (MAX_LIMIT, 0, slice(0, 10)),
    ],
)
async def test_get_user_tasks_paginates_with_limit_and_offset(
    api_client: AsyncClient, user: User, user_tasks: list[Task], limit: int, offset: int, expected_slice: slice
) -> None:
    """Пагинация limit/offset отдаёт нужный срез, total не зависит от страницы"""
    expected_ids = [task.id for task in reversed(user_tasks)][expected_slice]

    response = await api_client.get(get_url(user.id), params={'limit': limit, 'offset': offset})

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert [item['id'] for item in response_data['items']] == expected_ids
    assert response_data['total'] == len(user_tasks)
    assert response_data['limit'] == limit
    assert response_data['offset'] == offset


async def test_get_user_tasks_returns_404_when_user_not_found(api_client: AsyncClient) -> None:
    """Пользователя нет — 404"""
    response = await api_client.get(get_url(MAX_BIGINT))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Пользователь не найден'}


@pytest.mark.parametrize(
    'params',
    [
        {'status': 'unknown'},
        {'status': 'DONE'},
        {'limit': 0},
        {'limit': MAX_LIMIT + 1},
        {'offset': -1},
        {'limit': 'ten'},
    ],
)
async def test_get_user_tasks_returns_422_when_query_invalid(api_client: AsyncClient, user: User, params: dict) -> None:
    """Неизвестный статус или limit/offset вне диапазона — 422"""
    response = await api_client.get(get_url(user.id), params=params)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.parametrize('user_id', [0, -1, MAX_BIGINT + 1, 'abc'])
async def test_get_user_tasks_returns_422_when_user_id_invalid(api_client: AsyncClient, user_id: int | str) -> None:
    """Id пользователя вне диапазона BIGINT или не число — 422"""
    response = await api_client.get(f'/users/{user_id}/tasks')

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
