"""Append-only budget tracking, pricing lookup, and budget gating."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Pricing per million tokens: (input_price, output_price)
BATCH_PRICING: dict[str, tuple[float, float]] = {
    "gpt-6-luna": (0.05, 0.25),
    "gpt-6.1-sol": (1.00, 5.00),
    "claude-haiku-5-5": (0.05, 0.25),
    "claude-sonnet-5-5": (1.00, 5.00),
}

SYNC_PRICING: dict[str, tuple[float, float]] = {
    "gpt-6-luna": (0.10, 0.50),
    "gpt-6.1-sol": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-sonnet-5-5": (2.00, 10.00),
}


def canonical_model_name(model: str) -> str:
    m = model.lower()
    if "luna" in m:
        return "gpt-6-luna"
    if "sol" in m:
        return "gpt-6.1-sol"
    if "haiku-5-5" in m or "haiku" in m:
        return "claude-haiku-5-5"
    if "sonnet-5-5" in m or "sonnet" in m:
        return "claude-sonnet-5-5"
    return model


def calculate_cost(
    model: str,
    input_tokens: int | None,
    output_tokens: int | None,
    mode: str = "batch",
    cached_tokens: int | None = 0,
) -> float:
    inp = int(input_tokens or 0)
    out = int(output_tokens or 0)
    canonical = canonical_model_name(model)
    table = BATCH_PRICING if mode == "batch" else SYNC_PRICING
    if canonical not in table:
        return 0.0
    in_rate, out_rate = table[canonical]
    cost = (inp / 1_000_000.0) * in_rate + (out / 1_000_000.0) * out_rate
    return round(cost, 8)


class BudgetLedger:
    DEFAULT_PATH = Path("results/budget_ledger.jsonl")

    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path else self.DEFAULT_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load_entries(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        entries = []
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return entries

    def cumulative_cost(self, provider: str) -> float:
        prov = provider.lower()
        entries = self.load_entries()
        total = sum(float(e.get("actual_cost", 0.0)) for e in entries if e.get("provider", "").lower() == prov)
        return round(total, 6)

    def record(
        self,
        provider: str,
        batch_id: str,
        experiment: str,
        requests: int,
        actual_input_tokens: int,
        actual_output_tokens: int,
        actual_cost: float,
    ) -> dict[str, Any]:
        prov = provider.lower()
        prev_cumulative = self.cumulative_cost(prov)
        new_cumulative = round(prev_cumulative + actual_cost, 6)
        entry = {
            "provider": prov,
            "batch_id": batch_id,
            "experiment": experiment,
            "requests": int(requests),
            "actual_input_tokens": int(actual_input_tokens),
            "actual_output_tokens": int(actual_output_tokens),
            "actual_cost": round(float(actual_cost), 6),
            "cumulative_cost": new_cumulative,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        payload = (json.dumps(entry, sort_keys=True, ensure_ascii=False) + "\n").encode()
        descriptor = os.open(self.path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o644)
        try:
            os.write(descriptor, payload)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        return entry

    def check_budget_gate(
        self,
        provider: str,
        conservative_cost_of_next_batch: float,
        retry_reserve: float = 5.0,
        hard_stop: float = 45.0,
        primary_batches_done: bool = False,
    ) -> tuple[bool, str]:
        prov = provider.lower()
        cum_cost = self.cumulative_cost(prov)
        if cum_cost >= hard_stop:
            return False, f"Automatic hard stop triggered: {prov} actual spend ${cum_cost:.4f} >= ${hard_stop:.2f}"
        if not primary_batches_done and cum_cost >= 40.0:
            return False, f"Threshold gate triggered: {prov} actual spend ${cum_cost:.4f} >= $40.00 before primary batches completed"
        projected_total = cum_cost + conservative_cost_of_next_batch + retry_reserve
        if projected_total > hard_stop:
            return False, f"Projected total ${projected_total:.4f} exceeds hard stop of ${hard_stop:.2f} (current=${cum_cost:.4f}, next=${conservative_cost_of_next_batch:.4f}, reserve=${retry_reserve:.2f})"
        return True, f"Budget gate approved: current=${cum_cost:.4f}, next=${conservative_cost_of_next_batch:.4f}, projected=${projected_total:.4f} <= ${hard_stop:.2f}"
