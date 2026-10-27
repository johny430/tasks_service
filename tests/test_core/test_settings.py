from sqlalchemy import make_url

from src.core.settings.base import Settings


def test_postgres_url_keeps_special_chars_in_credentials() -> None:
    """Спецсимволы в логине и пароле экранируются и не ломают разбор URL"""
    settings = Settings(
        DB_USERNAME='us@er', DB_PASSWORD='p@ss:/%41word', DB_HOST='postgres', DB_PORT=5432, DB_NAME='tasks'
    )

    url = make_url(settings.postgres_url.render_as_string(hide_password=False))

    assert (url.username, url.password, url.host, url.port, url.database) == (
        'us@er',
        'p@ss:/%41word',
        'postgres',
        5432,
        'tasks',
    )
