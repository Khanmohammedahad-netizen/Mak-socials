PY := venv311/Scripts/python.exe

.PHONY: test lint typecheck run migrate

test:
	$(PY) -m pytest

lint:
	$(PY) -m ruff check src/

typecheck:
	$(PY) -m mypy src/core/

run:
	$(PY) dashboard_api.py

migrate:
	$(PY) -m alembic upgrade head
