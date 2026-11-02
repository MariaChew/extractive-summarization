"""
Трекинг экспериментов подбора гиперпараметров через MLflow.

Особенность проекта: `ExtractiveSummarizer` — модель без обучаемых весов,
поэтому «прогон» здесь означает одну комбинацию гиперпараметров,
оценённую на конкретном датасете. MLflow используется как журнал
экспериментов и как реестр версий конфигурации модели.

Модуль спроектирован так, что при отсутствии MLflow (прод-образ,
минимальное окружение) трекинг молча отключается, а расчёт продолжается.
"""

import hashlib
import logging
import typing as t
from pathlib import Path

logger = logging.getLogger(__name__)

try:  # pragma: no cover - зависит от окружения
    import mlflow

    MLFLOW_AVAILABLE = True
except ImportError:  # pragma: no cover - штатная ситуация в проде
    mlflow = None  # type: ignore[assignment]
    MLFLOW_AVAILABLE = False

EXPERIMENT_NAME = "extractive-summarization-hyperparams"


def is_tracking_enabled() -> bool:
    """
    Проверить, доступен ли MLflow в текущем окружении.

    :return: True, если трекинг возможен
    """
    return MLFLOW_AVAILABLE


def compute_dataset_hash(dataset_path: t.Union[str, Path]) -> str:
    """
    Посчитать короткий хеш содержимого датасета.

    :param dataset_path: путь к файлу датасета
    :return: первые 12 символов sha256
    """
    path = Path(dataset_path)
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def build_model_artifact(params: t.Mapping[str, t.Any]) -> t.Dict[str, t.Any]:
    """
    Собрать описание конфигурации модели для сохранения как артефакт.

    :param params: гиперпараметры прогона
    :return: словарь-описание модели
    """
    return {
        "algorithm": "tf_sentence_scoring",
        "model_type": "extractive",
        "trainable_parameters": 0,
        "settings": dict(params),
    }


class ExperimentTracker:
    """Обёртка над MLflow: логирование прогонов и работа с реестром моделей."""

    def __init__(
        self,
        experiment_name: str = EXPERIMENT_NAME,
        tracking_uri: t.Optional[str] = None,
    ) -> None:
        """
        Инициализировать трекер.

        :param experiment_name: имя эксперимента в MLflow
        :param tracking_uri: адрес MLflow-сервера (по умолчанию из окружения)
        """
        self.experiment_name = experiment_name
        self.enabled = is_tracking_enabled()
        self._run_id: t.Optional[str] = None

        if not self.enabled:
            logger.info(
                "MLflow недоступен: прогоны не логируются, расчёт продолжается"
            )
            return

        if tracking_uri:
            mlflow.set_tracking_uri(tracking_uri)

        mlflow.set_experiment(self.experiment_name)

    def log_run(
        self,
        params: t.Mapping[str, t.Any],
        metrics: t.Mapping[str, float],
        dataset_hash: t.Optional[str] = None,
        tags: t.Optional[t.Mapping[str, str]] = None,
    ) -> t.Optional[str]:
        """
        Залогировать один прогон подбора гиперпараметров.

        :param params: комбинация гиперпараметров
        :param metrics: метрики прогона
        :param dataset_hash: хеш датасета
        :param tags: дополнительные метки
        :return: идентификатор прогона или None, если трекинг отключён
        """
        if not self.enabled:
            return None

        with mlflow.start_run() as run:
            mlflow.log_params(dict(params))
            mlflow.log_metrics(dict(metrics))

            run_tags = {
                "model_type": "extractive_tf",
                "dataset_hash": dataset_hash or "unknown",
            }
            if tags:
                run_tags.update(dict(tags))
            mlflow.set_tags(run_tags)

            mlflow.log_dict(build_model_artifact(params), "model_config.json")

            self._run_id = str(run.info.run_id)
            return self._run_id

    def register_model_version(
        self,
        model_name: str,
        artifact: t.Mapping[str, t.Any],
        metrics: t.Mapping[str, float],
    ) -> t.Optional[str]:
        """
        Зарегистрировать новую версию конфигурации модели в реестре MLflow.

        :param model_name: имя модели в реестре
        :param artifact: описание конфигурации модели
        :param metrics: метрики версии
        :return: номер версии в виде строки или None, если трекинг отключён
        """
        if not self.enabled:
            return None

        with mlflow.start_run() as run:
            mlflow.log_dict(dict(artifact), "model_config.json")
            mlflow.log_metrics(dict(metrics))
            model_info = mlflow.register_model(
                model_uri=f"runs:/{run.info.run_id}/model_config.json",
                name=model_name,
            )
            return str(model_info.version)
