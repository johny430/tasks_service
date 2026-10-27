import typing as t

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    APPLICATION_NAME: str = 'tasks_service'

    DB_USERNAME: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    LOG_LEVEL: t.Literal['DEBUG', 'INFO', 'WARNING', 'ERROR'] = 'INFO'

    model_config: t.ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file='./.env', env_file_encoding='utf-8', extra='ignore', case_sensitive=True
    )

    @property
    def postgres_url(self) -> URL:
        """URL подключения к БД. URL.create экранирует спецсимволы в логине и пароле (@, /, :, %)."""
        return URL.create(
            drivername='postgresql+asyncpg',
            username=self.DB_USERNAME,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT,
            database=self.DB_NAME,
        )


settings = Settings()  # type: ignore[call-arg]
