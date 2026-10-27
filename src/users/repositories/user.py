from sqlalchemy import exists, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.dtos import UserDTO
from src.users.models import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_or_none(self, email: str, name: str) -> UserDTO | None:
        """
        Создаёт пользователя.

        Возвращает None, если пользователь с таким email уже есть. Проверка выполняется
        уникальным индексом в одном запросе, поэтому параллельные запросы не создадут дубль.
        """
        stmt = (
            insert(User)
            .values(email=email, name=name)
            .on_conflict_do_nothing(index_elements=[User.email])
            .returning(User)
        )
        user: User | None = await self.session.scalar(stmt)
        if user:
            return UserDTO.model_validate(user)
        return None

    async def get_or_none_by_id(self, user_id: int) -> UserDTO | None:
        user: User | None = await self.session.get(User, user_id)
        if user:
            return UserDTO.model_validate(user)
        return None

    async def exists_by_id(self, user_id: int) -> bool:
        stmt = select(exists().where(User.id == user_id))
        result = await self.session.execute(stmt)
        return bool(result.scalar_one())
