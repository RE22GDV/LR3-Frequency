"""
Пакет `freqcrack` — злам шифру Цезаря частотним аналізом
(задача CodinGame "Frequency-Based Decryption").

Лабораторна робота №3 з дисципліни «Захист даних».
"""

from .breaker import METHODS, BreakResult, break_all_methods, break_caesar, keyspace_bits
from .caesar import (
    ALPHABET,
    M,
    all_candidates,
    decrypt,
    encrypt,
    letter_counts,
    letters_only,
    shift,
)
from .frequencies import (
    BEKER_PIPER_FREQ,
    IOC_ENGLISH,
    IOC_RANDOM,
    PUZZLE_FREQ,
    compare_tables,
)
from .scoring import (
    chi_squared,
    index_of_coincidence,
    letter_frequencies,
    most_frequent_rule,
    shannon_entropy,
    unicity_distance,
    unigram_score,
)

__all__ = [
    "ALPHABET", "M",
    "shift", "encrypt", "decrypt", "all_candidates", "letters_only", "letter_counts",
    "PUZZLE_FREQ", "BEKER_PIPER_FREQ", "IOC_ENGLISH", "IOC_RANDOM", "compare_tables",
    "chi_squared", "unigram_score", "most_frequent_rule", "index_of_coincidence",
    "shannon_entropy", "letter_frequencies", "unicity_distance",
    "break_caesar", "break_all_methods", "BreakResult", "METHODS", "keyspace_bits",
]

__version__ = "1.0.0"
