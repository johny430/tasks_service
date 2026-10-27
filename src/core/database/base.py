from datetime import datetime

from sqlalchemy import DateTime, MetaData
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func

# Явные имена ограничений: миграции не зависят от автогенерации имён в PostgreSQL,
# а ограничение можно удалить или пересоздать по известному имени.
NAMING_CONVENTION = {
    'ix': 'ix_%(table_name)s_%(column_0_N_name)s',
    'uq': 'uq_%(table_name)s_%(column_0_N_name)s',
    'ck': 'ck_%(table_name)s_%(constraint_name)s',
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'pk': 'pk_%(table_name)s',
}


class Base(DeclarativeBase, AsyncAttrs):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment='Дата создания'
    )


class UpdatedAtMixin:
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment='Дата обновления'
    )


class TimeTrackingMixin(CreatedAtMixin, UpdatedAtMixin):
    pass
