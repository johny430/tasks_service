import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models import User
from tests.factories import UserFactory


@pytest.fixture
async def user(session: AsyncSession) -> User:
    return await UserFactory.create(session=session, email='ivan@example.com', name='Ivan')


@pytest.fixture
async def other_user(session: AsyncSession) -> User:
    return await UserFactory.create(session=session, email='petr@example.com', name='Petr')
