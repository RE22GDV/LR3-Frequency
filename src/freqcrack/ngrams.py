"""
Статистична модель англійської мови на квадриграмах.

Використовується як четверте, найсильніше правило рішення: на відміну
від частот окремих літер, квадриграми враховують ще й порядок символів.

Модель натренована на ~5.6 млн літер текстів із суспільного надбання
(див. ``tools/build_ngrams.py``); у репозиторії зберігається лише похідна
статистика частот, а не самі тексти.
"""

from __future__ import annotations

import gzip
import math
from pathlib import Path
from typing import Sequence

from .caesar import ALPHABET, M
from .frequencies import PUZZLE_FREQ

_A = ord("A")

DEFAULT_MODEL = Path(__file__).resolve().parents[2] / "data" / "english_quadgrams.txt.gz"


class NgramScorer:
    """
    Оцінювач «англійськості» тексту за квадриграмами.

    Квадриграма адресується цілим числом у системі числення за основою
    26, а таблиця логімовірностей — плоский список довжиною 26^4.
    """

    __slots__ = ("n", "table", "floor", "corpus_size", "source")

    def __init__(self, path: Path | str | None = None, n: int = 4) -> None:
        self.n = n
        path = Path(path) if path is not None else DEFAULT_MODEL

        counts: dict[str, int] = {}
        header = ""
        if path.exists():
            opener = gzip.open if str(path).endswith(".gz") else open
            with opener(path, "rt", encoding="ascii") as fh:  # type: ignore[operator]
                for line in fh:
                    if line.startswith("#"):
                        header = line.strip()
                        continue
                    gram, _, cnt = line.partition(" ")
                    if len(gram) == n:
                        counts[gram] = int(cnt)

        if counts:
            self._build(counts)
            self.corpus_size = sum(counts.values())
            self.source = "%s (%s)" % (path.name, header.lstrip("# "))
        else:
            self._fallback()
            self.corpus_size = 0
            self.source = "unigram-fallback (файл моделі не знайдено)"

    def _build(self, counts: dict[str, int]) -> None:
        total = sum(counts.values())
        self.floor = math.log10(0.01 / total)
        table = [self.floor] * (M ** self.n)
        for gram, cnt in counts.items():
            idx = 0
            for ch in gram:
                idx = idx * M + (ord(ch) - _A)
            table[idx] = math.log10(cnt / total)
        self.table = table

    def _fallback(self) -> None:
        self.n = 1
        self.floor = math.log10(1e-6)
        self.table = [math.log10(max(PUZZLE_FREQ[ch], 1e-4) / 100.0) for ch in ALPHABET]

    # ------------------------------------------------------------------ #

    def score_indices(self, seq: Sequence[int]) -> float:
        n, table = self.n, self.table
        length = len(seq)
        if length < n:
            return self.floor * max(length, 1)
        if n == 1:
            return sum(table[v] for v in seq)
        stride = M ** (n - 1)
        idx = 0
        for k in range(n):
            idx = idx * M + seq[k]
        total = table[idx]
        for k in range(n, length):
            idx = (idx % stride) * M + seq[k]
            total += table[idx]
        return total

    def score(self, text: str) -> float:
        """Логправдоподібність тексту; не-літерні символи ігноруються."""
        seq = [ord(ch) - _A for ch in text.upper() if "A" <= ch.upper() <= "Z"]
        return self.score_indices(seq)

    def __repr__(self) -> str:
        return "NgramScorer(n=%d, source=%r)" % (self.n, self.source)


_DEFAULT: NgramScorer | None = None


def default_scorer() -> NgramScorer:
    """Лінива глобальна модель — щоб не перечитувати файл на кожен виклик."""
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = NgramScorer()
    return _DEFAULT


def quadgram_score(text: str) -> float:
    """Зручна обгортка над глобальною моделлю."""
    return default_scorer().score(text)
