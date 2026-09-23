"""
Командний інтерфейс лабораторної роботи.

    python run.py solve < tests/samples/case1.txt   # режим CodinGame
    python run.py break --text "<шифротекст>"       # злам без ключа
    python run.py encrypt --key 3 --text "Hello"
    python run.py decrypt --key 3 --text "Khoor"
    python run.py analyze --text "<текст>"          # частоти, IoC, ентропія
    python run.py compare --text "<шифротекст>"     # усі 4 правила рішення
    python run.py tables                            # порівняння таблиць частот
    python run.py selftest                          # офіційні тести CodinGame
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

from .breaker import METHODS, break_all_methods, break_caesar, keyspace_bits
from .caesar import ALPHABET, M, decrypt, encrypt
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
    shannon_entropy,
    unicity_distance,
)

ROOT = Path(__file__).resolve().parents[2]


def _utf8_stdout() -> None:
    """Щоб кирилиця коректно друкувалася в консолі Windows."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def _text(args: argparse.Namespace) -> str:
    return args.text if args.text is not None else sys.stdin.read().rstrip("\n")


def _bar(value: float, scale: float, width: int = 24) -> str:
    n = int(round(width * min(value / scale, 1.0))) if scale > 0 else 0
    return "#" * n


# --------------------------------------------------------------------------- #

def cmd_solve(args: argparse.Namespace) -> int:
    """Режим CodinGame: один рядок зі stdin, один рядок у stdout."""
    message = sys.stdin.readline().rstrip("\n")
    print(break_caesar(message, "chi2").plaintext)
    return 0


def cmd_encrypt(args: argparse.Namespace) -> int:
    print(encrypt(_text(args), args.key))
    return 0


def cmd_decrypt(args: argparse.Namespace) -> int:
    print(decrypt(_text(args), args.key))
    return 0


def cmd_break(args: argparse.Namespace) -> int:
    result = break_caesar(_text(args), args.method)
    print("Правило рішення : %s" % result.method)
    print("Знайдений ключ  : %d" % result.key)
    print("Відрив від 2-го : %.2f" % result.margin)
    print("Час             : %.3f мс" % (result.elapsed_s * 1000))
    print("\n%s" % result.plaintext)
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    text = _text(args)
    results = break_all_methods(text)
    print("Порівняння правил рішення на одному шифротексті")
    print("-" * 78)
    print("%-10s %6s %12s %10s  %s" % ("правило", "ключ", "відрив", "час, мс", "початок тексту"))
    for name in METHODS:
        r = results[name]
        print("%-10s %6d %12.2f %10.3f  %s"
              % (r.method, r.key, r.margin, r.elapsed_s * 1000, r.plaintext[:34]))
    keys = {r.key for r in results.values()}
    print("-" * 78)
    print("Усі правила дали однаковий ключ: %s" % ("так" if len(keys) == 1 else "НІ"))
    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    text = _text(args)
    if not text.strip():
        print("порожній текст", file=sys.stderr)
        return 2

    ioc = index_of_coincidence(text)
    print("Довжина, символів   : %d" % len(text))
    print("З них літер         : %d" % sum(1 for c in text if c.isascii() and c.isalpha()))
    print("Індекс відповідності: %.5f  (англ. %.4f, випадк. %.4f)"
          % (ioc, IOC_ENGLISH, IOC_RANDOM))
    print("Хі-квадрат до таблиці з умови: %.1f" % chi_squared(text))
    print("Ентропія за літерами: %.4f біт/символ (макс. %.4f)"
          % (shannon_entropy(text), 4.7004))
    print()
    print("Частоти літер (спостережувано проти таблиці з умови):")
    freqs = letter_frequencies(text)
    for i, letter in enumerate(ALPHABET):
        print("  %s %5.2f%% %-24s | умова %5.2f%% %s"
              % (letter, freqs[i], _bar(freqs[i], 13.0),
                 PUZZLE_FREQ[letter], _bar(PUZZLE_FREQ[letter], 13.0)))
    print()
    print("Індекс відповідності НЕ змінюється при зсуві, тому він показує тип")
    print("шифру (моноалфавітний), але не дає ключа. Ключ визначає хі-квадрат.")
    return 0


def cmd_tables(args: argparse.Namespace) -> int:
    cmp = compare_tables()
    print("Порівняння таблиць частот")
    print("-" * 60)
    print("Сума частот, умова задачі      : %.2f %%" % cmp["total_a"])
    print("Сума частот, Beker & Piper     : %.2f %%" % cmp["total_b"])
    print("Максимальне відхилення         : %.2f в. п." % cmp["max_abs_diff_pp"])
    print("Середнє відхилення             : %.3f в. п." % cmp["mean_abs_diff_pp"])
    print("Найчастіша літера збігається   : %s"
          % ("так" if cmp["argmax_letter_matches"] else "ні"))
    print("Однаковий початок упорядкування: %d літер"
          % int(cmp["identical_order_prefix"]))
    print()
    print("%-8s %8s %8s %8s" % ("літера", "умова", "B&P", "різниця"))
    for ch in ALPHABET:
        a, b = PUZZLE_FREQ[ch], BEKER_PIPER_FREQ[ch]
        print("%-8s %7.2f%% %7.3f%% %+8.3f" % (ch, a, b, a - b))
    return 0


def cmd_keyspace(args: argparse.Namespace) -> int:
    bits = keyspace_bits()
    print("Простір ключів шифру Цезаря")
    print("-" * 60)
    print("Кількість ключів     : %d" % M)
    print("Ентропія ключа       : %.4f біта" % bits)
    print("Відстань єдиності    : %.1f символу (за h ≈ 1,5 біта на символ)"
          % unicity_distance(bits))
    print()
    print("Відстань єдиності — оцінка в прийнятій моделі мови, а не жорстка")
    print("межа: вона не гарантує ні неможливості зламу коротших повідомлень,")
    print("ні успіху конкретного алгоритму на довших.")
    return 0


def cmd_selftest(args: argparse.Namespace) -> int:
    cases = json.loads((ROOT / "tests" / "official_cases.json").read_text(
        encoding="utf-8"))["cases"]
    passed = 0
    print("Офіційні тести CodinGame")
    print("-" * 78)
    for case in cases:
        result = break_caesar(case["input"], "chi2")
        ok = result.plaintext == case["expected"]
        passed += ok
        print("[%s] %-7s ключ %2d (істина %2d)  %s"
              % ("OK" if ok else "FAIL", case["label"], result.key, case["shift"],
                 result.plaintext[:44]))
    print("-" * 78)
    print("Пройдено %d з %d" % (passed, len(cases)))
    return 0 if passed == len(cases) else 1


# --------------------------------------------------------------------------- #

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="freqcrack",
        description="Лабораторна робота №3: злам шифру Цезаря частотним аналізом.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    def with_text(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--text", default=None, help="текст (типово — зі stdin)")

    sp = sub.add_parser("solve", help="режим CodinGame: рядок зі stdin")
    sp.set_defaults(func=cmd_solve)

    sp = sub.add_parser("break", help="зламати шифротекст без ключа")
    with_text(sp)
    sp.add_argument("--method", choices=METHODS, default="chi2")
    sp.set_defaults(func=cmd_break)

    sp = sub.add_parser("compare", help="порівняти всі правила рішення")
    with_text(sp)
    sp.set_defaults(func=cmd_compare)

    sp = sub.add_parser("encrypt", help="зашифрувати з відомим ключем")
    with_text(sp)
    sp.add_argument("--key", type=int, required=True)
    sp.set_defaults(func=cmd_encrypt)

    sp = sub.add_parser("decrypt", help="розшифрувати з відомим ключем")
    with_text(sp)
    sp.add_argument("--key", type=int, required=True)
    sp.set_defaults(func=cmd_decrypt)

    sp = sub.add_parser("analyze", help="статистичний аналіз тексту")
    with_text(sp)
    sp.set_defaults(func=cmd_analyze)

    sp = sub.add_parser("tables", help="порівняння таблиць частот")
    sp.set_defaults(func=cmd_tables)

    sp = sub.add_parser("keyspace", help="простір ключів і відстань єдиності")
    sp.set_defaults(func=cmd_keyspace)

    sp = sub.add_parser("selftest", help="прогін офіційних тестів CodinGame")
    sp.set_defaults(func=cmd_selftest)
    return p


def main(argv: list[str] | None = None) -> int:
    _utf8_stdout()
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
