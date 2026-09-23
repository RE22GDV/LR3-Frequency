"""
Метрики, за якими кандидат-розшифрування оцінюється на «англійськість».

Реалізовано чотири правила рішення — саме їх порівнює експеримент:

  * :func:`chi_squared`      — критерій хі-квадрат до таблиці частот (менше — краще);
  * :func:`unigram_score`    — логарифмічна правдоподібність за частотами літер;
  * :func:`quadgram_score`   — логарифмічна правдоподібність за квадриграмами;
  * :func:`most_frequent_rule` — наївне правило «найчастіша літера шифротексту → E».

Окремо наведено :func:`index_of_coincidence`. Ця метрика має протилежні
властивості: вона ІНВАРІАНТНА щодо зсуву Цезаря, тому не містить
інформації про конкретне значення ключа. Водночас вона лишається
статистичною характеристикою розподілу символів і використовується в
криптоаналізі як допоміжний показник.
"""

from __future__ import annotations

import math
from collections import Counter

from .caesar import ALPHABET, M, letter_counts
from .frequencies import PUZZLE_FREQ, as_vector


# --------------------------------------------------------------------------- #
#  Критерій хі-квадрат
# --------------------------------------------------------------------------- #

def chi_squared(text: str, table: dict[str, float] | None = None) -> float:
    """
    Статистика хі-квадрат між спостережуваними частотами літер тексту
    й еталонною таблицею. Менше значення — текст ближчий до англійської.

    Еталон — саме таблиця частот, а не рівномірний розподіл.
    """
    counts = letter_counts(text)
    n = sum(counts)
    if n == 0:
        return float("inf")
    ref = as_vector(table or PUZZLE_FREQ)
    total = 0.0
    for observed, percent in zip(counts, ref):
        expected = n * percent / 100.0
        if expected <= 0.0:
            expected = 1e-9
        total += (observed - expected) ** 2 / expected
    return total


# --------------------------------------------------------------------------- #
#  Логарифмічна правдоподібність за частотами літер
# --------------------------------------------------------------------------- #

def unigram_score(text: str, table: dict[str, float] | None = None) -> float:
    """Сума ``log10 P(літера)``; більше — краще."""
    counts = letter_counts(text)
    if sum(counts) == 0:
        return -math.inf
    ref = as_vector(table or PUZZLE_FREQ, fraction=True)
    total = 0.0
    for observed, probability in zip(counts, ref):
        if observed:
            total += observed * math.log10(max(probability, 1e-6))
    return total


# --------------------------------------------------------------------------- #
#  Наївне правило
# --------------------------------------------------------------------------- #

def most_frequent_rule(ciphertext: str, target: str = "E") -> int:
    """
    Найпростіше правило частотного аналізу: припускаємо, що найчастіша
    літера шифротексту відповідає найчастішій літері мови (звичайно E).

    Повертає припущений ключ. Правило не використовує жодної інформації,
    крім однієї літери, тому й помиляється помітно частіше за хі-квадрат —
    див. експеримент у розділі «Порівняння правил рішення».

    Якщо максимум гістограми досягається на кількох літерах, нічия
    розв'язується на користь меншого індексу. Циклічний зсув такого вибору
    не зберігає, тому на коротких текстах, де нічиї часті, похибка правила
    перестає бути строго передбачуваною.
    """
    counts = letter_counts(ciphertext)
    if sum(counts) == 0:
        return 0
    top = max(range(M), key=lambda i: counts[i])
    return (top - (ord(target) - 65)) % M


# --------------------------------------------------------------------------- #
#  Індекс відповідності
# --------------------------------------------------------------------------- #

def index_of_coincidence(text: str) -> float:
    """
    Ймовірність того, що дві навмання взяті літери тексту збігаються.

    Для англійської мови ~0.0667, для рівномірно випадкової
    послідовності ~0.0385. Величина не змінюється при будь-якому зсуві
    (і взагалі при будь-якій моноалфавітній заміні), тому вона показує
    ТИП шифру, але не його ключ.
    """
    counts = letter_counts(text)
    n = sum(counts)
    if n < 2:
        return 0.0
    return sum(c * (c - 1) for c in counts) / (n * (n - 1))


def shannon_entropy(text: str) -> float:
    """Ентропія Шеннона за окремими літерами, біт/символ (максимум log2 26)."""
    counts = letter_counts(text)
    n = sum(counts)
    if n == 0:
        return 0.0
    h = 0.0
    for c in counts:
        if c:
            p = c / n
            h -= p * math.log2(p)
    return h


def letter_frequencies(text: str, *, percent: bool = True) -> list[float]:
    """Спостережувані частоти 26 літер."""
    counts = letter_counts(text)
    n = sum(counts)
    if n == 0:
        return [0.0] * M
    scale = 100.0 / n if percent else 1.0 / n
    return [c * scale for c in counts]


def bigram_counts(text: str) -> Counter:
    """Лічильник біграм лише за літерами (для додаткової діагностики)."""
    letters = [ch.upper() for ch in text if ch.isascii() and ch.isalpha()]
    return Counter("".join(letters[i:i + 2]) for i in range(len(letters) - 1))


def unicity_distance(key_bits: float, entropy_per_char: float = 1.5) -> float:
    """
    Орієнтовна відстань єдиності за Шенноном: ``U = H(K) / D``, де
    ``D = log2(26) − h`` — надлишковість мови на символ.

    Це оцінка в прийнятій моделі мови, а не жорстка межа для кожного
    окремого повідомлення: вона не гарантує ні неможливості зламу
    коротших текстів, ні успіху конкретного алгоритму на довших.
    """
    redundancy = math.log2(M) - entropy_per_char
    if redundancy <= 0:
        return math.inf
    return key_bits / redundancy


def summary(text: str) -> dict[str, float]:
    """Зведений статистичний «паспорт» тексту."""
    return {
        "letters": float(sum(letter_counts(text))),
        "ioc": index_of_coincidence(text),
        "chi2": chi_squared(text),
        "entropy_bits_per_letter": shannon_entropy(text),
    }
