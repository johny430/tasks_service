import typing as t
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from src.core.api import api_router
from src.core.database.di import engine
from src.core.settings import setup_logging
from src.healthcheck import api as healthcheck_api

setup_logging()


@asynccontextmanager
async def lifespan(_: FastAPI) -> t.AsyncIterator[None]:
    yield
    await engine.dispose()


app = FastAPI(
    title='Tasks Service',
    description='Сервис учёта задач пользователей',
    version='0.1.0',
    lifespan=lifespan,
)

app.include_router(healthcheck_api.router)
app.include_router(api_router)


@app.get('/', include_in_schema=False)
async def redirect_to_docs() -> RedirectResponse:
    return RedirectResponse('/docs')
