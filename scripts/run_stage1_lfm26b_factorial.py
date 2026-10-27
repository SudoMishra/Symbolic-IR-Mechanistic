#!/usr/bin/env python3
"""Stage 1 Factorial Ablation for LFM2.5-2.6B on 100 paired examples.

Compares:
1. default_80:  Default chat template, 80-token cap
2. default_512: Default chat template, 512-token cap
3. prefill_80:  Closed-thinking prefill, 80-token cap
4. prefill_512: Closed-thinking prefill, 512-token cap

On 100 paired examples at N=5 and N=20 sources (structured vs uuid).
Total generations: 100 * 2 * 2 * 4 = 1,600.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from symbolic_ir.data.citation import generate_citation_examples
from symbolic_ir.evaluation import evaluate_output
from symbolic_ir.identifiers import render_identifiers
from symbolic_ir.prompts import render_prompt
from symbolic_ir.tokenization import create_token_counter


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", text.lower().replace("’", "'"))).strip()


def citation_field(output: str) -> str:
    match = re.search(r"(?im)^\s*CITATIONS?\s*:\s*(.*?)\s*$", output)
    return match.group(1) if match else ""


def relaxed_sources(raw_output: str, citation_by_source: dict[str, str]) -> set[str]:
    text = citation_field(raw_output)
    found = set()
    for source, label in citation_by_source.items():
        inner = (
            label[1:-1]
            if len(label) >= 2 and (label[0], label[-1]) in {("[", "]"), ("<", ">")}
            else label
        )
        if label in text or re.search(r"(?<![A-Za-z0-9])" + re.escape(inner) + r"(?![A-Za-z0-9])", text, re.I):
            found.add(source)
    return found

try:
    import llama_cpp
except ImportError:
    raise RuntimeError("llama_cpp required")

MODEL_PATH = "models/LFM2.5-2.6B-Q4_K_M.gguf"
MODEL_NAME = "LiquidAI/LFM2.5-2.6B-GGUF:q4_k_m"
MODEL_REVISION = "e7caca5d835a3901a8e0d63e94009429bafafdfc"
GGUF_SHA256 = "02a8b7e17487d326e46d68ce0ba24211e1b80a14c4cd0597fa73c1cd697f52ed"
SEED = 202601


def get_git_revision() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:
        return "unknown"


def run_factorial_ablation():
    print(f"\n[Initializing LFM 2.6B for Factorial Ablation]")
    llm = llama_cpp.Llama(
        model_path=MODEL_PATH,
        n_ctx=4096,
        n_gpu_layers=-1,
        main_gpu=0,
        offload_kqv=True,
        seed=SEED,
        verbose=False,
    )

    handler = llm.chat_handler or llm._chat_handlers.get(llm.chat_format)
    formatter = handler.__closure__[0].cell_contents

    tokenizer = create_token_counter({"type": "llama_cpp", "model_path": MODEL_PATH})

    raw_out_path = ROOT / "results/raw/stage1_lfm25_26b_factorial.jsonl"
    raw_out_path.parent.mkdir(parents=True, exist_ok=True)

    completed_keys = set()
    if raw_out_path.exists():
        with raw_out_path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        completed_keys.add(json.loads(line)["request_key"])
                    except Exception:
                        pass
        print(f"Resuming: {len(completed_keys)} records already completed.")

    raw_file = raw_out_path.open("a", encoding="utf-8")

    arms = [
        {"arm": "default_80", "prefill": False, "max_tokens": 80},
        {"arm": "default_512", "prefill": False, "max_tokens": 512},
        {"arm": "prefill_80", "prefill": True, "max_tokens": 80},
        {"arm": "prefill_512", "prefill": True, "max_tokens": 512},
    ]

    total_records = 0
    all_records = []

    print(f"Starting execution across 100 paired examples...")
    start_total = time.perf_counter()

    for num_sources in [5, 20]:
        examples = generate_citation_examples(seed=SEED, count=100, num_sources=num_sources, task_type="single_hop")
        print(f"\n--- Loaded {len(examples)} examples for num_sources={num_sources} ---")

        for eg_idx, eg in enumerate(examples):
            if (eg_idx + 1) % 25 == 0:
                print(f"  Progress num_sources={num_sources}: example {eg_idx + 1}/100...")

            for condition in ["structured", "uuid"]:
                mapping = render_identifiers(eg.sources, condition, SEED, tokenizer)
                rendered = render_prompt(eg, mapping, require_citations=True)

                # Render canonical prompt via Jinja chat formatter
                rendered_chat = formatter(messages=[{"role": "user", "content": rendered.prompt}])
                clean_prompt = rendered_chat.prompt
                for bos in ("<|startoftext|>", "<s>", "<bos>"):
                    if clean_prompt.startswith(bos):
                        clean_prompt = clean_prompt[len(bos):]
                        break

                for arm_cfg in arms:
                    arm_name = arm_cfg["arm"]
                    max_tok = arm_cfg["max_tokens"]
                    use_prefill = arm_cfg["prefill"]

                    req_key = hashlib.sha256(
                        f"{SEED}:{num_sources}:{eg.example_id}:{condition}:{arm_name}".encode()
                    ).hexdigest()[:20]

                    if req_key in completed_keys:
                        continue

                    t0 = time.perf_counter()
                    if use_prefill:
                        # Append closed thinking to Jinja prompt
                        if clean_prompt.endswith("<think>"):
                            prompt_str = clean_prompt + "\n</think>\n"
                        else:
                            prompt_str = clean_prompt + "<think>\n</think>\n"
                        resp = llm(
                            prompt_str,
                            max_tokens=max_tok,
                            temperature=0.0,
                            seed=SEED,
                            stop=rendered_chat.stop,
                        )
                        raw_text = str(resp["choices"][0]["text"] or "").strip()
                        finish_reason = resp["choices"][0]["finish_reason"]
                        usage = resp.get("usage", {})
                    else:
                        resp = llm.create_chat_completion(
                            messages=[{"role": "user", "content": rendered.prompt}],
                            max_tokens=max_tok,
                            temperature=0.0,
                            seed=SEED,
                        )
                        raw_text = str(resp["choices"][0]["message"]["content"] or "").strip()
                        finish_reason = resp["choices"][0]["finish_reason"]
                        usage = resp.get("usage", {})

                    latency = time.perf_counter() - t0
                    out_tokens = usage.get("completion_tokens", len(raw_text.split()))
                    hit_cap = (finish_reason == "length") or (out_tokens >= max_tok)

                    # Evaluate output
                    ev = evaluate_output(rendered, raw_text)

                    # Semantic / content match
                    exp_ans = rendered.expected_answer.strip().lower()
                    answer_content_match = exp_ans in raw_text.lower()

                    rec = {
                        "request_key": req_key,
                        "example_id": eg.example_id,
                        "example_index": eg_idx,
                        "num_sources": num_sources,
                        "condition": condition,
                        "arm": arm_name,
                        "max_tokens": max_tok,
                        "use_prefill": use_prefill,
                        "expected_answer": rendered.expected_answer,
                        "parsed_answer": ev["parsed_answer"],
                        "answer_content_match": bool(answer_content_match),
                        "strict_answer_accuracy": bool(ev["answer_correct"]),
                        "relaxed_binding_recall": ev.get("citation_recall") or 0.0,
                        "strict_citation_syntax": float(ev.get("citation_exact_match") or 0.0),
                        "has_citation_field": bool(ev.get("failure_category") != "missing_citation_field"),
                        "malformed_ids_count": len(ev.get("malformed_ids", [])),
                        "invalid_ids_count": len(ev.get("invalid_ids", [])),
                        "hit_generation_cap": bool(hit_cap),
                        "output_tokens": out_tokens,
                        "latency_seconds": latency,
                        "raw_output": raw_text,
                    }

                    raw_file.write(json.dumps(rec) + "\n")
                    raw_file.flush()
                    completed_keys.add(req_key)
                    total_records += 1

    raw_file.close()
    elapsed = time.perf_counter() - start_total
    print(f"\nAll generations complete! Total time: {elapsed:.2f}s ({elapsed/60:.2f}m).")

    # Now analyze and build processed summary
    summarize_factorial_results(raw_out_path)


def summarize_factorial_results(raw_path: Path):
    with raw_path.open("r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]

    print(f"\nAnalyzing and rescoring {len(records)} records from {raw_path}...")

    # Load canonical example mappings for exact Stage 1 rescoring
    tokenizer = create_token_counter({"type": "llama_cpp", "model_path": MODEL_PATH})
    eg_by_key = {}
    for n in [5, 20]:
        for eg in generate_citation_examples(seed=SEED, count=100, num_sources=n, task_type="single_hop"):
            for cond in ["structured", "uuid"]:
                mapping = render_identifiers(eg.sources, cond, SEED, tokenizer)
                eg_by_key[(n, cond, eg.example_id)] = (eg, mapping)

    # Group by (num_sources, condition, arm)
    from collections import defaultdict
    groups = defaultdict(list)
    for r in records:
        eg, mapping = eg_by_key[(r["num_sources"], r["condition"], r["example_id"])]
        exp_norm = normalize(eg.answer)
        pred_ans_norm = normalize(r["parsed_answer"])
        content_match = bool(exp_norm) and exp_norm in pred_ans_norm

        pred_sources = relaxed_sources(r["raw_output"], mapping.citation_by_source)
        exp_sources = set(eg.relevant_sources)
        relaxed_recall = len(pred_sources & exp_sources) / len(exp_sources) if exp_sources else 1.0

        r_rescored = {
            **r,
            "answer_content_match": content_match,
            "relaxed_binding_recall": relaxed_recall,
            "has_citation_field": bool(citation_field(r["raw_output"])),
        }
        groups[(r["num_sources"], r["condition"], r["arm"])].append(r_rescored)

    cells = []
    for (num_sources, condition, arm), recs in sorted(groups.items()):
        n = len(recs)
        content_acc = sum(1 for r in recs if r["answer_content_match"]) / n
        strict_acc = sum(1 for r in recs if r["strict_answer_accuracy"]) / n
        relaxed_rec = sum(r["relaxed_binding_recall"] for r in recs) / n
        strict_cit = sum(r["strict_citation_syntax"] for r in recs) / n
        trunc_rate = sum(1 for r in recs if r["hit_generation_cap"]) / n
        mean_tokens = sum(r["output_tokens"] for r in recs) / n
        has_cit_field = sum(1 for r in recs if r["has_citation_field"]) / n

        cells.append({
            "num_sources": num_sources,
            "condition": condition,
            "arm": arm,
            "n": n,
            "answer_content_accuracy": content_acc,
            "strict_answer_accuracy": strict_acc,
            "relaxed_binding_recall": relaxed_rec,
            "strict_citation_syntax": strict_cit,
            "truncation_rate": trunc_rate,
            "has_citation_field_rate": has_cit_field,
            "mean_output_tokens": mean_tokens,
        })

    summary = {
        "model": MODEL_NAME,
        "model_revision": MODEL_REVISION,
        "gguf_sha256": GGUF_SHA256,
        "llama_cpp_version": llama_cpp.__version__,
        "git_revision": get_git_revision(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "seed": SEED,
        "total_records": len(records),
        "cells": cells,
    }

    out_json = ROOT / "results/processed/stage1_lfm25_26b_factorial.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Saved processed summary to {out_json}")

    # Print markdown table
    print("\n" + "=" * 110)
    print("STAGE 1 FACTORIAL ABLATION: LFM 2.5-2.6B (RE-SCORED WITH CANONICAL METRICS)")
    print("=" * 110)
    print(f"{'Sources':<8} {'Cond':<11} {'Arm':<15} {'ContentAcc':<11} {'StrictAns':<10} {'RelaxRecall':<12} {'StrictCit':<10} {'TruncRate':<10} {'MeanTok':<8}")
    print("-" * 110)
    for c in cells:
        print(f"{c['num_sources']:<8} {c['condition']:<11} {c['arm']:<15} {c['answer_content_accuracy']*100:>9.1f}% {c['strict_answer_accuracy']*100:>9.1f}% {c['relaxed_binding_recall']*100:>11.1f}% {c['strict_citation_syntax']*100:>9.1f}% {c['truncation_rate']*100:>9.1f}% {c['mean_output_tokens']:>8.1f}")
    print("=" * 110)


if __name__ == "__main__":
    run_factorial_ablation()
