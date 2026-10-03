PY ?= venv/bin/python

.PHONY: install up down reset logs db run test test-unit test-acceptance test-integration lint

install:
	$(PY) -m pip install -r requirements-dev.txt

up:
	docker compose up --build -d

down:
	docker compose down

reset:  ## apaga o volume do banco e recria (re-executa db/init)
	docker compose down -v && docker compose up --build -d

logs:
	docker compose logs -f api

db:  ## sobe só o Postgres (para rodar a API local)
	docker compose up --build -d db

run:
	$(PY) -m uvicorn app.main:app --reload

test:
	$(PY) -m pytest

test-unit:
	$(PY) -m pytest tests/unit

test-acceptance:
	$(PY) -m pytest tests/acceptance

test-integration:
	$(PY) -m pytest tests/integration -m integration

lint:
	$(PY) -m ruff check . && $(PY) -m mypy app
