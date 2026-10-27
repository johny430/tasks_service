import typing as t

from src.core.use_cases.base import BaseSessionAsyncUseCase
from src.users.dtos import UserDTO
from src.users.exceptions import UserNotFoundError
from src.users.repositories import UserRepository


class GetUserUseCase(BaseSessionAsyncUseCase):
    """Получение пользователя по ID"""

    def __init__(
        self,
        user_id: int,
        user_repo: type[UserRepository] = UserRepository,
        *args: t.Any,
        **kwargs: t.Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.user_id = user_id
        self.user_repo = user_repo(self.session)

    async def execute(self) -> UserDTO:
        user_dto = await self.user_repo.get_or_none_by_id(self.user_id)
        if not user_dto:
            raise UserNotFoundError
        return user_dto
