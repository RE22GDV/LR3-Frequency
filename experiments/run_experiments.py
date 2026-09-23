"""
Обчислювальні експерименти лабораторної роботи.

    python experiments/run_experiments.py            # усі експерименти
    python experiments/run_experiments.py --quick    # скорочений прогін

Результати:
    docs/results/experiments.json   — усі виміряні величини
    docs/results/summary.md         — зведена таблиця для звіту
    docs/figures/*.png              — рисунки (+ pdf/ — версії без заголовків)

Усі генератори випадкових чисел ініціалізуються фіксованим зерном,
тому результати відтворювані.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import PercentFormatter  # noqa: E402

from freqcrack import (  # noqa: E402
    ALPHABET,
    M,
    PUZZLE_FREQ,
    break_caesar,
    chi_squared,
    compare_tables,
    decrypt,
    encrypt,
    index_of_coincidence,
    keyspace_bits,
    letter_frequencies,
    most_frequent_rule,
    shannon_entropy,
    unicity_distance,
)
from freqcrack.ngrams import default_scorer  # noqa: E402

# --------------------------------------------------------------------------- #
#  Оформлення рисунків
#  Палітра — перші три категорійні слоти референсної системи (blue/orange/aqua):
#  саме ця трійка проходить перевірку all-pairs за колірним зором.
# --------------------------------------------------------------------------- #

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e3e2de"
S1 = "#2a78d6"   # слот 1 — синій
S2 = "#eb6834"   # слот 2 — помаранчевий
S3 = "#1baf7a"   # слот 3 — бірюзовий

plt.rcParams.update({
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID,
    "axes.labelcolor": INK_2,
    "axes.titlecolor": INK,
    "axes.titlesize": 12,
    "axes.titleweight": "semibold",
    "axes.labelsize": 9.5,
    "axes.grid": True,
    "axes.axisbelow": True,
    "grid.color": GRID,
    "grid.linewidth": 0.8,
    "xtick.color": INK_2,
    "ytick.color": INK_2,
    "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5,
    "legend.frameon": False,
    "legend.fontsize": 9,
    "lines.linewidth": 2.0,
    "font.size": 10,
})

FIG = ROOT / "docs" / "figures"
RES = ROOT / "docs" / "results"

METHOD_LABELS = {
    "chi2": "хі-квадрат",
    "quadgram": "квадриграми",
    "unigram": "частоти літер",
    "mostfreq": "найчастіша → E",
}
METHOD_COLORS = {"chi2": S1, "quadgram": S2, "unigram": S3, "mostfreq": INK_2}


def _n(value: float, digits: int = 2) -> str:
    """Число з комою як десятковим роздільником (для підписів на рисунках)."""
    return ("%.*f" % (digits, value)).replace(".", ",")


def _finish(ax, note: str | None = None) -> None:
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    if note:
        ax.text(0.995, -0.17, note, transform=ax.transAxes, ha="right", va="top",
                fontsize=7.5, color=INK_2)


def save(fig, name: str) -> str:
    """
    Зберігає рисунок двічі:
      docs/figures/<name>      — із заголовком, для README на GitHub;
      docs/figures/pdf/<name>  — без заголовка, для звіту, де роль заголовка
                                 виконує підпис «Рисунок N.M – ...».
    """
    FIG.mkdir(parents=True, exist_ok=True)
    path = FIG / name
    fig.savefig(path, dpi=200, bbox_inches="tight")

    (FIG / "pdf").mkdir(parents=True, exist_ok=True)
    for ax in fig.axes:
        ax.set_title("")
    if fig._suptitle is not None:
        fig.suptitle("")
    fig.savefig(FIG / "pdf" / name, dpi=200, bbox_inches="tight")

    plt.close(fig)
    print("    рисунок -> %s (+ pdf/)" % path.relative_to(ROOT))
    return str(path.relative_to(ROOT)).replace("\\", "/")


# --------------------------------------------------------------------------- #

def load_corpus() -> str:
    """Англомовний корпус для експериментів (текст суспільного надбання)."""
    raw = (ROOT / "data" / "sample_plaintext.txt").read_text(encoding="utf-8")
    return " ".join(raw.split())


def sample_of(text: str, length: int, rng: random.Random) -> str:
    doubled = text + " " + text
    start = rng.randrange(len(text))
    return doubled[start:start + length]


# --------------------------------------------------------------------------- #
#  Експеримент 1 — що робить зсув із гістограмою частот
# --------------------------------------------------------------------------- #

def exp_histogram(corpus: str) -> dict:
    print("[1] Частотний профіль відкритого тексту та шифротексту")
    key = 3
    ciphertext = encrypt(corpus, key)

    pt = letter_frequencies(corpus)
    ct = letter_frequencies(ciphertext)
    ref = [PUZZLE_FREQ[c] for c in ALPHABET]

    fig, ax = plt.subplots(figsize=(10, 4.2))
    x = range(M)
    w = 0.38
    ax.bar([i - w / 2 for i in x], pt, width=w - 0.04, color=S1,
           label="відкритий текст", zorder=3)
    ax.bar([i + w / 2 for i in x], ct, width=w - 0.04, color=S2,
           label="шифротекст (зсув %d)" % key, zorder=3)
    ax.plot(list(x), ref, color=INK_2, linewidth=1.4, linestyle=(0, (4, 3)),
            marker="o", markersize=3.2, label="таблиця з умови задачі", zorder=4)

    ax.set_xticks(list(x))
    ax.set_xticklabels(list(ALPHABET))
    ax.set_ylabel("частота, %")
    ax.set_ylim(0, max(max(pt), max(ct), max(ref)) * 1.34)
    ax.set_title("Рис. 1. Зсув не приховує статистику, а лише зсуває гістограму")
    ax.legend(loc="upper right", ncols=3)
    _finish(ax, "IoC: відкритий %s, шифротекст %s (величина не змінюється)"
            % (_n(index_of_coincidence(corpus), 4),
               _n(index_of_coincidence(ciphertext), 4)))
    path = save(fig, "fig1_histogram.png")

    peak_pt = max(range(M), key=lambda i: pt[i])
    peak_ct = max(range(M), key=lambda i: ct[i])
    return {
        "figure": path,
        "key": key,
        "plaintext_ioc": index_of_coincidence(corpus),
        "ciphertext_ioc": index_of_coincidence(ciphertext),
        "plaintext_entropy": shannon_entropy(corpus),
        "ciphertext_entropy": shannon_entropy(ciphertext),
        "peak_letter_plaintext": ALPHABET[peak_pt],
        "peak_letter_ciphertext": ALPHABET[peak_ct],
        "peak_shift_equals_key": (peak_ct - peak_pt) % M == key,
        "chi2_plaintext": chi_squared(corpus),
        "chi2_ciphertext": chi_squared(ciphertext),
    }


# --------------------------------------------------------------------------- #
#  Експеримент 2 — хі-квадрат по всіх 26 ключах
# --------------------------------------------------------------------------- #

def exp_chi_profile(corpus: str) -> dict:
    print("[2] Профіль хі-квадрат по 26 кандидатах")
    key = 11
    text = corpus[:400]
    ciphertext = encrypt(text, key)
    scores = [chi_squared(decrypt(ciphertext, k)) for k in range(M)]
    result = break_caesar(ciphertext, "chi2")

    colors = [S2 if k == key else S1 for k in range(M)]
    fig, ax = plt.subplots(figsize=(9.5, 4.0))
    ax.bar(range(M), scores, color=colors, width=0.68, zorder=3)
    ax.set_xticks(range(M))
    ax.set_xlabel("припущений ключ k")
    ax.set_ylabel("хі-квадрат (менше — краще)")
    ax.set_title("Рис. 2. Правильний ключ дає різкий мінімум хі-квадрат")
    ax.annotate("k = %d" % key, xy=(key, scores[key]),
                xytext=(key + 1.4, scores[key] + 0.22 * max(scores)),
                fontsize=9.5, color=INK,
                arrowprops=dict(arrowstyle="-", color=S2, linewidth=1.4))
    handles = [plt.Rectangle((0, 0), 1, 1, color=S1),
               plt.Rectangle((0, 0), 1, 1, color=S2)]
    ax.legend(handles, ["хибні кандидати", "правильний ключ"], loc="upper right")
    _finish(ax, "текст %d символів; відрив від другого кандидата — %s; час %s мс"
            % (len(text), _n(result.margin, 0), _n(result.elapsed_s * 1000, 2)))
    path = save(fig, "fig2_chi_profile.png")

    ordered = sorted(scores)
    return {
        "figure": path,
        "true_key": key,
        "recovered_key": result.key,
        "text_length": len(text),
        "margin": result.margin,
        "ratio_second_to_best": ordered[1] / ordered[0] if ordered[0] else math.inf,
        "elapsed_ms": result.elapsed_s * 1000,
    }


# --------------------------------------------------------------------------- #
#  Експеримент 3 — IoC інваріантний, хі-квадрат — ні
# --------------------------------------------------------------------------- #

def exp_invariance(corpus: str) -> dict:
    print("[3] Інваріантність IoC проти чутливості хі-квадрат")
    text = corpus[:600]
    iocs = [index_of_coincidence(encrypt(text, k)) for k in range(M)]
    chis = [chi_squared(encrypt(text, k)) for k in range(M)]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 3.8))
    ax1.plot(range(M), iocs, color=S1, marker="o", markersize=4,
             markerfacecolor=SURFACE, markeredgewidth=1.5, zorder=3)
    ax1.set_xlabel("застосований зсув k")
    ax1.set_ylabel("індекс відповідності")
    ax1.set_title("IoC: не залежить від зсуву")
    ax1.set_ylim(min(iocs) - 0.01, max(iocs) + 0.01)
    _finish(ax1)

    ax2.plot(range(M), chis, color=S2, marker="o", markersize=4,
             markerfacecolor=SURFACE, markeredgewidth=1.5, zorder=3)
    ax2.set_xlabel("застосований зсув k")
    ax2.set_ylabel("хі-квадрат")
    ax2.set_title("Хі-квадрат: залежить")
    _finish(ax2)

    fig.suptitle("Рис. 3. Чому ключ дає саме хі-квадрат, а не індекс відповідності",
                 fontsize=12, fontweight="semibold", color=INK)
    fig.tight_layout()
    path = save(fig, "fig3_invariance.png")

    return {
        "figure": path,
        "text_length": len(text),
        "ioc_spread": max(iocs) - min(iocs),
        "ioc_value": iocs[0],
        "chi2_min": min(chis),
        "chi2_max": max(chis),
        "chi2_spread_ratio": max(chis) / min(chis) if min(chis) else math.inf,
    }


# --------------------------------------------------------------------------- #
#  Експеримент 4 — успішність правил рішення залежно від довжини
# --------------------------------------------------------------------------- #

def exp_success_vs_length(corpus: str, quick: bool) -> dict:
    print("[4] Успішність правил рішення залежно від довжини повідомлення")
    lengths = [5, 10, 15, 20, 30, 40, 60, 80, 120, 200] if not quick else [10, 40, 120]
    trials = 200 if not quick else 40
    methods = ("chi2", "quadgram", "unigram", "mostfreq")

    rng = random.Random(20260923)
    success = {m: [] for m in methods}
    timing = {m: [] for m in methods}

    for length in lengths:
        hits = {m: 0 for m in methods}
        times = {m: [] for m in methods}
        for _ in range(trials):
            plain = sample_of(corpus, length, rng)
            key = rng.randrange(M)
            ct = encrypt(plain, key)
            for m in methods:
                r = break_caesar(ct, m)
                hits[m] += (r.key == key)
                times[m].append(r.elapsed_s)
        for m in methods:
            success[m].append(100.0 * hits[m] / trials)
            timing[m].append(statistics.mean(times[m]) * 1000)
        print("    L=%3d  " % length + "  ".join(
            "%s %5.1f%%" % (METHOD_LABELS[m], success[m][-1]) for m in methods))

    fig, ax = plt.subplots(figsize=(9.2, 4.3))
    markers = {"chi2": "o", "quadgram": "s", "unigram": "^", "mostfreq": "D"}
    for m in methods:
        ax.plot(lengths, success[m], color=METHOD_COLORS[m], marker=markers[m],
                markersize=6.5, markerfacecolor=SURFACE, markeredgewidth=1.8,
                label=METHOD_LABELS[m], zorder=3)
    # Підписуємо лише крайні криві: решта збігаються на 100 %% і підписи
    # накладалися б одна на одну.
    for m in ("chi2", "mostfreq"):
        ax.annotate("%s%%" % _n(success[m][-1], 0), xy=(lengths[-1], success[m][-1]),
                    xytext=(7, 0), textcoords="offset points", va="center",
                    fontsize=8.5, color=METHOD_COLORS[m])

    ax.set_xlabel("довжина повідомлення, символів")
    ax.set_ylabel("частка правильно знайдених ключів")
    ax.yaxis.set_major_formatter(PercentFormatter())
    ax.set_ylim(-4, 108)
    ax.set_xlim(0, lengths[-1] * 1.12)
    ax.axvspan(67, lengths[-1] * 1.12, color=S3, alpha=0.10, zorder=1)
    ax.text((67 + lengths[-1] * 1.12) / 2, 104, "діапазон CodinGame (L ≥ 67)",
            ha="center", va="center", fontsize=8, color=INK_2)
    ax.set_title("Рис. 4. Скільки тексту потрібно різним правилам рішення")
    ax.legend(loc="lower right", ncols=2)
    _finish(ax, "по %d випробувань на точку; ключ щоразу випадковий" % trials)
    path = save(fig, "fig4_success.png")

    def first_full(m: str) -> int | None:
        for length, value in zip(lengths, success[m]):
            if value >= 100.0:
                return length
        return None

    return {
        "figure": path,
        "lengths": lengths,
        "trials_per_point": trials,
        "success_percent": success,
        "mean_time_ms": timing,
        "first_length_at_100_percent": {m: first_full(m) for m in methods},
    }


# --------------------------------------------------------------------------- #
#  Експеримент 5 — чому помиляється наївне правило
# --------------------------------------------------------------------------- #

def exp_naive_error(corpus: str, quick: bool) -> dict:
    print("[5] Структура помилки наївного правила")
    length = 40
    trials = 2000 if not quick else 300
    rng = random.Random(4242)

    errors = [0] * M
    top_letters: dict[str, int] = {}
    for _ in range(trials):
        plain = sample_of(corpus, length, rng)
        key = rng.randrange(M)
        guess = most_frequent_rule(encrypt(plain, key))
        errors[(guess - key) % M] += 1
        counts = [plain.upper().count(ch) for ch in ALPHABET]
        top = ALPHABET[max(range(M), key=lambda i: counts[i])]
        top_letters[top] = top_letters.get(top, 0) + 1

    shifts = list(range(-12, 14))
    values = [100.0 * errors[k % M] / trials for k in shifts]
    colors = [S2 if k == 0 else S1 for k in shifts]

    fig, ax = plt.subplots(figsize=(9.5, 3.9))
    ax.bar(shifts, values, color=colors, width=0.7, zorder=3)
    ax.set_xlabel("похибка визначення ключа (припущений − справжній), mod 26")
    ax.set_ylabel("частка випробувань, %")
    ax.set_xticks(range(-12, 14, 2))
    ax.set_title("Рис. 5. Наївне правило помиляється систематично, а не випадково")
    correct = values[shifts.index(0)]
    ax.annotate("точне влучання: %s %%" % _n(correct, 1), xy=(0, correct),
                xytext=(2.0, correct + 4), fontsize=9.5, color=INK,
                arrowprops=dict(arrowstyle="-", color=S2, linewidth=1.4))
    _finish(ax, "повідомлення по %d символів, %d випробувань; "
                "похибка дорівнює зсуву найчастішої літери тексту відносно E"
            % (length, trials))
    path = save(fig, "fig5_naive_error.png")

    top_sorted = sorted(top_letters.items(), key=lambda kv: -kv[1])[:5]
    return {
        "figure": path,
        "length": length,
        "trials": trials,
        "accuracy_percent": correct,
        "error_distribution_percent": {str(k): values[shifts.index(k)] for k in shifts},
        "top_plaintext_letters": [(ch, 100.0 * n / trials) for ch, n in top_sorted],
    }


# --------------------------------------------------------------------------- #
#  Експеримент 6 — шифр без статистичних закономірностей
# --------------------------------------------------------------------------- #

def exp_flat_cipher(corpus: str) -> dict:
    print("[6] Порівняння з шифром, що не лишає статистичних слідів")
    text = corpus[:600]
    rng = random.Random(77)

    caesar_ct = encrypt(text, 9)
    # Одноразовий блокнот над Z_26: для кожної позиції — власний випадковий зсув.
    otp_ct = "".join(
        encrypt(ch, rng.randrange(M)) if ch.isascii() and ch.isalpha() else ch
        for ch in text
    )

    caesar_chi = [chi_squared(decrypt(caesar_ct, k)) for k in range(M)]
    otp_chi = [chi_squared(decrypt(otp_ct, k)) for k in range(M)]

    fig, ax = plt.subplots(figsize=(9.5, 4.0))
    ax.plot(range(M), caesar_chi, color=S1, marker="o", markersize=5,
            markerfacecolor=SURFACE, markeredgewidth=1.6,
            label="шифр Цезаря (один зсув)", zorder=4)
    ax.plot(range(M), otp_chi, color=S2, marker="s", markersize=5,
            markerfacecolor=SURFACE, markeredgewidth=1.6,
            label="випадковий зсув на кожну позицію", zorder=3)
    ax.set_xlabel("припущений ключ k")
    ax.set_ylabel("хі-квадрат")
    ax.set_xticks(range(0, M, 2))
    ax.set_title("Рис. 6. Частотна атака працює лише тоді, коли шифр лишає слід")
    ax.legend(loc="upper right")
    _finish(ax, "той самий відкритий текст, %d символів" % len(text))
    path = save(fig, "fig6_flat_cipher.png")

    return {
        "figure": path,
        "text_length": len(text),
        "caesar_min": min(caesar_chi),
        "caesar_max": max(caesar_chi),
        "caesar_contrast": max(caesar_chi) / min(caesar_chi),
        "otp_min": min(otp_chi),
        "otp_max": max(otp_chi),
        "otp_contrast": max(otp_chi) / min(otp_chi),
        "caesar_ioc": index_of_coincidence(caesar_ct),
        "otp_ioc": index_of_coincidence(otp_ct),
    }


# --------------------------------------------------------------------------- #
#  Зведена таблиця
# --------------------------------------------------------------------------- #

def write_summary(results: dict) -> None:
    RES.mkdir(parents=True, exist_ok=True)
    (RES / "experiments.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    sv = results["success_vs_length"]
    lines = [
        "# Зведені результати експериментів",
        "",
        "Згенеровано автоматично: `python experiments/run_experiments.py`",
        "",
        "## Простір ключів",
        "",
        "| Величина | Значення |",
        "|---|---:|",
        "| Кількість ключів | 26 |",
        "| Ентропія ключа, біт | %.4f |" % results["keyspace"]["bits"],
        "| Відстань єдиності (h = 1.5 біта/символ), символів | %.1f |"
        % results["keyspace"]["unicity_distance"],
        "",
        "## Частка правильно знайдених ключів, %",
        "",
        "| Правило рішення | " + " | ".join(str(x) for x in sv["lengths"]) + " |",
        "|---|" + "---:|" * len(sv["lengths"]),
    ]
    for m, values in sv["success_percent"].items():
        lines.append("| %s | " % m + " | ".join("%.1f" % v for v in values) + " |")
    lines += [
        "",
        "Довжини — у символах, по %d випробувань на точку." % sv["trials_per_point"],
        "",
    ]
    (RES / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n    зведення -> docs/results/summary.md")
    print("    сирі дані -> docs/results/experiments.json")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="скорочений прогін")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    t0 = time.perf_counter()
    corpus = load_corpus()
    print("Корпус для експериментів: %d символів\n" % len(corpus))

    results = {
        "meta": {
            "corpus_chars": len(corpus),
            "language_model": default_scorer().source,
            "quick": args.quick,
        },
        "keyspace": {
            "keys": M,
            "bits": keyspace_bits(),
            "unicity_distance": unicity_distance(keyspace_bits()),
        },
        "tables": compare_tables(),
        "histogram": exp_histogram(corpus),
        "chi_profile": exp_chi_profile(corpus),
        "invariance": exp_invariance(corpus),
        "success_vs_length": exp_success_vs_length(corpus, args.quick),
        "naive_error": exp_naive_error(corpus, args.quick),
        "flat_cipher": exp_flat_cipher(corpus),
    }
    results["meta"]["total_seconds"] = time.perf_counter() - t0
    write_summary(results)
    print("\nГотово за %.1f с" % results["meta"]["total_seconds"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
