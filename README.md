# Extractive Summarization

Простой, сервис экстрактивной суммаризации текста:
TF-скоринг слов + ранжирование предложений, отдаётся через FastAPI.

## Структура

- `extractive_summarization/` — библиотека (логика суммаризации + unit-тесты).
- `service/` — FastAPI-приложение и тесты API.
- `requirements/` — requirements-файлы для быстрой установки без Poetry.

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

```bash
uvicorn service.app:app --host 127.0.0.1 --port 8000 --reload
```

Swagger: <http://127.0.0.1:8000/docs>

## Тесты

```bash
pytest
```

## Линтеры и pre-commit

```bash
pre-commit install
pre-commit run --all-files
```

## Пример запроса

```bash
curl -X POST http://127.0.0.1:8000/summarize \
     -H "Content-Type: application/json" \
     -d '{"text":"Python is a language. Python is popular. Bananas are yellow.","num_sentences":2}'
```
