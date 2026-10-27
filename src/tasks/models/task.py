from sqlalchemy import BigInteger, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database.base import Base, TimeTrackingMixin
from src.tasks.constants import STATUS_MAX_LENGTH, TITLE_MAX_LENGTH
from src.tasks.enums import TaskStatusEnum


class Task(TimeTrackingMixin, Base):
    """Задача пользователя."""

    __tablename__ = 'tasks'
    __table_args__ = (
        # фильтрация по статусу и статистика всегда идут в разрезе пользователя
        Index('ix_tasks_user_id_status', 'user_id', 'status'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('users.id', ondelete='CASCADE'),
        comment='ID пользователя-владельца',
    )
    title: Mapped[str] = mapped_column(String(TITLE_MAX_LENGTH), comment='Заголовок')
    description: Mapped[str | None] = mapped_column(Text, comment='Описание')
    # Статус хранится строкой (native_enum=False), а не PG ENUM: добавить новый статус можно без ALTER TYPE.
    # Допустимые значения защищены CHECK-ограничением ck_tasks_status, из БД значение читается как TaskStatusEnum.
    status: Mapped[TaskStatusEnum] = mapped_column(
        Enum(
            TaskStatusEnum,
            name='status',
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            length=STATUS_MAX_LENGTH,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        server_default=TaskStatusEnum.NEW.value,
        comment='Статус',
    )
