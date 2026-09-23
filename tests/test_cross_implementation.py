"""
Перехресна перевірка двох незалежних реалізацій (Python і C#).

Тести автоматично пропускаються, якщо .NET SDK не встановлено.
"""

from __future__ import annotations

import json
import random
import shutil
import subprocess
from pathlib import Path

import pytest

from freqcrack import ALPHABET, M, break_caesar, encrypt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PROJECT = ROOT / "csharp" / "Freq"
CASES = json.loads((HERE / "official_cases.json").read_text(encoding="utf-8"))["cases"]

dotnet_required = pytest.mark.skipif(
    shutil.which("dotnet") is None, reason=".NET SDK не встановлено"
)


def _run_csharp(args: list[str], stdin: str | None = None) -> str:
    # Явне UTF-8: програма на C# сама виставляє Console.OutputEncoding = UTF8,
    # тож покладатися на локаль консолі Windows не можна.
    proc = subprocess.run(
        ["dotnet", "run", "--project", str(PROJECT), "--"] + args,
        input=stdin, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=300,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return proc.stdout.rstrip("\n")


@dotnet_required
def test_csharp_selftest_passes() -> None:
    out = _run_csharp(["selftest"])
    assert "пройдено 3 з 3" in out
    assert "2000 з 2000" in out
    assert "FAIL" not in out


@dotnet_required
@pytest.mark.parametrize("case", CASES, ids=[c["label"] for c in CASES])
def test_python_and_csharp_break_identically(case: dict) -> None:
    """Обидві реалізації мають відновити той самий відкритий текст."""
    assert _run_csharp([], stdin=case["input"] + "\n") == case["expected"]
    assert break_caesar(case["input"], "chi2").plaintext == case["expected"]


@dotnet_required
@pytest.mark.parametrize("key", [0, 5, 13, 25])
def test_encryption_matches_between_languages(key: int) -> None:
    rng = random.Random(key)
    text = "".join(rng.choice(ALPHABET + ALPHABET.lower() + " ,.") for _ in range(70))
    assert _run_csharp(["encrypt", str(key), text]) == encrypt(text, key)
