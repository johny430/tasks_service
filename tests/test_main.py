from fastapi import status
from httpx import AsyncClient


async def test_root_redirects_to_docs(api_client: AsyncClient) -> None:
    """Корень сервиса перенаправляет на Swagger"""
    response = await api_client.get('/')

    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers['location'] == '/docs'
