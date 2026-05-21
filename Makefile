install:
	pip install -r requirements.txt

dev:
	pip install -r requirements.txt && pip install black ruff pytest pytest-mock

test:
	pytest tests/ -v

lint:
	ruff check .

format:
	black .

check:
	ruff check . && black --check .

run:
	python cli.py
