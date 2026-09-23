#!/usr/bin/env python3
"""
Точка входу без встановлення пакета.

    python run.py selftest
    python run.py break --text "Khoor Zruog !"
    python run.py compare --text "<шифротекст>"
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from freqcrack.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
