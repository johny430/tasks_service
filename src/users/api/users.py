import typing as t

from fastapi import APIRouter, HTTPException, Path, status

from src.core.constants import MAX_BIGINT
from src.core.database.di import SessionDep
from src.core.schemas import ErrorResponseSchema
from src.users.dtos import UserDTO
from src.users.exceptions import UserEmailAlreadyExistsError, UserNotFoundError
from src.users.logic.use_cases import CreateUserUseCase, GetUserUseCase
from src.users.schemas import UserCreateSchema, UserSchema

users_router = APIRouter(prefix='/users', tags=['Users'])


@users_router.post(
    '',
    summary='Создаёт пользователя',
    status_code=status.HTTP_201_CREATED,
    response_model=UserSchema,
    responses={
        status.HTTP_409_CONFLICT: {'model': ErrorResponseSchema, 'description': 'Email уже занят'},
    },
)
async def create_user(session: SessionDep, user_data: UserCreateSchema) -> UserDTO:
    use_case = CreateUserUseCase(session=session, email=user_data.email, name=user_data.name)
    try:
        return await use_case.execute()
    except UserEmailAlreadyExistsError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail='Пользователь с таким email уже существует'
        ) from err


@users_router.get(
    '/{user_id}',
    summary='Возвращает пользователя',
    response_model=UserSchema,
    responses={
        status.HTTP_404_NOT_FOUND: {'model': ErrorResponseSchema, 'description': 'Пользователь не найден'},
    },
)
async def get_user(
    session: SessionDep,
    user_id: t.Annotated[int, Path(description='ID пользователя', ge=1, le=MAX_BIGINT)],
) -> UserDTO:
    use_case = GetUserUseCase(session=session, user_id=user_id)
    try:
        return await use_case.execute()
    except UserNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Пользователь не найден') from err
