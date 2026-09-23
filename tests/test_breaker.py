"""Тести зламу без ключа."""

from __future__ import annotations

import math
import random

import pytest

from freqcrack import M, METHODS, break_all_methods, break_caesar, encrypt, keyspace_bits

TEXT = (
    "The quick brown fox jumps over the lazy dog, and then it does so again "
    "because the sentence is famous for containing every letter of the "
    "alphabet at least once, which makes it a convenient test string."
)


@pytest.mark.parametrize("method", ["chi2", "unigram", "quadgram"])
@pytest.mark.parametrize("key", [0, 1, 7, 13, 25])
def test_all_scoring_methods_recover_the_key(method: str, key: int) -> None:
    result = break_caesar(encrypt(TEXT, key), method)
    assert result.key == key
    assert result.plaintext == TEXT


def test_ranking_covers_every_key_exactly_once() -> None:
    result = break_caesar(encrypt(TEXT, 11), "chi2")
    assert len(result.ranking) == M
    assert {k for k, _ in result.ranking} == set(range(M))


def test_winner_is_first_in_ranking() -> None:
    result = break_caesar(encrypt(TEXT, 4), "chi2")
    assert result.ranking[0][0] == result.key


def test_margin_is_non_negative() -> None:
    for key in (0, 9, 20):
        assert break_caesar(encrypt(TEXT, key), "chi2").margin >= 0.0


def test_break_all_methods_returns_every_method() -> None:
    results = break_all_methods(encrypt(TEXT, 6))
    assert set(results) == set(METHODS)
    assert all(r.key == 6 for r in results.values())


def test_unknown_method_is_rejected() -> None:
    with pytest.raises(ValueError):
        break_caesar("Khoor", "magic")


def test_case_and_punctuation_survive_the_break() -> None:
    original = "Mr. and Mrs. Dursley, of number four, Privet Drive, were proud to say."
    result = break_caesar(encrypt(original, 24), "chi2")
    assert result.plaintext == original


def test_keyspace_is_26_keys_not_2_to_the_26() -> None:
    """Ентропія ключа — це логарифм кількості варіантів, а не показник."""
    assert math.isclose(keyspace_bits(), math.log2(M), rel_tol=1e-12)
    assert 4.69 < keyspace_bits() < 4.71


def test_break_is_fast() -> None:
    result = break_caesar(encrypt(TEXT * 5, 3), "chi2")
    assert result.elapsed_s < 1.0


def test_chi2_and_quadgram_agree_on_long_texts() -> None:
    """На довгих текстах різні правила мають сходитися до одного ключа."""
    rng = random.Random(5)
    for _ in range(20):
        key = rng.randrange(M)
        ct = encrypt(TEXT, key)
        assert break_caesar(ct, "chi2").key == break_caesar(ct, "quadgram").key == key
