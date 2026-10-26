#!/usr/bin/env python3
"""Stage 9 deterministic canonicalize/validate/rehydrate evaluation."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from evaluate_stage9_system import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
