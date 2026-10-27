import typing as t

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def api_client(app_with_session: FastAPI) -> t.AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app_with_session), base_url='http://test') as client:
        yield client
