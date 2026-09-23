"""
Злам шифру Цезаря без ключа.

Через малий простір ключів (26 варіантів) практичний злам шифру Цезаря
зводиться до повного перебору всіх 26 зсувів і вибору найкращого
кандидата за статистичним критерієм. Перебір тут тривіальний, тому вся
складність зосереджена у ВИРІШАЛЬНОМУ ПРАВИЛІ — саме різні правила й
порівнює ця робота:

    ``chi2``      — критерій хі-квадрат до таблиці частот з умови задачі;
    ``unigram``   — логарифмічна правдоподібність за частотами літер;
    ``quadgram``  — логарифмічна правдоподібність за квадриграмами;
    ``mostfreq``  — наївне правило «найчастіша літера → E» (без перебору).

Модуль не має зовнішніх залежностей: лише стандартна бібліотека.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable

from .caesar import M, decrypt
from .scoring import chi_squared, most_frequent_rule, unigram_score

#: Назви доступних правил рішення.
METHODS = ("chi2", "unigram", "quadgram", "mostfreq")


@dataclass
class BreakResult:
    """Результат зламу одного шифротексту."""

    method: str
    key: int
    plaintext: str
    score: float
    margin: float
    elapsed_s: float
    ranking: list[tuple[int, float]] = field(default_factory=list)

    def __str__(self) -> str:
        return "%-9s ключ=%2d  відрив=%9.2f  %.3f мс  %s" % (
            self.method, self.key, self.margin, self.elapsed_s * 1000,
            self.plaintext[:48],
        )


def _scorer(method: str) -> tuple[Callable[[str], float], bool]:
    """Повертає (функція оцінки, чи менше — краще)."""
    if method == "chi2":
        return chi_squared, True
    if method == "unigram":
        return unigram_score, False
    if method == "quadgram":
        from .ngrams import quadgram_score
        return quadgram_score, False
    raise ValueError("невідоме правило рішення: %r" % (method,))


def break_caesar(ciphertext: str, method: str = "chi2") -> BreakResult:
    """
    Зламати шифр Цезаря без ключа.

    :param method: правило рішення — один із :data:`METHODS`.
    """
    t0 = time.perf_counter()

    if method == "mostfreq":
        key = most_frequent_rule(ciphertext)
        plaintext = decrypt(ciphertext, key)
        return BreakResult(method, key, plaintext, 0.0, 0.0,
                           time.perf_counter() - t0, [])

    score_of, lower_is_better = _scorer(method)
    scored = [(score_of(decrypt(ciphertext, k)), k) for k in range(M)]
    scored.sort(reverse=not lower_is_better)

    best_score, best_key = scored[0]
    runner_up = scored[1][0] if len(scored) > 1 else best_score
    margin = abs(runner_up - best_score)

    return BreakResult(
        method=method,
        key=best_key,
        plaintext=decrypt(ciphertext, best_key),
        score=best_score,
        margin=margin,
        elapsed_s=time.perf_counter() - t0,
        ranking=[(k, s) for s, k in scored],
    )


def break_all_methods(ciphertext: str) -> dict[str, BreakResult]:
    """Прогін усіх чотирьох правил рішення на одному шифротексті."""
    return {m: break_caesar(ciphertext, m) for m in METHODS}


def keyspace_bits() -> float:
    """
    Ентропія ключа шифру Цезаря за рівноймовірного вибору зсуву:
    ``log2(26) ≈ 4.70`` біта. Це 26 варіантів, а не 2^26.
    """
    import math

    return math.log2(M)
