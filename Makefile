.PHONY: pyclean
pyclean:
	find . | grep -E "(__pycache__|\.pyc$$)" | xargs rm -rf

.PHONY: prepare
prepare:
	cp .env.example .env

.PHONY: sync
sync:
	uv sync

.PHONY: format
format:
	uv run ruff check --fix --show-fixes .
	uv run ruff format .

.PHONY: lint
lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy .

.PHONY: test
test:
	uv run pytest -vv --cov

.PHONY: test-docker
test-docker:
	docker compose run --rm --build tests

.PHONY: runserver
runserver:
	uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

.PHONY: migrate
migrate:
	uv run alembic upgrade head

.PHONY: revision
revision:
	uv run alembic revision --autogenerate -m "$(msg)"

.PHONY: down-migrate
down-migrate:
	uv run alembic downgrade -$(cnt)

.PHONY: up
up:
	docker compose up -d postgres

.PHONY: down
down:
	docker compose down
