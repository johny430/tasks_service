import typing as t
from datetime import datetime

from pydantic import AfterValidator, BaseModel, EmailStr, Field, StringConstraints

from src.core.constants import NO_NUL_PATTERN
from src.core.schemas.base import BaseFromAttrsModel
from src.users.constants import EMAIL_MAX_LENGTH, NAME_MAX_LENGTH

# Email приводится к нижнему регистру целиком: уникальность не зависит от регистра.
NormalizedEmail = t.Annotated[EmailStr, Field(max_length=EMAIL_MAX_LENGTH), AfterValidator(str.lower)]
UserName = t.Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=NAME_MAX_LENGTH, pattern=NO_NUL_PATTERN)
]


class UserCreateSchema(BaseModel):
    """Данные для создания пользователя"""

    email: NormalizedEmail = Field(description='Email пользователя, уникальный', examples=['user@example.com'])
    name: UserName = Field(description='Имя пользователя', examples=['Ivan'])


class UserSchema(BaseFromAttrsModel):
    """Пользователь"""

    id: int = Field(description='ID пользователя')
    email: str = Field(description='Email пользователя')
    name: str = Field(description='Имя пользователя')
    created_at: datetime = Field(description='Дата создания')
