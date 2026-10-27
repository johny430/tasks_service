from pydantic import BaseModel, ConfigDict, Field


class BaseFromAttrsModel(BaseModel):
    """
    Модель нужна для того, чтобы можно в model_validate
    передавать сразу объект с атрибутами для валидации.
    """

    model_config = ConfigDict(from_attributes=True)


class ErrorResponseSchema(BaseModel):
    """Тело ответа с ошибкой (формат HTTPException в FastAPI)."""

    detail: str = Field(description='Описание ошибки')
