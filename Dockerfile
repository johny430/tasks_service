FROM ghcr.io/astral-sh/uv:0.11.7 AS uv


FROM python:3.13-slim AS base

ARG USERNAME=app
ARG USER_UID=1000
ARG USER_GID=$USER_UID

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/usr/local \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN groupadd --gid $USER_GID $USERNAME && useradd --no-create-home --uid $USER_UID --gid $USER_GID $USERNAME

WORKDIR /app

COPY pyproject.toml uv.lock ./
# uv и его кэш подключаются только на время сборки и в образ не попадают
RUN --mount=from=uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project --python-preference only-system


FROM base AS application

COPY alembic.ini ./
COPY src ./src
USER $USERNAME

EXPOSE 8000
HEALTHCHECK --interval=5s --timeout=3s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthcheck')" || exit 1
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]


FROM base AS tests

RUN --mount=from=uv,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --python-preference only-system
# pytest и coverage пишут кэш и отчёт в рабочую директорию
RUN chown $USERNAME:$USERNAME /app
COPY --chown=$USERNAME:$USERNAME alembic.ini conftest.py ./
COPY --chown=$USERNAME:$USERNAME src ./src
COPY --chown=$USERNAME:$USERNAME tests ./tests
USER $USERNAME

CMD ["pytest", "-vv", "--cov"]
