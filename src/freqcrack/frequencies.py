"""
Таблиці частот літер англійської мови.

У роботі використано дві таблиці:

* :data:`PUZZLE_FREQ` — таблиця, наведена безпосередньо в умові задачі
  CodinGame. Саме її вимагає завдання, і саме на ній працює надісланий
  розв'язок;
* :data:`BEKER_PIPER_FREQ` — класична таблиця (Beker & Piper, 1982),
  яку взято для перевірки того, наскільки результат залежить від вибору
  еталона.

Обидві таблиці нормовано у відсотках і вони не збігаються поточково:
див. :func:`compare_tables`.
"""

from __future__ import annotations

from .caesar import ALPHABET, M

#: Частоти літер, наведені в умові задачі CodinGame (у відсотках).
PUZZLE_FREQ: dict[str, float] = {
    "A": 8.08, "B": 1.67, "C": 3.18, "D": 3.99, "E": 12.56, "F": 2.17,
    "G": 1.80, "H": 5.27, "I": 7.24, "J": 0.14, "K": 0.63, "L": 4.04,
    "M": 2.60, "N": 7.38, "O": 7.47, "P": 1.91, "Q": 0.09, "R": 6.42,
    "S": 6.59, "T": 9.15, "U": 2.79, "V": 1.00, "W": 1.89, "X": 0.21,
    "Y": 1.65, "Z": 0.07,
}

#: Класична таблиця Beker & Piper (1982), у відсотках.
BEKER_PIPER_FREQ: dict[str, float] = {
    "A": 8.167, "B": 1.492, "C": 2.782, "D": 4.253, "E": 12.702, "F": 2.228,
    "G": 2.015, "H": 6.094, "I": 6.966, "J": 0.153, "K": 0.772, "L": 4.025,
    "M": 2.406, "N": 6.749, "O": 7.507, "P": 1.929, "Q": 0.095, "R": 5.987,
    "S": 6.327, "T": 9.056, "U": 2.758, "V": 0.978, "W": 2.360, "X": 0.150,
    "Y": 1.974, "Z": 0.074,
}

#: Очікуваний індекс відповідності для англійського тексту.
IOC_ENGLISH = 0.0667

#: Очікуваний індекс відповідності для рівномірно випадкової послідовності.
IOC_RANDOM = 1.0 / M


def as_vector(table: dict[str, float], *, fraction: bool = False) -> list[float]:
    """Таблиця у вигляді вектора з 26 чисел у порядку алфавіту."""
    scale = 0.01 if fraction else 1.0
    return [table[ch] * scale for ch in ALPHABET]


def total(table: dict[str, float]) -> float:
    """Сума частот — має бути близькою до 100 %."""
    return sum(table.values())


def most_frequent(table: dict[str, float]) -> str:
    """Найчастіша літера таблиці (для наївного правила «найчастіша → E»)."""
    return max(table, key=table.get)


def compare_tables(a: dict[str, float] | None = None,
                   b: dict[str, float] | None = None) -> dict[str, float]:
    """
    Порівняння двох таблиць частот: максимальне та середнє відхилення
    у відсоткових пунктах і збіг порядку найчастіших літер.
    """
    a = a or PUZZLE_FREQ
    b = b or BEKER_PIPER_FREQ
    diffs = {ch: abs(a[ch] - b[ch]) for ch in ALPHABET}
    order_a = sorted(ALPHABET, key=lambda ch: -a[ch])
    order_b = sorted(ALPHABET, key=lambda ch: -b[ch])
    same_prefix = 0
    for x, y in zip(order_a, order_b):
        if x != y:
            break
        same_prefix += 1
    return {
        "max_abs_diff_pp": max(diffs.values()),
        "mean_abs_diff_pp": sum(diffs.values()) / M,
        "argmax_letter_matches": float(order_a[0] == order_b[0]),
        "identical_order_prefix": float(same_prefix),
        "total_a": total(a),
        "total_b": total(b),
    }
