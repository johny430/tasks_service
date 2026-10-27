import typing as t

from structlog import get_logger

from src.core.use_cases.base import BaseSessionAsyncUseCase
from src.users.dtos import UserDTO
from src.users.exceptions import UserEmailAlreadyExistsError
from src.users.repositories import UserRepository

logger = get_logger(__name__)


class CreateUserUseCase(BaseSessionAsyncUseCase):
    """Создание пользователя с уникальным email"""

    def __init__(
        self,
        email: str,
        name: str,
        user_repo: type[UserRepository] = UserRepository,
        *args: t.Any,
        **kwargs: t.Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.email = email
        self.name = name
        self.user_repo = user_repo(self.session)

    async def execute(self) -> UserDTO:
        user_dto = await self.user_repo.create_or_none(email=self.email, name=self.name)
        if not user_dto:
            raise UserEmailAlreadyExistsError

        await self.session.commit()
        logger.info('Пользователь создан', user_id=user_dto.id)
        return user_dto
