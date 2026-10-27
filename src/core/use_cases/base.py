import typing as t

from sqlalchemy.ext.asyncio import AsyncSession


class BaseSessionAsyncUseCase:
    """
    Базовый сценарий, работающий с сессией БД.

    Транзакцией управляет сценарий: репозитории не коммитят, коммит делается в execute.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def execute(self, *args: t.Any, **kwargs: t.Any) -> t.Any:
        raise NotImplementedError
