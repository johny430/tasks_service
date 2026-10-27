from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database.base import Base, CreatedAtMixin
from src.users.constants import EMAIL_MAX_LENGTH, NAME_MAX_LENGTH


class User(CreatedAtMixin, Base):
    """Пользователь, владелец задач."""

    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(
        String(EMAIL_MAX_LENGTH),
        unique=True,
        comment='Email в нижнем регистре',
    )
    name: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH), comment='Имя')
