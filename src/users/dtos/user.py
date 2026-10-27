from datetime import datetime

from src.core.schemas.base import BaseFromAttrsModel


class UserDTO(BaseFromAttrsModel):
    """DTO для работы с пользователем"""

    id: int
    email: str
    name: str
    created_at: datetime
