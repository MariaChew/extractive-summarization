# =============================================================================
# Change Log
#
# Формат основан на Keep a Changelog (https://keepachangelog.com/ru/1.1.0/),
# версии — по Semantic Versioning (https://semver.org/lang/ru/).
# =============================================================================

## [Unreleased]

### Added
- Docker-образ сервиса суммаризации: многоступенчатая сборка, запуск от
  непривилегированного пользователя, встроенный healthcheck.
- `docker-compose.yml` для локального запуска в контейнере.
- `.dockerignore` — уменьшает контекст сборки и размер образа.
- `Makefile` с типовыми командами: линтеры, тесты, запуск, Docker.
- CI на GitHub Actions: линтеры, тесты и сборка Docker-образа на каждый
  push и pull request.

## [0.1.0] - 2026-02-01

### Added
- Библиотека `extractive_summarization`: TF-скоринг слов, ранжирование
  предложений, `TextProcessor` (разбиение на предложения, токенизация,
  стоп-слова для русского языка).
- `ExtractiveSummarizer` с настройками `num_sentences`, `ratio`,
  `min_sentence_length`, `max_sentences`.
- FastAPI-сервис: `GET /health`, `POST /summarize`.
- Unit-тесты библиотеки и тесты API (`pytest`).
- Конфигурация Poetry, pre-commit (black, isort, ruff, mypy).
- `requirements/` для установки без Poetry.
