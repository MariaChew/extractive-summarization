"""
FastAPI-приложение сервиса экстрактивной суммаризации.

Продовые аспекты, добавленные к базовой версии:
- структурированное логирование вместо вывода в консоль;
- middleware для измерения latency каждого запроса;
- глобальный обработчик непредвиденных ошибок;
- версия сервиса вынесена в константу и попадает в /health.
"""

import logging
import time
import typing as t

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from typing_extensions import Annotated

from extractive_summarization import ExtractiveSummarizer, SummarizerSettings
from service.dependencies import get_summarizer
from service.schemas import HealthResponse, SummarizeRequest, SummarizeResponse

SERVICE_VERSION = "0.1.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("service")

app = FastAPI(
    title="Extractive Summarization Service",
    version=SERVICE_VERSION,
    description="Simple extractive summarization over TF-based sentence scoring.",
)

SummarizerDep = Annotated[ExtractiveSummarizer, Depends(get_summarizer)]


@app.middleware("http")
async def log_requests(request: Request, call_next: t.Callable) -> t.Any:
    """
    Залогировать запрос и время его обработки.

    :param request: входящий запрос
    :param call_next: следующий обработчик в цепочке
    :return: ответ приложения
    """
    started = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - started) * 1000

    logger.info(
        "%s %s -> %s за %.1f мс",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.1f}"
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Вернуть аккуратный ответ на непредвиденную ошибку.

    :param request: входящий запрос
    :param exc: возникшее исключение
    :return: JSON с описанием ошибки
    """
    logger.exception("Непредвиденная ошибка на %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутренняя ошибка сервиса"},
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """
    Проверка работоспособности сервиса.

    :return: статус и версия сервиса
    """
    return HealthResponse(status="ok", version=SERVICE_VERSION)


@app.post("/summarize", response_model=SummarizeResponse)
def summarize(
    payload: SummarizeRequest,
    summarizer: SummarizerDep,
) -> SummarizeResponse:
    """
    Суммаризировать переданный текст экстрактивно.

    :param payload: тело запроса
    :param summarizer: экземпляр суммаризатора
    :return: саммари и число предложений в нём
    """
    settings = SummarizerSettings(
        num_sentences=payload.num_sentences,
        ratio=payload.ratio,
    )
    sentences = summarizer.select_sentences(payload.text, settings)
    summary = " ".join(sentences)

    logger.info(
        "Суммаризация: вход %d символов, выход %d предложений",
        len(payload.text),
        len(sentences),
    )

    return SummarizeResponse(
        summary=summary,
        num_sentences=len(sentences),
        input_characters=len(payload.text),
        output_characters=len(summary),
    )
