"""Generate unified Frontier Evaluation Report across OpenAI and Anthropic."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from symbolic_ir.budget import BudgetLedger
from scripts.analyze_frontier_musique import analyze_frontier_file
from scripts.analyze_frontier_reasoning import analyze_reasoning_ablation
from scripts.analyze_frontier_stage8 import analyze_stage8_file


EXPECTED_RECORDS = {
    "musique_500": 2_000,
    "reasoning": 400,
    "stage8": 2_000,
}


def _record_count(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line)


def compile_frontier_report(provider: str | None = None) -> dict[str, Any]:
    if provider not in {None, "anthropic", "openai"}:
        raise ValueError(f"Unsupported provider: {provider}")

    ledger = BudgetLedger(ROOT / "results/budget_ledger.jsonl")
    spend_openai = ledger.cumulative_cost("openai")
    spend_anthropic = ledger.cumulative_cost("anthropic")
    total_spend = spend_openai + spend_anthropic

    report: dict[str, Any] = {
        "budget": {
            "openai_actual_spend": spend_openai,
            "openai_cap": 45.0,
            "anthropic_actual_spend": spend_anthropic,
            "anthropic_cap": 45.0,
            "total_spend": total_spend,
            "total_ceiling": 90.0,
        },
        "scope": {
            "provider": provider or "all",
            "incomplete_files_excluded": True,
            "expected_records": EXPECTED_RECORDS,
        },
        "musique_500": {},
        "reasoning_ablation": {},
        "stage8_entity_resolution": {},
    }

    # MuSiQue files
    musique_dir = ROOT / "results/raw/musique_500"
    for p in sorted(musique_dir.glob("*.jsonl")):
        tag = p.stem
        if provider and not tag.startswith(f"{provider}_"):
            continue
        if _record_count(p) != EXPECTED_RECORDS["musique_500"]:
            continue
        try:
            res = analyze_frontier_file(p)
            report["musique_500"][tag] = res
        except Exception as e:
            report["musique_500"][tag] = {"error": str(e)}

    # Stage 8 files
    stage8_dir = ROOT / "results/raw/stage8"
    if stage8_dir.exists():
        for p in sorted(stage8_dir.glob("*.jsonl")):
            tag = p.stem
            if provider and not tag.startswith(f"{provider}_"):
                continue
            if _record_count(p) != EXPECTED_RECORDS["stage8"]:
                continue
            try:
                res = analyze_stage8_file(p)
                report["stage8_entity_resolution"][tag] = res
            except Exception as e:
                report["stage8_entity_resolution"][tag] = {"error": str(e)}

    # Reasoning ablation
    reasoning_dir = ROOT / "results/raw/reasoning"
    if provider in {None, "anthropic"} and (reasoning_dir / "anthropic_sonnet.jsonl").exists() and (musique_dir / "anthropic_sonnet.jsonl").exists() and _record_count(reasoning_dir / "anthropic_sonnet.jsonl") == EXPECTED_RECORDS["reasoning"] and _record_count(musique_dir / "anthropic_sonnet.jsonl") == EXPECTED_RECORDS["musique_500"]:
        try:
            report["reasoning_ablation"]["anthropic_sonnet"] = analyze_reasoning_ablation(
                musique_dir / "anthropic_sonnet.jsonl",
                reasoning_dir / "anthropic_sonnet.jsonl",
            )
        except Exception as e:
            report["reasoning_ablation"]["anthropic_sonnet"] = {"error": str(e)}

    if provider in {None, "openai"} and (reasoning_dir / "openai_luna.jsonl").exists() and (musique_dir / "openai_luna.jsonl").exists() and _record_count(reasoning_dir / "openai_luna.jsonl") == EXPECTED_RECORDS["reasoning"] and _record_count(musique_dir / "openai_luna.jsonl") == EXPECTED_RECORDS["musique_500"]:
        try:
            report["reasoning_ablation"]["openai_luna"] = analyze_reasoning_ablation(
                musique_dir / "openai_luna.jsonl",
                reasoning_dir / "openai_luna.jsonl",
            )
        except Exception as e:
            report["reasoning_ablation"]["openai_luna"] = {"error": str(e)}

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["anthropic", "openai"])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rep = compile_frontier_report(args.provider)
    default_name = f"frontier_{args.provider}_summary.json" if args.provider else "frontier_evaluation_summary.json"
    out_path = args.output or ROOT / "results/processed" / default_name
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(rep, indent=2) + "\n", encoding="utf-8")
    print(f"Frontier summary compiled to {out_path}.")
