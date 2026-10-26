from __future__ import annotations

import sys
from pathlib import Path

from symbolic_ir.config import load_config
from symbolic_ir.runner import run_experiment


def run(config_name: str) -> None:
    root = Path(__file__).resolve().parents[1]
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    path, counts = run_experiment(load_config(root / "configs" / "experiments" / config_name), limit=limit)
    print(f"{path}: {counts}")

