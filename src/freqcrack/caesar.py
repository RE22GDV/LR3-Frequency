"""
Шифр Цезаря у тому вигляді, в якому він заданий умовою задачі.

    c[i] = m[i] + k (mod 26)  — тільки для літер;
    решта символів (цифри, розділові знаки, пробіли, апострофи)
    передається без змін, а регістр літер зберігається.

Термінологічне уточнення. В умові лабораторної роботи зсув названо
перестановкою. У строгій класифікації шифрів циклічний зсув є
ПІДСТАНОВКОЮ символів: він замінює кожну літеру іншою, але не
змінює їхніх позицій у повідомленні. Перестановний (транспозиційний)
шифр, навпаки, переставляє самі символи, не змінюючи їхнього складу
(Handbook of Applied Cryptography, § 1.5.2). Далі збережено
термінологію умови.
"""

from __future__ import annotations

from functools import lru_cache

#: Робочий алфавіт (обробляються обидва регістри).
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

#: Потужність алфавіту — модуль кільця Z_26.
M = 26

_UPPER = ALPHABET
_LOWER = ALPHABET.lower()


@lru_cache(maxsize=M)
def _table(k: int) -> dict:
    """
    Таблиця трансляції для зсуву ``k``.

    Використання ``str.translate`` замість посимвольного циклу дає
    лінійний прохід на рівні C і не потребує жодних умовних переходів
    для нелітерних символів — вони просто відсутні в таблиці.
    """
    k %= M
    src = _UPPER + _LOWER
    dst = _UPPER[k:] + _UPPER[:k] + _LOWER[k:] + _LOWER[:k]
    return str.maketrans(src, dst)


def shift(text: str, k: int) -> str:
    """Зсунути всі літери тексту на ``k`` позицій уперед за модулем 26."""
    return text.translate(_table(k % M))


def encrypt(plaintext: str, key: int) -> str:
    """Зашифрувати: ``c = m + k``."""
    return shift(plaintext, key)


def decrypt(ciphertext: str, key: int) -> str:
    """Розшифрувати: ``m = c - k``."""
    return shift(ciphertext, -key)


def all_candidates(ciphertext: str) -> list[tuple[int, str]]:
    """Усі 26 можливих розшифрувань — повний простір ключів шифру."""
    return [(k, decrypt(ciphertext, k)) for k in range(M)]


def letters_only(text: str, *, upper: bool = True) -> str:
    """Лише літери A..Z (за потреби — у верхньому регістрі)."""
    out = [ch for ch in text if ch.isascii() and ch.isalpha()]
    s = "".join(out)
    return s.upper() if upper else s


def letter_counts(text: str) -> list[int]:
    """Абсолютні частоти 26 літер без урахування регістру."""
    counts = [0] * M
    for ch in text:
        if "A" <= ch <= "Z":
            counts[ord(ch) - 65] += 1
        elif "a" <= ch <= "z":
            counts[ord(ch) - 97] += 1
    return counts
