"""
Тести метрик.

Центральне місце — різниця між двома метриками:
індекс відповідності ІНВАРІАНТНИЙ щодо зсуву (тому не дає ключа),
а хі-квадрат — ні (тому дає).
"""

from __future__ import annotations

import math
import random

from freqcrack import (
    ALPHABET,
    M,
    BEKER_PIPER_FREQ,
    IOC_RANDOM,
    PUZZLE_FREQ,
    chi_squared,
    compare_tables,
    encrypt,
    index_of_coincidence,
    letter_frequencies,
    most_frequent_rule,
    shannon_entropy,
    unicity_distance,
    unigram_score,
)
from freqcrack.ngrams import NgramScorer, default_scorer, quadgram_score

ENGLISH = (
    "It is a truth universally acknowledged, that a single man in possession "
    "of a good fortune, must be in want of a wife. However little known the "
    "feelings or views of such a man may be on his first entering a "
    "neighbourhood, this truth is so well fixed in the minds of the "
    "surrounding families, that he is considered the rightful property."
)


# --------------------------------------------------------------------------- #
#  Таблиці частот
# --------------------------------------------------------------------------- #

def test_puzzle_table_sums_to_100() -> None:
    assert abs(sum(PUZZLE_FREQ.values()) - 100.0) < 0.05


def test_both_tables_agree_on_most_frequent_letter() -> None:
    assert max(PUZZLE_FREQ, key=PUZZLE_FREQ.get) == "E"
    assert max(BEKER_PIPER_FREQ, key=BEKER_PIPER_FREQ.get) == "E"


def test_tables_are_close_but_not_identical() -> None:
    cmp = compare_tables()
    assert cmp["max_abs_diff_pp"] > 0.0, "таблиці мали б відрізнятися"
    assert cmp["max_abs_diff_pp"] < 1.0, "але не більш ніж на 1 в. п."
    assert cmp["argmax_letter_matches"] == 1.0


# --------------------------------------------------------------------------- #
#  Індекс відповідності проти хі-квадрат
# --------------------------------------------------------------------------- #

def test_ioc_is_invariant_under_shift() -> None:
    """
    Ключова властивість: зсув не змінює індексу відповідності, бо лише
    переставляє стовпчики гістограми. Тому IoC не може дати ключа.
    """
    base = index_of_coincidence(ENGLISH)
    for k in range(M):
        assert abs(index_of_coincidence(encrypt(ENGLISH, k)) - base) < 1e-12


def test_chi_squared_is_not_shift_invariant() -> None:
    """А хі-квадрат змінюється — саме тому він і визначає ключ."""
    values = {round(chi_squared(encrypt(ENGLISH, k)), 6) for k in range(M)}
    assert len(values) == M, "усі 26 значень мають бути різними"


def test_chi_squared_minimal_at_zero_shift_for_plain_english() -> None:
    scores = [chi_squared(encrypt(ENGLISH, k)) for k in range(M)]
    assert scores.index(min(scores)) == 0


def test_ioc_of_english_and_random() -> None:
    assert 0.055 < index_of_coincidence(ENGLISH) < 0.085
    rng = random.Random(0)
    noise = "".join(rng.choice(ALPHABET) for _ in range(20000))
    assert abs(index_of_coincidence(noise) - IOC_RANDOM) < 0.003


# --------------------------------------------------------------------------- #
#  Правила рішення
# --------------------------------------------------------------------------- #

def test_unigram_score_prefers_english() -> None:
    rng = random.Random(1)
    noise = "".join(rng.choice(ALPHABET) for _ in range(len(ENGLISH)))
    assert unigram_score(ENGLISH) > unigram_score(noise)


def test_quadgram_score_prefers_english() -> None:
    rng = random.Random(2)
    noise = "".join(rng.choice(ALPHABET) for _ in range(300))
    assert quadgram_score(ENGLISH[:300]) > quadgram_score(noise)


def test_most_frequent_rule_on_clean_english() -> None:
    """На достатньо довгому тексті наївне правило теж спрацьовує."""
    for k in (0, 5, 13, 25):
        assert most_frequent_rule(encrypt(ENGLISH, k)) == k


def test_most_frequent_rule_fails_when_top_letter_is_not_e() -> None:
    """
    Правило спирається рівно на одну літеру, тому помиляється щоразу,
    коли найчастіша літера відкритого тексту — не E. У рядку «Hi Bob»
    найчастіша літера B, і правило зміщує відповідь на сталу величину
    для будь-якого справжнього ключа.
    """
    text = "Hi Bob"
    assert max(ALPHABET, key=lambda ch: text.upper().count(ch)) == "B"
    offset = (ord("B") - ord("E")) % M
    for k in range(M):
        assert most_frequent_rule(encrypt(text, k)) == (k + offset) % M
        assert most_frequent_rule(encrypt(text, k)) != k


def test_scorers_handle_text_without_letters() -> None:
    assert chi_squared("12345 !!!") == math.inf
    assert unigram_score("12345 !!!") == -math.inf
    assert index_of_coincidence("1") == 0.0


# --------------------------------------------------------------------------- #
#  Інші метрики
# --------------------------------------------------------------------------- #

def test_entropy_bounds() -> None:
    rng = random.Random(3)
    uniform = "".join(rng.choice(ALPHABET) for _ in range(20000))
    assert 4.65 < shannon_entropy(uniform) <= 4.7005
    assert shannon_entropy("aaaa") == 0.0
    assert shannon_entropy(ENGLISH) < shannon_entropy(uniform)


def test_letter_frequencies_sum_to_100() -> None:
    freqs = letter_frequencies(ENGLISH)
    assert abs(sum(freqs) - 100.0) < 1e-9
    assert len(freqs) == M


def test_unicity_distance_for_caesar() -> None:
    """
    Для 26 ключів оцінка дуже мала — близько 1,5 символу. Це наслідок
    крихітного простору ключів, а не властивість конкретного алгоритму.
    """
    u = unicity_distance(math.log2(M))
    assert 1.0 < u < 2.0
    assert unicity_distance(math.log2(math.factorial(M))) > 25


def test_fallback_scorer_when_model_missing(tmp_path) -> None:
    scorer = NgramScorer(tmp_path / "missing.txt.gz")
    assert scorer.n == 1
    assert "fallback" in scorer.source
    assert scorer.score("THEQUICKBROWNFOX") > scorer.score("ZZZZZZZZZZZZZZZZ")


def test_default_scorer_is_cached() -> None:
    assert default_scorer() is default_scorer()
