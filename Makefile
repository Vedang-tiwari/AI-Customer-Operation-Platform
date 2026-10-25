.PHONY: help install dev worker test lint seed up down

help:
	@echo "Available commands:"
	@echo "  make install    Install backend dependencies into venv"
	@echo "  make dev        Run FastAPI local dev server with venv"
	@echo "  make worker     Run Celery worker locally"
	@echo "  make test       Run test suite in venv"
	@echo "  make seed       Seed the database with sample data"
	@echo "  make up         Start Docker Compose services"
	@echo "  make down       Stop Docker Compose services"

install:
	backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt

dev:
	backend/.venv/Scripts/python.exe -m uvicorn app.main:app --app-dir backend --reload --port 8000

worker:
	cd backend && .venv/Scripts/celery.exe -A app.workers.celery_app:celery_app worker --loglevel=info

test:
	backend/.venv/Scripts/python.exe -m pytest backend/tests -v

seed:
	backend/.venv/Scripts/python.exe -m app.db.seed

up:
	docker compose up -d

down:
	docker compose down
