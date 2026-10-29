"""Phase 1: Connection and synchronous stability testing across 4 frontier models.

Measures:
- Parser success rate (threshold >= 99%)
- Binding-status agreement across 3 repetitions (threshold >= 95%)
- Truncation rate (threshold < 1%)
- Refusal rate
- Invalid citation rate
- Actual token consumption (input, output, reasoning, cache)
- Synchronous latency statistics
- Actual cost per model-condition cell
- Budget projection vs $45 hard stop
"""

from __future__ import annotations

import argparse
import concurrent.futures
import copy
import hashlib
import json
import os
import sys
import time
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from symbolic_ir.budget import BudgetLedger, calculate_cost, canonical_model_name  # noqa: E402
from symbolic_ir.data.musique import load_musique_examples  # noqa: E402
from symbolic_ir.evaluation import evaluate_output  # noqa: E402
from symbolic_ir.identifiers import render_identifiers  # noqa: E402
from symbolic_ir.inference.anthropic_api import AnthropicBackend  # noqa: E402
from symbolic_ir.inference.openai_api import OpenAIBackend  # noqa: E402
from symbolic_ir.prompts import render_prompt  # noqa: E402
from symbolic_ir.runner import JsonlStore  # noqa: E402
from symbolic_ir.schema import GenerationRequest  # noqa: E402
from symbolic_ir.tokenization import create_token_counter  # noqa: E402

MODELS = [
    {
        "provider": "openai",
        "slug": "gpt-6-luna",
        "model_name": "gpt-6-luna",
        "reasoning_effort": "none",
        "temperature": 0.0,
        "backend_cls": OpenAIBackend,
        "backend_kwargs": {"model": "gpt-6-luna", "reasoning_effort": "none", "temperature": 0.0, "is_batch": False},
    },
    {
        "provider": "openai",
        "slug": "gpt-6-1-sol",
        "model_name": "gpt-6.1-sol",
        "reasoning_effort": "low",
        "temperature": None,
        "backend_cls": OpenAIBackend,
        "backend_kwargs": {"model": "gpt-6.1-sol", "reasoning_effort": "low", "temperature": None, "is_batch": False},
    },
    {
        "provider": "anthropic",
        "slug": "claude-haiku-5-5",
        "model_name": "claude-haiku-5-5",
        "thinking_type": "disabled",
        "effort": "low",
        "backend_cls": AnthropicBackend,
        "backend_kwargs": {"model": "claude-haiku-5-5", "thinking_type": "disabled", "effort": "low", "is_batch": False},
    },
    {
        "provider": "anthropic",
        "slug": "claude-sonnet-5-5",
        "model_name": "claude-sonnet-5-5",
        "thinking_type": "between_tools",
        "effort": "low",
        "backend_cls": AnthropicBackend,
        "backend_kwargs": {"model": "claude-sonnet-5-5", "thinking_type": "between_tools", "effort": "low", "is_batch": False},
    },
]


def run_single_probe(backend: Any, label: str) -> None:
    req = GenerationRequest(
        prompt="Answer the question directly. What is 2 + 2?\nANSWER:",
        example_id="probe",
        max_output_tokens=32,
    )
    started = time.perf_counter()
    resp = backend.generate(req)
    latency = time.perf_counter() - started
    print(f"  [PROBE SUCCESS] {label} in {latency:.2f}s -> response: {resp.text.strip()!r} (tokens: in={resp.input_tokens}, out={resp.output_tokens}, cost=${resp.calculated_cost:.6f})")


def run_connection_test(backends: dict[str, Any]) -> None:
    print("=== Step 1: Four-request connection test ===")
    for model_cfg in MODELS:
        slug = model_cfg["slug"]
        backend = backends[slug]
        try:
            run_single_probe(backend, slug)
        except Exception as exc:
            print(f"  [PROBE FAILED] {slug}: {exc}", file=sys.stderr)
            raise RuntimeError(f"Connection test failed for {slug}. Stopping immediately.") from exc
    print("All four model configurations connected successfully!\n")


def build_prompts(seed: int = 202620) -> list[dict[str, Any]]:
    tokenizer = create_token_counter({"type": "regex"})
    prompt_items = []
    for num_sources in [15, 20]:
        config = {
            "data_path": str(ROOT / "data/musique/musique_ans_v1.0_dev.jsonl"),
            "selection_path": str(ROOT / "configs/musique/calibration_20.json"),
            "num_sources": num_sources,
            "count": 20,
        }
        examples = load_musique_examples(config, seed)
        for ex in examples:
            for condition in ["numeric", "uuid"]:
                mapping = render_identifiers(ex.sources, condition, seed, tokenizer)
                rendered = render_prompt(ex, mapping, require_citations=True)
                expected_citations = [mapping.citation_by_source[k] for k in ex.relevant_sources]
                prompt_items.append({
                    "example_id": ex.example_id,
                    "num_sources": num_sources,
                    "condition": condition,
                    "mapping": mapping,
                    "rendered": rendered,
                    "prompt": rendered.prompt,
                    "expected_answer": rendered.expected_answer or ex.answer,
                    "expected_citations": expected_citations,
                })
    return prompt_items


def execute_call(
    backend: Any,
    model_cfg: dict[str, Any],
    item: dict[str, Any],
    rep: int,
    store: JsonlStore,
    completed_keys: set[str],
) -> dict[str, Any]:
    slug = model_cfg["slug"]
    key = f"phase1_{slug}_{item['example_id']}_{item['num_sources']}_{item['condition']}_rep{rep}"
    if key in completed_keys:
        return {"request_key": key, "status": "skipped"}

    req = GenerationRequest(
        prompt=item["prompt"],
        example_id=item["example_id"],
        max_output_tokens=256,
        temperature=model_cfg.get("temperature"),
        reasoning_budget=model_cfg.get("reasoning_effort"),
        thinking_type=model_cfg.get("thinking_type"),
        effort=model_cfg.get("effort"),
        metadata={
            "request_key": key,
            "expected_answer": item["expected_answer"],
            "expected_citations": item["expected_citations"],
            "repetition": rep,
            "num_sources": item["num_sources"],
            "condition": item["condition"],
        },
    )

    started = time.perf_counter()
    resp = backend.generate(req)
    total_latency = time.perf_counter() - started

    evaluation = evaluate_output(item["rendered"], resp.text)
    record = {
        "request_key": key,
        "phase": "phase1_stability",
        "provider": model_cfg["provider"],
        "model_slug": slug,
        "model": resp.model,
        "repetition": rep,
        "example_id": item["example_id"],
        "num_sources": item["num_sources"],
        "condition": item["condition"],
        "prompt_hash": resp.prompt_hash,
        "request_id": resp.request_id,
        "stop_reason": resp.stop_reason,
        "retry_count": resp.retry_count,
        "latency_seconds": resp.latency_seconds or total_latency,
        "calculated_cost": resp.calculated_cost,
        "request_body": resp.request_body,
        "token_counts": {
            "input": resp.input_tokens,
            "output": resp.output_tokens,
            "cache": resp.cached_tokens,
            "reasoning": resp.reasoning_tokens,
        },
        "raw_output": resp.text,
        "parsed_answer": evaluation["parsed_answer"],
        "parsed_citations": evaluation["parsed_citations"],
        "answer_correct": evaluation["answer_correct"],
        "answer_f1": evaluation["answer_f1"],
        "citation_exact_match": evaluation["citation_exact_match"],
        "citation_precision": evaluation["citation_precision"],
        "citation_recall": evaluation["citation_recall"],
        "invalid_ids": evaluation["invalid_ids"],
        "malformed_ids": evaluation["malformed_ids"],
        "failure_category": evaluation["failure_category"],
        "strict_format": evaluation["strict_format"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    store.append(record)
    completed_keys.add(key)
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--concurrency", type=int, default=4, help="Max workers for concurrent synchronous calls")
    parser.add_argument("--dry-run", action="store_true", help="Validate prompts without calling API")
    args = parser.parse_args()

    # Pre-render prompts
    prompts = build_prompts(seed=202620)
    print(f"Prepared {len(prompts)} unique conditions across 20 calibration questions (15 and 20 sources, numeric and uuid).")
    if args.dry_run:
        print("Dry run complete.")
        return 0

    # Initialize backends
    backends = {}
    for cfg in MODELS:
        slug = cfg["slug"]
        backends[slug] = cfg["backend_cls"](**cfg["backend_kwargs"])

    # Step 1: Probe
    run_connection_test(backends)

    # Step 2: Run 960 calls
    ledger = BudgetLedger()
    raw_dir = ROOT / "results/raw/frontier_stability"
    raw_dir.mkdir(parents=True, exist_ok=True)

    print("=== Step 2: Executing 960 synchronous stability calls ===")
    for model_cfg in MODELS:
        slug = model_cfg["slug"]
        provider = model_cfg["provider"]
        backend = backends[slug]
        store_path = raw_dir / f"{provider}_{slug}.jsonl"
        store = JsonlStore(store_path)
        completed = store.completed_keys()
        print(f"\nRunning {slug} ({provider})... (Already completed: {len(completed)}/240)")

        tasks = []
        for rep in [1, 2, 3]:
            for item in prompts:
                tasks.append((item, rep))

        batch_start = time.perf_counter()
        completed_records = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
            futures = [
                pool.submit(execute_call, backend, model_cfg, item, rep, store, completed)
                for item, rep in tasks
            ]
            for idx, future in enumerate(concurrent.futures.as_completed(futures), 1):
                rec = future.result()
                if rec.get("status") != "skipped":
                    completed_records.append(rec)
                if idx % 40 == 0 or idx == len(tasks):
                    print(f"  [{slug}] {idx}/{len(tasks)} processed ({len(completed)} store entries)")

        batch_time = time.perf_counter() - batch_start
        print(f"Finished {slug} in {batch_time:.1f}s.")

        # Record in budget ledger
        # Read all records for this model from store
        all_records = [json.loads(line) for line in store_path.read_text(encoding="utf-8").splitlines() if line]
        total_inp = sum(int(r["token_counts"]["input"] or 0) for r in all_records)
        total_out = sum(int(r["token_counts"]["output"] or 0) for r in all_records)
        total_cost = sum(float(r["calculated_cost"] or 0.0) for r in all_records)
        ledger.record(
            provider=provider,
            batch_id=f"sync-phase1-{slug}",
            experiment="frontier_phase1_stability",
            requests=len(all_records),
            actual_input_tokens=total_inp,
            actual_output_tokens=total_out,
            actual_cost=total_cost,
        )
        print(f"Ledger updated: {slug} total_cost=${total_cost:.4f}, provider cumulative=${ledger.cumulative_cost(provider):.4f}")

    # Step 3: Analysis and Validation Gates
    print("\n=== Step 3: Computing Phase 1 Stability Metrics & Gates ===")
    analysis_results = {}
    gate_passed = True
    gate_failures = []

    for model_cfg in MODELS:
        slug = model_cfg["slug"]
        provider = model_cfg["provider"]
        store_path = raw_dir / f"{provider}_{slug}.jsonl"
        records = [json.loads(line) for line in store_path.read_text(encoding="utf-8").splitlines() if line]

        total_calls = len(records)
        assert total_calls == 240, f"Expected 240 records for {slug}, found {total_calls}"

        # 1. Parser success rate: percentage of responses with valid parsed_answer
        parsed_ok = sum(1 for r in records if r["parsed_answer"] is not None and str(r["parsed_answer"]).strip() != "")
        parser_success_rate = (parsed_ok / total_calls) * 100.0

        # 2. Truncation rate
        def is_truncated(r: dict) -> bool:
            stop = str(r.get("stop_reason") or "").lower()
            return stop in ("max_tokens", "length", "incomplete")
        truncated_count = sum(1 for r in records if is_truncated(r))
        truncation_rate = (truncated_count / total_calls) * 100.0

        # 3. Refusals
        def is_refusal(r: dict) -> bool:
            out = str(r.get("raw_output") or "").lower()
            return any(phrase in out for phrase in ["i cannot", "i am unable", "i apologize", "as an ai"]) and not r.get("answer_correct")
        refusal_count = sum(1 for r in records if is_refusal(r))
        refusal_rate = (refusal_count / total_calls) * 100.0

        # 4. Invalid citation rate
        invalid_count = sum(1 for r in records if r.get("invalid_ids"))
        invalid_rate = (invalid_count / total_calls) * 100.0

        # 5. Token consumption
        in_tokens = [int(r["token_counts"]["input"] or 0) for r in records]
        out_tokens = [int(r["token_counts"]["output"] or 0) for r in records]
        reas_tokens = [int(r["token_counts"].get("reasoning") or 0) for r in records]
        cache_tokens = [int(r["token_counts"].get("cache") or 0) for r in records]

        # 6. Latency
        latencies = [float(r.get("latency_seconds") or 0.0) for r in records]
        latencies_sorted = sorted(latencies)

        # 7. Binding-status agreement across repetitions
        # Group by item key: (example_id, num_sources, condition)
        grouped = defaultdict(dict)
        for r in records:
            item_key = (r["example_id"], r["num_sources"], r["condition"])
            rep = r["repetition"]
            grouped[item_key][rep] = r

        triplet_agreements = []
        pairwise_agreements = []
        for item_key, reps in grouped.items():
            if len(reps) != 3:
                continue
            # Binding status is citation_exact_match or tuple of sorted parsed_citations
            b1 = (reps[1]["citation_exact_match"], tuple(sorted(reps[1]["parsed_citations"])))
            b2 = (reps[2]["citation_exact_match"], tuple(sorted(reps[2]["parsed_citations"])))
            b3 = (reps[3]["citation_exact_match"], tuple(sorted(reps[3]["parsed_citations"])))

            triplet_agreements.append(b1 == b2 == b3)
            pair_agree = ((b1 == b2) + (b2 == b3) + (b1 == b3)) / 3.0
            pairwise_agreements.append(pair_agree)

        triplet_agree_rate = (sum(triplet_agreements) / len(triplet_agreements)) * 100.0 if triplet_agreements else 0.0
        pairwise_agree_rate = (sum(pairwise_agreements) / len(pairwise_agreements)) * 100.0 if pairwise_agreements else 0.0

        # Total cost
        cost_total = sum(float(r["calculated_cost"] or 0.0) for r in records)

        model_summary = {
            "model_slug": slug,
            "provider": provider,
            "total_calls": total_calls,
            "parser_success_rate": round(parser_success_rate, 2),
            "truncation_rate": round(truncation_rate, 2),
            "refusal_rate": round(refusal_rate, 2),
            "invalid_citation_rate": round(invalid_rate, 2),
            "triplet_agreement_rate": round(triplet_agree_rate, 2),
            "pairwise_agreement_rate": round(pairwise_agree_rate, 2),
            "token_usage": {
                "input_mean": round(sum(in_tokens) / len(in_tokens), 1),
                "output_mean": round(sum(out_tokens) / len(out_tokens), 1),
                "reasoning_mean": round(sum(reas_tokens) / len(reas_tokens), 1),
                "cache_mean": round(sum(cache_tokens) / len(cache_tokens), 1),
            },
            "latency": {
                "min": round(latencies_sorted[0], 3),
                "mean": round(sum(latencies) / len(latencies), 3),
                "median": round(latencies_sorted[len(latencies_sorted) // 2], 3),
                "p95": round(latencies_sorted[int(len(latencies_sorted) * 0.95)], 3),
                "max": round(latencies_sorted[-1], 3),
            },
            "actual_cost": round(cost_total, 4),
        }
        analysis_results[slug] = model_summary

        # Check gates per model
        if parser_success_rate < 99.0:
            gate_passed = False
            gate_failures.append(f"{slug}: Parser success rate {parser_success_rate:.2f}% < 99.0%")
        if pairwise_agree_rate < 95.0:
            gate_passed = False
            gate_failures.append(f"{slug}: Pairwise agreement rate {pairwise_agree_rate:.2f}% < 95.0%")
        if truncation_rate >= 1.0:
            gate_passed = False
            gate_failures.append(f"{slug}: Truncation rate {truncation_rate:.2f}% >= 1.0%")

    # Provider spend check
    openai_cost = ledger.cumulative_cost("openai")
    anthropic_cost = ledger.cumulative_cost("anthropic")
    print(f"\nProvider Spend after Phase 1:")
    print(f"  OpenAI: ${openai_cost:.4f} (Cap: $4.00, Hard stop: $45.00)")
    print(f"  Anthropic: ${anthropic_cost:.4f} (Cap: $4.00, Hard stop: $45.00)")

    if openai_cost > 45.0:
        gate_passed = False
        gate_failures.append(f"OpenAI cost ${openai_cost:.2f} > $45 hard stop")
    if anthropic_cost > 45.0:
        gate_passed = False
        gate_failures.append(f"Anthropic cost ${anthropic_cost:.2f} > $45 hard stop")

    # Project future phase costs
    # Phase 2 MuSiQue 500: 4,000 calls per provider (batch discounted)
    # Expected: Luna: 2000 * 3.5k in ($0.05/M) + 2000 * 50 out ($0.25/M) = $0.35 + $0.025 = $0.38
    # Sol: 2000 * 3.5k in ($1/M) + 2000 * 100 out ($5/M) = $7.00 + $1.00 = $8.00
    # Phase 2 OpenAI: ~$8.40. Anthropic: ~$8.40.
    # Phase 3 Reasoning: 400 calls per provider: ~$1.80.
    # Phase 4 Stage 8: 2,000 calls per provider: ~$7.00.
    # Total projected spend: OpenAI ~$19.50, Anthropic ~$19.50. Both << $45.00.

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "gate_passed": gate_passed,
        "gate_failures": gate_failures,
        "provider_spend": {
            "openai": openai_cost,
            "anthropic": anthropic_cost,
        },
        "models": analysis_results,
    }

    out_file = ROOT / "results/processed/frontier_phase1_stability.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote results to {out_file}")

    print("\n" + "=" * 60)
    print("PHASE 1 STABILITY SUMMARY TABLE")
    print("=" * 60)
    print(f"{'Model':<20} | {'Parser %':<9} | {'Agree %':<9} | {'Trunc %':<8} | {'Cost':<8} | {'Lat(med)':<8}")
    print("-" * 72)
    for slug, res in analysis_results.items():
        print(f"{slug:<20} | {res['parser_success_rate']:<9.1f} | {res['pairwise_agreement_rate']:<9.1f} | {res['truncation_rate']:<8.1f} | ${res['actual_cost']:<7.4f} | {res['latency']['median']:<7.2f}s")
    print("-" * 72)

    if gate_passed:
        print(">>> ALL PHASE 1 GATES PASSED! Proceeding to Phase 2. <<<")
        return 0
    else:
        print(">>> GATES FAILED: <<<")
        for f in gate_failures:
            print("  -", f)
        return 1


if __name__ == "__main__":
    sys.exit(main())
