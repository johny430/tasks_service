import typing as t

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

import src.core.database.di as app_db_di
from src.core.database.base import Base
from src.core.database.di import get_db_session
from src.core.settings import settings
from src.main import app

pytest_plugins = [
    'tests.fixtures.api_clients',
    'tests.fixtures.users',
    'tests.fixtures.tasks',
]

TEST_DATABASE_NAME = f'{settings.DB_NAME}_test'


async def _recreate_database(*, create: bool) -> None:
    # подключаемся к служебной базе postgres, т.к. к удаляемой базе подключаться нельзя
    admin_engine = create_async_engine(settings.postgres_url.set(database='postgres'), isolation_level='AUTOCOMMIT')
    async with admin_engine.connect() as conn:
        await conn.execute(text(f'DROP DATABASE IF EXISTS {TEST_DATABASE_NAME} WITH (FORCE)'))
        if create:
            await conn.execute(text(f'CREATE DATABASE {TEST_DATABASE_NAME}'))
    await admin_engine.dispose()


@pytest.fixture(scope='session')
async def engine() -> t.AsyncIterator[AsyncEngine]:
    await _recreate_database(create=True)

    test_engine = create_async_engine(settings.postgres_url.set(database=TEST_DATABASE_NAME))
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield test_engine

    await test_engine.dispose()
    await app_db_di.engine.dispose()
    await _recreate_database(create=False)


@pytest.fixture
async def session(engine: AsyncEngine) -> t.AsyncIterator[AsyncSession]:
    async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)

    # Такой подход позволяет откатывать даже session.commit()
    async with engine.connect() as conn:
        trans = await conn.begin()
        # join_transaction_mode нужен для работы с транзакциями
        async with async_session(bind=conn, join_transaction_mode='create_savepoint') as session:
            yield session
        await trans.rollback()


@pytest.fixture(autouse=True)
def app_with_session(session: AsyncSession) -> t.Iterator[t.Any]:
    async def get_test_session() -> t.AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_db_session] = get_test_session
    yield app
    app.dependency_overrides.clear()
