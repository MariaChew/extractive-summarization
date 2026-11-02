"""
Метрики качества экстрактивной суммаризации.

Модуль намеренно не тянет внешних зависимостей: ROUGE реализован
на стандартной библиотеке, поэтому метрики считаются и в CI,
и в проде одинаково, без установки дополнительных пакетов.
"""

import typing as t
from collections import Counter

from extractive_summarization.utils.text_processing import TextProcessor


def _tokenize(text: str, processor: t.Optional[TextProcessor] = None) -> t.List[str]:
    """
    Привести текст к списку токенов в нижнем регистре.

    :param text: исходный текст
    :param processor: обработчик текста (по умолчанию создаётся новый)
    :return: список токенов
    """
    processor = processor or TextProcessor()
    return processor.tokenize(text)


def _ngrams(tokens: t.Sequence[str], n: int) -> Counter:
    """
    Построить мультимножество n-грамм.

    :param tokens: последовательность токенов
    :param n: размер n-граммы
    :return: счётчик n-грамм
    """
    if n <= 0:
        raise ValueError("Размер n-граммы должен быть положительным")
    if len(tokens) < n:
        return Counter()
    return Counter(tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1))


def _lcs_length(first: t.Sequence[str], second: t.Sequence[str]) -> int:
    """
    Длина наибольшей общей подпоследовательности.

    :param first: первая последовательность
    :param second: вторая последовательность
    :return: длина НОП
    """
    if not first or not second:
        return 0

    previous = [0] * (len(second) + 1)
    for token_a in first:
        current = [0] * (len(second) + 1)
        for j, token_b in enumerate(second, start=1):
            if token_a == token_b:
                current[j] = previous[j - 1] + 1
            else:
                current[j] = max(previous[j], current[j - 1])
        previous = current
    return previous[-1]


def _f1(overlap: int, total_candidate: int, total_reference: int) -> float:
    """
    Посчитать F1 по числу совпавших и общему числу единиц.

    :param overlap: число совпавших единиц
    :param total_candidate: всего единиц в кандидате
    :param total_reference: всего единиц в эталоне
    :return: F1 в диапазоне [0, 1]
    """
    if total_candidate == 0 or total_reference == 0:
        return 0.0
    precision = overlap / total_candidate
    recall = overlap / total_reference
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


class RougeCalculator:
    """Расчёт ROUGE-1, ROUGE-2 и ROUGE-L для одного кандидата против эталона."""

    def __init__(self, text_processor: t.Optional[TextProcessor] = None) -> None:
        """
        Инициализировать калькулятор.

        :param text_processor: обработчик текста
        """
        self.text_processor = text_processor or TextProcessor()

    def rouge_n(self, candidate: str, reference: str, n: int) -> float:
        """
        Посчитать ROUGE-N (F1).

        :param candidate: саммари модели
        :param reference: эталонное саммари
        :param n: размер n-граммы (1 — ROUGE-1, 2 — ROUGE-2)
        :return: значение F1
        """
        cand_tokens = _tokenize(candidate, self.text_processor)
        ref_tokens = _tokenize(reference, self.text_processor)

        cand_ngrams = _ngrams(cand_tokens, n)
        ref_ngrams = _ngrams(ref_tokens, n)

        overlap = sum((cand_ngrams & ref_ngrams).values())
        return _f1(overlap, sum(cand_ngrams.values()), sum(ref_ngrams.values()))

    def rouge_l(self, candidate: str, reference: str) -> float:
        """
        Посчитать ROUGE-L (F1) по наибольшей общей подпоследовательности.

        :param candidate: саммари модели
        :param reference: эталонное саммари
        :return: значение F1
        """
        cand_tokens = _tokenize(candidate, self.text_processor)
        ref_tokens = _tokenize(reference, self.text_processor)

        lcs = _lcs_length(cand_tokens, ref_tokens)
        return _f1(lcs, len(cand_tokens), len(ref_tokens))

    def evaluate_corpus(
        self,
        pairs: t.Sequence[t.Tuple[str, str]],
    ) -> t.Dict[str, float]:
        """
        Средние метрики по корпусу пар «кандидат — эталон».

        :param pairs: последовательность пар (candidate, reference)
        :return: словарь усреднённых метрик
        """
        if not pairs:
            return {"rouge_1": 0.0, "rouge_2": 0.0, "rouge_l": 0.0, "documents": 0.0}

        rouge_1 = [self.rouge_n(c, r, 1) for c, r in pairs]
        rouge_2 = [self.rouge_n(c, r, 2) for c, r in pairs]
        rouge_l = [self.rouge_l(c, r) for c, r in pairs]

        count = len(pairs)
        return {
            "rouge_1": sum(rouge_1) / count,
            "rouge_2": sum(rouge_2) / count,
            "rouge_l": sum(rouge_l) / count,
            "documents": float(count),
        }
