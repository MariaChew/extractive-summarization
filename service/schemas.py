"""Pydantic-схемы запросов и ответов сервиса."""

import typing as t

from pydantic import BaseModel, Field


class SummarizeRequest(BaseModel):
    """Тело запроса к /summarize."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=100_000,
        description="Текст для суммаризации.",
    )
    num_sentences: t.Optional[int] = Field(
        default=None,
        ge=1,
        description="Точное число предложений в саммари. Приоритет над ratio.",
    )
    ratio: float = Field(
        default=0.3,
        gt=0.0,
        le=1.0,
        description="Доля предложений, если num_sentences не задан.",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "text": "Python — это язык программирования. Python популярен.",
                    "num_sentences": 1,
                }
            ]
        }
    }


class SummarizeResponse(BaseModel):
    """Тело ответа /summarize."""

    summary: str = Field(..., description="Извлечённое саммари.")
    num_sentences: int = Field(..., description="Число предложений в саммари.")
    input_characters: int = Field(
        ...,
        ge=0,
        description="Длина исходного текста в символах.",
    )
    output_characters: int = Field(
        ...,
        ge=0,
        description="Длина саммари в символах.",
    )


class HealthResponse(BaseModel):
    """Тело ответа /health."""

    status: str = Field(..., description="Статус сервиса.")
    version: str = Field(..., description="Версия сервиса.")
