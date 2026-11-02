# syntax=docker/dockerfile:1

# Stage 1: builder — устанавливаем зависимости в изолированное venv
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.8.2 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/tmp/poetry-cache

WORKDIR /app

# Системные зависимости для сборки (нужны только на этом этапе)
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install "poetry==${POETRY_VERSION}"

# Сначала только манифесты — так слой с зависимостями кешируется
# и не пересобирается при каждом изменении кода.
COPY pyproject.toml poetry.lock ./

# --only main: dev-зависимости (pytest, black, ruff, mypy) в образ не попадают
RUN poetry install --only main --no-root \
    && rm -rf "${POETRY_CACHE_DIR}"

# Stage 2: runtime — тонкий образ только с тем, что нужно для запуска
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PORT=8000

# Непривилегированный пользователь: контейнер не должен работать от root
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash appuser

WORKDIR /app

# Только готовое venv из builder — pip, компиляторы и кеши в runtime не едут
COPY --from=builder /app/.venv /app/.venv

# Код приложения
COPY --chown=appuser:appuser extractive_summarization/ ./extractive_summarization/
COPY --chown=appuser:appuser service/ ./service/

USER appuser

EXPOSE 8000

# Контейнер считается живым, только если /health отвечает
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).status == 200 else 1)"

CMD ["uvicorn", "service.app:app", "--host", "0.0.0.0", "--port", "8000"]
