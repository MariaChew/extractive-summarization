.PHONY: help install lint format test test-cov run pre-commit docker-build docker-up docker-down docker-logs clean

# Значения по умолчанию
IMAGE ?= extractive-summarization
TAG   ?= 0.1.0

help: ## Показать список команд
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install: ## Установить все зависимости (включая dev) через Poetry
	poetry install

lint: ## Проверить код линтерами и типами
	poetry run ruff check .
	poetry run black --check .
	poetry run isort --check-only .
	poetry run mypy extractive_summarization service

format: ## Отформатировать код
	poetry run black .
	poetry run isort .

test: ## Запустить тесты
	poetry run pytest

test-cov: ## Запустить тесты с покрытием (терминал + htmlcov/)
	poetry run pytest --cov=. --cov-report=term-missing --cov-report=html

run: ## Запустить сервис локально
	poetry run uvicorn service.app:app --host 127.0.0.1 --port 8000 --reload

pre-commit: ## Прогнать все pre-commit хуки по всем файлам
	poetry run pre-commit run --all-files

docker-build: ## Собрать Docker-образ
	docker build -f docker/Dockerfile -t $(IMAGE):$(TAG) .

docker-up: ## Поднять сервис через docker compose
	docker compose up --build -d

docker-down: ## Остановить сервис
	docker compose down

docker-logs: ## Логи контейнера
	docker compose logs -f api

clean: ## Удалить кеши и артефакты
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov dist build
	find . -type d -name __pycache__ -exec rm -rf {} +
