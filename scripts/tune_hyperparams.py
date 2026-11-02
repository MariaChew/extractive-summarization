"""
Подбор гиперпараметров суммаризатора с логированием прогонов в MLflow.

Скрипт запускается вручную или по расписанию (см. Model_retrain_BPMN.md,
этап «Обучение новой версии»). Каждая комбинация гиперпараметров —
отдельный прогон в MLflow с метриками и хешем датасета.

Запуск:
    poetry run python scripts/tune_hyperparams.py --dataset data/val.jsonl
"""

import argparse
import itertools
import json
import logging
import typing as t
from pathlib import Path

from extractive_summarization import ExtractiveSummarizer, SummarizerSettings
from extractive_summarization.metrics import RougeCalculator
from extractive_summarization.tracking import ExperimentTracker, compute_dataset_hash

logger = logging.getLogger(__name__)

# Сетка подбора. Значения подобраны под русскоязычные обращения;
# при смене домена сетку стоит пересмотреть.
DEFAULT_GRID: t.Dict[str, t.List[t.Any]] = {
    "ratio": [0.2, 0.25, 0.3, 0.35],
    "min_sentence_length": [2, 3, 4],
}

# Порог, ниже которого комбинация не считается пригодной
ROUGE_L_THRESHOLD = 0.35


def load_dataset(path: Path) -> t.List[t.Dict[str, str]]:
    """
    Загрузить датасет из JSONL: по объекту на строку.

    :param path: путь к файлу датасета
    :return: список объектов с полями text и reference
    """
    if not path.exists():
        raise FileNotFoundError(f"Датасет не найден: {path}")

    records = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"Некорректный JSON в строке {line_number}: {error}") from error
        if "text" not in item or "reference" not in item:
            raise ValueError(f"Строка {line_number}: нужны поля text и reference")
        records.append(item)

    if not records:
        raise ValueError(f"Датасет пуст: {path}")
    return records


def evaluate(
    summarizer: ExtractiveSummarizer,
    dataset: t.Sequence[t.Mapping[str, str]],
    settings: SummarizerSettings,
) -> t.Dict[str, float]:
    """
    Оценить комбинацию настроек на датасете.

    :param summarizer: суммаризатор
    :param dataset: записи с полями text и reference
    :param settings: настройки прогона
    :return: словарь метрик
    """
    calculator = RougeCalculator(summarizer.text_processor)
    pairs = [
        (summarizer.summarize(item["text"], settings), item["reference"])
        for item in dataset
    ]
    return calculator.evaluate_corpus(pairs)


def parse_args() -> argparse.Namespace:
    """
    Разобрать аргументы командной строки.

    :return: разобранные аргументы
    """
    parser = argparse.ArgumentParser(description="Подбор гиперпараметров суммаризатора")
    parser.add_argument("--dataset", type=Path, required=True, help="Путь к датасету (JSONL)")
    parser.add_argument("--tracking-uri", type=str, default=None, help="Адрес MLflow-сервера")
    parser.add_argument(
        "--log-level", type=str, default="INFO", help="Уровень логирования"
    )
    return parser.parse_args()


def main() -> None:
    """Точка входа: перебрать сетку и залогировать каждый прогон."""
    args = parse_args()
    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    dataset = load_dataset(args.dataset)
    dataset_hash = compute_dataset_hash(args.dataset)
    summarizer = ExtractiveSummarizer()
    tracker = ExperimentTracker(tracking_uri=args.tracking_uri)

    logger.info(
        "Загружено %d документов, хеш датасета %s, трекинг %s",
        len(dataset),
        dataset_hash,
        "включён" if tracker.enabled else "отключён",
    )

    best: t.Optional[t.Tuple[float, t.Dict[str, t.Any], str]] = None

    for ratio, min_len in itertools.product(
        DEFAULT_GRID["ratio"], DEFAULT_GRID["min_sentence_length"]
    ):
        params: t.Dict[str, t.Any] = {
            "ratio": ratio,
            "min_sentence_length": min_len,
        }
        settings = SummarizerSettings(**params)

        try:
            metrics = evaluate(summarizer, dataset, settings)
        except Exception:  # noqa: BLE001 - один сбойный прогон не должен ронять подбор
            logger.exception("Прогон %s упал, пропускаем", params)
            continue

        run_id = tracker.log_run(params, metrics, dataset_hash=dataset_hash)
        marker = "" if metrics["rouge_l"] >= ROUGE_L_THRESHOLD else " (ниже порога)"
        logger.info(
            "ratio=%.2f min_len=%d → ROUGE-L=%.3f%s%s",
            ratio,
            min_len,
            metrics["rouge_l"],
            marker,
            f" run_id={run_id}" if run_id else "",
        )

        if best is None or metrics["rouge_l"] > best[0]:
            best = (metrics["rouge_l"], params, dataset_hash)

    if best is None:
        logger.error("Ни один прогон не завершился успешно")
        raise SystemExit(1)

    score, params, dataset_hash = best
    logger.info("Лучшая комбинация: %s с ROUGE-L=%.3f", params, score)

    # Результат подбора — файл, который подхватывает следующий шаг процесса.
    result = {
        "best_params": params,
        "rouge_l": round(score, 4),
        "dataset_hash": dataset_hash,
        "threshold": ROUGE_L_THRESHOLD,
        "passed": score >= ROUGE_L_THRESHOLD,
    }
    out_path = Path("best_params.json")
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Результат записан в %s", out_path)


if __name__ == "__main__":
    main()
