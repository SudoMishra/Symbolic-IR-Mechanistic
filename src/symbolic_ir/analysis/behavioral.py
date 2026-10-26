from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from symbolic_ir.evaluation.metrics import aggregate_records


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def summarize_file(path: str | Path) -> list[dict[str, Any]]:
    return aggregate_records(load_jsonl(path))

