"""Модульні тести шифру Цезаря в редакції умови задачі."""

from __future__ import annotations

import random
import string

import pytest

from freqcrack import ALPHABET, M, all_candidates, decrypt, encrypt, letter_counts, shift

SAMPLE = "Hello World ! 42 don't — ось так, ok?"


def test_example_from_statement() -> None:
    assert decrypt("Khoor Zruog !", 3) == "Hello World !"
    assert encrypt("Hello World !", 3) == "Khoor Zruog !"


def test_case_is_preserved() -> None:
    encoded = encrypt("AbCdE", 5)
    assert encoded == "FgHiJ"
    assert [c.isupper() for c in encoded] == [True, False, True, False, True]


@pytest.mark.parametrize("ch", list("0123456789 ,.!?-'’\n\t") + ["ї", "—"])
def test_non_letter_characters_are_untouched(ch: str) -> None:
    """Зсув застосовується лише до літер A..Z — решта символів без змін."""
    for k in range(M):
        assert encrypt(ch, k) == ch


def test_typographic_apostrophe_survives() -> None:
    """У п'ятому офіційному тесті трапляється символ U+2019."""
    text = "you’d expect"
    assert encrypt(text, 7).count("’") == 1
    assert decrypt(encrypt(text, 7), 7) == text


def test_roundtrip_property() -> None:
    rng = random.Random(2026)
    pool = string.ascii_letters + string.digits + " .,!?'-"
    for _ in range(500):
        text = "".join(rng.choice(pool) for _ in range(rng.randrange(1, 80)))
        k = rng.randrange(M)
        assert decrypt(encrypt(text, k), k) == text


def test_shift_is_modular() -> None:
    assert encrypt(SAMPLE, 3) == encrypt(SAMPLE, 29)
    assert encrypt(SAMPLE, 0) == SAMPLE
    assert encrypt(SAMPLE, -1) == encrypt(SAMPLE, 25)


def test_shifts_compose_additively() -> None:
    """Зсуви утворюють циклічну групу: E_a . E_b = E_{a+b}."""
    rng = random.Random(7)
    for _ in range(50):
        a, b = rng.randrange(M), rng.randrange(M)
        assert encrypt(encrypt(SAMPLE, a), b) == encrypt(SAMPLE, (a + b) % M)


def test_alphabet_is_permuted_bijectively() -> None:
    for k in range(M):
        assert sorted(encrypt(ALPHABET, k)) == list(ALPHABET)


def test_all_candidates_covers_key_space() -> None:
    cands = all_candidates("Khoor")
    assert len(cands) == M
    assert len({k for k, _ in cands}) == M
    assert ("Hello" in [t for _, t in cands])


def test_letter_counts_ignores_case_and_symbols() -> None:
    counts = letter_counts("aA bB! 123")
    assert counts[0] == 2 and counts[1] == 2
    assert sum(counts) == 4


def test_shift_of_empty_text() -> None:
    assert encrypt("", 5) == ""
    assert decrypt("", 5) == ""


def test_shift_helper_matches_encrypt() -> None:
    assert shift(SAMPLE, 9) == encrypt(SAMPLE, 9)
