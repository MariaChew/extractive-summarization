# =============================================================================
# README.md — обновлённая версия
#
# Что изменилось относительно текущего README:
# 1. Добавлен бейдж CI в самом верху.
# 2. Добавлены разделы "Запуск через Docker" и "CI/CD".
# 3. Добавлена шпаргалка по Makefile и структура репозитория.
#
# ВАЖНО: замени <USERNAME> и <REPO> на свои значения —
# GitHub не подставит их сам, бейдж без этого не заработает.
# =============================================================================

# Extractive Summarization

[![CI](https://github.com/<USERNAME>/<REPO>/actions/workflows/ci.yml/badge.svg)](https://github.com/<USERNAME>/<REPO>/actions/workflows/ci.yml)

Простой сервис экстрактивной суммаризации текста:
TF-скоринг слов + ранжирование предложений, отдаётся через FastAPI.

## Структура

```
extractive_summarization/   # библиотека: логика суммаризации + unit-тесты
service/                    # FastAPI-приложение и тесты API
requirements/               # requirements-файлы для установки без Poetry
docker/                     # Dockerfile
.github/workflows/          # конфигурация CI
```

## Установка

```bash
git clone <repo-url>
cd extractive-summarization

# вариант 1 (рекомендуется) — через Poetry
poetry install
poetry shell

# вариант 2 — через pip/requirements
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements/requirements-dev.txt
```

## Запуск сервиса

### Локально

```bash
poetry run uvicorn service.app:app --host 127.0.0.1 --port 8000 --reload
```

Swagger: http://127.0.0.1:8000/docs

### Через Docker

```bash
# сборка образа
docker build -f docker/Dockerfile -t extractive-summarization:0.1.0 .

# запуск
docker run --rm -p 8000:8000 --name extractive-summarization extractive-summarization:0.1.0
```

Сервис будет доступен на http://127.0.0.1:8000, документация — на `/docs`.

Проверка состояния контейнера (включая встроенный healthcheck):

```bash
docker ps                       # в колонке STATUS будет (healthy)
curl http://127.0.0.1:8000/health
```

### Через docker compose

```bash
docker compose up --build -d    # поднять
docker compose logs -f api      # логи
docker compose down             # остановить
```

## Makefile — шпаргалка команд

```bash
make help           # список всех команд
make install        # установить зависимости
make lint           # black + isort + ruff + mypy
make format         # отформатировать код
make test           # тесты
make test-cov       # тесты с покрытием
make run            # запустить сервис локально
make docker-build   # собрать образ
make docker-up      # запустить через compose
```

## Тесты

```bash
pytest
# или
make test
```

## Линтеры и pre-commit

```bash
pre-commit install                  # включить хуки в этом репозитории
pre-commit run --all-files          # прогнать по всем файлам вручную
```

## CI/CD

В репозитории настроен GitHub Actions (`.github/workflows/ci.yml`).
На каждый push в `main`/`master`/`develop` и на каждый pull request
автоматически запускаются три задачи:

| Job | Что проверяет |
| --- | --- |
| `Lint & format` | black, isort, ruff, mypy |
| `Tests` | `pytest` на Python 3.12 |
| `Docker build` | что Dockerfile собирается без ошибок |

Результат виден во вкладке **Actions** и рядом с каждым коммитом.

## Пример запроса

```bash
curl -X POST http://127.0.0.1:8000/summarize \
     -H "Content-Type: application/json" \
     -d '{"text":"Python is a language. Python is popular. Bananas are yellow.","num_sentences":2}'
```

## Лицензия

MIT
