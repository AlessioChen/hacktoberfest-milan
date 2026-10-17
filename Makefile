.PHONY: install run test up down logs build notify clean bench

install:
	uv sync

run:
	uv run streamlit run app/main.py

test:
	uv run pytest

build:
	docker compose build

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f

notify:
	uv run python scripts/notify.py

clean:
	rm -rf .venv .pytest_cache

bench:
	uv run python scripts/bench_labels.py
