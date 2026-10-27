from fastapi import status
from httpx import AsyncClient


async def test_get_healthcheck_returns_ok(api_client: AsyncClient) -> None:
    """Сервис отвечает на healthcheck"""
    response = await api_client.get('/healthcheck')

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'status': 'ok'}
