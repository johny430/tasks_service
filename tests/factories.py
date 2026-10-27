import typing as t

import factory
from factory.alchemy import SQLAlchemyModelFactory
from sqlalchemy.ext.asyncio import AsyncSession

from src.tasks.enums import TaskStatusEnum
from src.tasks.models import Task
from src.users.models import User


class BaseFactory(SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session_persistence = 'flush'

    @classmethod
    async def create(cls, session: AsyncSession, **overrides: t.Any) -> t.Any:  # type: ignore[override]
        obj = cls.build(**overrides)
        session.add(obj)
        await session.flush()
        # подтягиваем значения, сгенерированные БД (created_at, updated_at, status)
        await session.refresh(obj)
        return obj


class UserFactory(BaseFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f'user{n}@example.com')
    name = factory.Faker('first_name')


class TaskFactory(BaseFactory):
    class Meta:
        model = Task

    title = factory.Faker('sentence', nb_words=3)
    description = factory.Faker('sentence')
    status = TaskStatusEnum.NEW
