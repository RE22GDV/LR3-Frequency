"""
Прогін офіційних валідаційних тестів CodinGame.

Дані у ``tests/official_cases.json`` — це саме ті п'ять тестів, які
виконує валідатор платформи (входи та еталонні виходи).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from freqcrack import METHODS, break_caesar, encrypt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CASES = json.loads((HERE / "official_cases.json").read_text(encoding="utf-8"))["cases"]
IDS = [c["label"] for c in CASES]


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_fixture_is_self_consistent(case: dict) -> None:
    """
    Записаний у наборі тестових даних зсув має точно перетворювати очікуваний
    відкритий текст на збережений шифротекст. Це ловить будь-яку
    помилку переписування тестових даних.
    """
    assert encrypt(case["expected"], case["shift"]) == case["input"]


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_official_case(case: dict) -> None:
    result = break_caesar(case["input"], "chi2")
    assert result.key == case["shift"]
    assert result.plaintext == case["expected"]


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_standalone_codingame_script(case: dict) -> None:
    """Файл, який вставляється в редактор CodinGame, теж має проходити тести."""
    script = ROOT / "solution" / "codingame_solution.py"
    proc = subprocess.run(
        [sys.executable, str(script)],
        input=case["input"] + "\n", capture_output=True, text=True,
        encoding="utf-8", timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.rstrip("\n") == case["expected"]


@pytest.mark.parametrize("payload", ["12345 !!!", "", "   ", "----"])
def test_standalone_script_survives_input_without_letters(payload: str) -> None:
    """
    Умова задачі гарантує англійський текст, але програма не має падати
    на вході без жодної літери: хі-квадрат ділив би на нуль. Реалізація
    мовою C# таку перевірку мала від початку — тут вона її повторює.
    """
    script = ROOT / "solution" / "codingame_solution.py"
    proc = subprocess.run(
        [sys.executable, str(script)],
        input=payload + "\n", capture_output=True, text=True,
        encoding="utf-8", timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.rstrip("\n") == payload


def test_atypical_text_defeats_every_rule() -> None:
    """
    Довжина повідомлення сама по собі не гарантує успіху атаки: вирішує
    схожість розподілу літер на англійський. Текст із 80 символів, у якому
    лише три різні літери, не зламується жодним із чотирьох правил.
    """
    plaintext = "I did it. " * 8
    assert len(plaintext) == 80
    assert len({ch for ch in plaintext.upper() if ch.isalpha()}) == 3

    key = 3
    ciphertext = encrypt(plaintext, key)
    for method in METHODS:
        assert break_caesar(ciphertext, method).key != key, method


def test_message_lengths_match_the_constraints() -> None:
    """Умова задачі: 67 <= довжина повідомлення < 1000."""
    for case in CASES:
        assert 67 <= len(case["input"]) < 1000, case["label"]


def test_cases_use_different_keys() -> None:
    """У п'яти тестах п'ять різних ключів — перебір одного зсуву не пройде."""
    assert len({c["shift"] for c in CASES}) == len(CASES)


def test_cli_selftest_command() -> None:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "run.py"), "selftest"],
        capture_output=True, text=True, encoding="utf-8", timeout=120,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
