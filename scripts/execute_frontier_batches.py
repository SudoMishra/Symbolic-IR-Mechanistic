"""Unified batch submission, status tracking, result retrieval, and evaluation.

Implements strict budget gates:
- projected_total = cumulative_actual_cost + conservative_cost_of_next_batch + $5 retry reserve <= $45
- Stop at $40 cumulative unless all required primary batches are already complete
- Absolute automatic stop at $45/provider
- Never retry successful requests
- Maximum two retries per failed request (429, 5xx, canceled, expired)
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from symbolic_ir.budget import BudgetLedger, calculate_cost  # noqa: E402
from symbolic_ir.data.musique import load_musique_examples  # noqa: E402
from symbolic_ir.evaluation import evaluate_output  # noqa: E402
from symbolic_ir.evaluation.answer import answer_exact_match  # noqa: E402
from symbolic_ir.evaluation.parser import parse_output  # noqa: E402
from symbolic_ir.identifiers import render_identifiers  # noqa: E402
from symbolic_ir.inference.batch import AnthropicBatchManager, OpenAIBatchManager  # noqa: E402
from symbolic_ir.prompts import render_prompt  # noqa: E402
from symbolic_ir.runner import JsonlStore  # noqa: E402
from symbolic_ir.tokenization import create_token_counter  # noqa: E402

TRACKING_DIR = ROOT / "results/batches/tracking"


def get_prepared_dir(phase: str) -> Path:
    if phase == "musique_500":
        return ROOT / "results/batches/prepared/musique_500"
    if phase == "reasoning":
        return ROOT / "results/batches/prepared/reasoning_ablation_100"
    if phase == "stage8":
        return ROOT / "results/batches/prepared/stage8_500"
    raise ValueError(f"Unknown phase: {phase}")


def get_raw_output_path(phase: str, provider: str, model_slug: str) -> Path:
    return ROOT / f"results/raw/{phase}/{provider}_{model_slug}.jsonl"


def estimate_next_batch_cost(phase: str, model_slug: str, count: int = 500) -> float:
    # Conservative token estimates
    if phase == "stage8":
        in_tokens = 3200
        out_tokens = 64
    elif phase == "reasoning":
        in_tokens = 3800
        out_tokens = 800
    else:
        in_tokens = 3800
        out_tokens = 100
    total_in = count * in_tokens
    total_out = count * out_tokens
    return calculate_cost(model_slug, total_in, total_out, mode="batch") * 1.25  # 25% conservative buffer


def submit_batch_job(
    phase: str,
    provider: str,
    model_slug: str,
    block_idx: int | str,
    ledger: BudgetLedger,
    primary_batches_done: bool = False,
) -> dict[str, Any]:
    TRACKING_DIR.mkdir(parents=True, exist_ok=True)
    track_file = TRACKING_DIR / f"{phase}_{provider}_{model_slug}_b{block_idx}.json"
    if track_file.exists():
        existing = json.loads(track_file.read_text(encoding="utf-8"))
        print(f"Batch {track_file.name} already submitted (id={existing.get('batch_id')}, status={existing.get('status')}).")
        return existing

    # Budget gate check
    conservative_cost = estimate_next_batch_cost(phase, model_slug, count=500 if phase != "reasoning" else 400)
    approved, reason = ledger.check_budget_gate(
        provider=provider,
        conservative_cost_of_next_batch=conservative_cost,
        retry_reserve=5.0,
        hard_stop=45.0,
        primary_batches_done=primary_batches_done,
    )
    if not approved:
        raise RuntimeError(f"BUDGET GATE REJECTED: {reason}")
    print(f"  [BUDGET GATE PASSED] {reason}")

    prep_dir = get_prepared_dir(phase)
    if provider == "openai":
        manager = OpenAIBatchManager()
        # Find jsonl payload
        if phase == "reasoning":
            payload_path = prep_dir / f"openai_luna_medium.jsonl"
        elif phase == "stage8":
            payload_path = prep_dir / f"openai_{model_slug}_block_{block_idx}.jsonl"
        else:
            payload_path = prep_dir / f"openai_{model_slug}_block_{block_idx}.jsonl"

        items = [json.loads(line) for line in payload_path.read_text(encoding="utf-8").splitlines() if line]
        record = manager.submit_batch(
            items=items,
            batch_record_path=track_file,
            metadata={"phase": phase, "model": model_slug, "block": str(block_idx)},
        )
        print(f"Submitted OpenAI batch {record['batch_id']} ({len(items)} requests).")
        return record
    elif provider == "anthropic":
        manager = AnthropicBatchManager()
        if phase == "reasoning":
            payload_path = prep_dir / f"anthropic_sonnet_adaptive.json"
        elif phase == "stage8":
            payload_path = prep_dir / f"anthropic_{model_slug}_block_{block_idx}.json"
        else:
            payload_path = prep_dir / f"anthropic_{model_slug}_block_{block_idx}.json"

        items = json.loads(payload_path.read_text(encoding="utf-8"))
        record = manager.submit_batch(
            items=items,
            batch_record_path=track_file,
        )
        print(f"Submitted Anthropic batch {record['batch_id']} ({len(items)} requests).")
        return record
    else:
        raise ValueError(f"Unknown provider: {provider}")


def check_batch_jobs(phase: str | None = None) -> list[dict[str, Any]]:
    TRACKING_DIR.mkdir(parents=True, exist_ok=True)
    statuses = []
    oai_manager = None
    ant_manager = None

    for f in sorted(TRACKING_DIR.glob("*.json")):
        if phase and not f.name.startswith(phase):
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        batch_id = data.get("batch_id")
        provider = data.get("provider")
        if not batch_id or not provider:
            continue

        if provider == "openai":
            if not oai_manager:
                oai_manager = OpenAIBatchManager()
            st = oai_manager.check_status(batch_id)
        else:
            if not ant_manager:
                ant_manager = AnthropicBatchManager()
            st = ant_manager.check_status(batch_id)

        data["status"] = st.get("status")
        data["counts"] = {k: v for k, v in st.items() if "requests" in k or "id" in k}
        f.write_text(json.dumps(data, indent=2, default=str) + "\n", encoding="utf-8")
        statuses.append(data)
    return statuses


def retrieve_and_evaluate_batch(
    phase: str,
    provider: str,
    model_slug: str,
    block_idx: int | str,
    ledger: BudgetLedger,
) -> dict[str, Any]:
    track_file = TRACKING_DIR / f"{phase}_{provider}_{model_slug}_b{block_idx}.json"
    if not track_file.exists():
        raise FileNotFoundError(f"Tracking file {track_file} does not exist.")
    track_data = json.loads(track_file.read_text(encoding="utf-8"))
    batch_id = track_data["batch_id"]

    prep_dir = get_prepared_dir(phase)
    manifest = json.loads((prep_dir / "manifest.json").read_text(encoding="utf-8"))

    rendered_cache = {}
    if phase in ("musique_500", "reasoning"):
        tokenizer = create_token_counter({"type": "regex"})
        seed = 202620
        for ns in [15, 20]:
            cfg = {
                "data_path": str(ROOT / "data/musique/musique_ans_v1.0_dev.jsonl"),
                "selection_path": str(ROOT / "configs/musique/musique_balanced_500.json"),
                "num_sources": ns,
                "count": 500,
            }
            for ex in load_musique_examples(cfg, seed):
                for cond in ["numeric", "uuid"]:
                    mapping = render_identifiers(ex.sources, cond, seed, tokenizer)
                    rendered = render_prompt(ex, mapping, require_citations=True)
                    rendered_cache[(ex.example_id, ns, cond)] = rendered

    if provider == "openai":
        manager = OpenAIBatchManager()
        results = manager.retrieve_results(batch_id)
    else:
        manager = AnthropicBatchManager()
        results = manager.retrieve_results(batch_id)

    raw_path = get_raw_output_path(phase, provider, model_slug)
    store = JsonlStore(raw_path)
    completed_keys = store.completed_keys()

    actual_in = 0
    actual_out = 0
    actual_cost = 0.0
    parsed_ok = 0
    total_items = len(results)

    for cid, res in results.items():
        if cid in completed_keys:
            continue
        meta = manifest.get(cid, {})
        text = res["text"]
        actual_in += int(res.get("input_tokens") or 0)
        actual_out += int(res.get("output_tokens") or 0)
        actual_cost += float(res.get("calculated_cost") or 0.0)

        # Evaluation
        if phase == "stage8":
            parsed = parse_output(text, ())
            ans = parsed.answer or text.strip()
            expected = meta.get("expected_answer", "")
            eval_dict = {
                "parsed_answer": ans,
                "answer_correct": answer_exact_match(ans, expected),
                "raw_pii_leakage": any(p in text for p in meta.get("protected_values", [])),
            }
            if ans:
                parsed_ok += 1
        else:
            # MuSiQue citation evaluation using exact rendered example
            ex_key = (meta["example_id"], meta["num_sources"], meta["condition"])
            rendered = rendered_cache[ex_key]
            eval_dict = evaluate_output(rendered, text)
            if eval_dict.get("parsed_answer"):
                parsed_ok += 1

        record = {
            "request_key": cid,
            "example_id": meta.get("example_id"),
            "num_sources": meta.get("num_sources"),
            "condition": meta.get("condition"),
            "phase": phase,
            "provider": provider,
            "model_slug": model_slug,
            "block": block_idx,
            "batch_id": batch_id,
            "raw_output": text,
            "token_counts": {
                "input": res.get("input_tokens"),
                "output": res.get("output_tokens"),
                "cache": res.get("cached_tokens"),
                "reasoning": res.get("reasoning_tokens"),
            },
            "stop_reason": res.get("stop_reason"),
            "calculated_cost": res.get("calculated_cost"),
            "evaluation": eval_dict,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        store.append(record)
        completed_keys.add(cid)

    # Record in budget ledger
    ledger.record(
        provider=provider,
        batch_id=batch_id,
        experiment=f"{phase}_{model_slug}_b{block_idx}",
        requests=total_items,
        actual_input_tokens=actual_in,
        actual_output_tokens=actual_out,
        actual_cost=actual_cost,
    )
    track_data["retrieved_at"] = datetime.now(timezone.utc).isoformat()
    track_data["actual_cost"] = actual_cost
    track_data["parsed_success_rate"] = round((parsed_ok / total_items) * 100.0, 2) if total_items else 0.0
    track_file.write_text(json.dumps(track_data, indent=2, default=str) + "\n", encoding="utf-8")

    print(f"Retrieved and evaluated batch {batch_id}: {total_items} items, cost=${actual_cost:.4f}, parser_success={track_data['parsed_success_rate']}%.")
    return track_data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", choices=["submit", "status", "retrieve"], required=True)
    parser.add_argument("--phase", choices=["musique_500", "reasoning", "stage8"], default="musique_500")
    parser.add_argument("--provider", choices=["openai", "anthropic"])
    parser.add_argument("--model", choices=["luna", "sol", "haiku", "sonnet"])
    parser.add_argument("--block", type=str, default="0")
    parser.add_argument("--primary-done", action="store_true")
    args = parser.parse_args()

    ledger = BudgetLedger()

    if args.action == "status":
        statuses = check_batch_jobs(args.phase)
        print(f"Active batch statuses ({len(statuses)} total):")
        for s in statuses:
            print(f"  [{s.get('provider')}] {s.get('batch_id')}: status={s.get('status')} {s.get('counts')}")
        return 0

    if args.action == "submit":
        if not args.provider or not args.model:
            print("Must specify --provider and --model for submit", file=sys.stderr)
            return 1
        res = submit_batch_job(
            phase=args.phase,
            provider=args.provider,
            model_slug=args.model,
            block_idx=args.block,
            ledger=ledger,
            primary_batches_done=args.primary_done,
        )
        print(json.dumps(res, indent=2, default=str))
        return 0

    if args.action == "retrieve":
        if not args.provider or not args.model:
            print("Must specify --provider and --model for retrieve", file=sys.stderr)
            return 1
        res = retrieve_and_evaluate_batch(
            phase=args.phase,
            provider=args.provider,
            model_slug=args.model,
            block_idx=args.block,
            ledger=ledger,
        )
        print(json.dumps(res, indent=2, default=str))
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
