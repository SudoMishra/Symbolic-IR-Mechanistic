#!/usr/bin/env python3
"""Diagnostic harness to test LFM 1.2B and LFM 2.6B on 3-5 samples per experiment.

Tests:
1. Stage 1: Single-hop Citations (5 sources, 20 sources; numeric vs UUID)
2. Stage 3: MuSiQue Multi-hop QA (15 sources; numeric vs UUID)
3. Stage 5: Scratchpad Reasoning (Arithmetic, Temporal, Constraint; Pass 1 & Pass 2 vs Direct)
4. LongProc: Theory of Mind Tracking (2k output)
5. Stage 8: PII Entity Resolution (Raw vs Untyped vs Typed)
"""

from __future__ import annotations

import dataclasses
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from symbolic_ir.data.citation import generate_citation_examples
from symbolic_ir.data.musique import load_musique_examples
from symbolic_ir.data.pii import generate_pii_examples
from symbolic_ir.data.reasoning import _arithmetic, _constraint, _distractors, _temporal
from symbolic_ir.evaluation import evaluate_output
from symbolic_ir.evaluation.longproc import evaluate_tom_trace
from symbolic_ir.evaluation.parser import parse_output
from symbolic_ir.identifiers import render_identifiers
from symbolic_ir.prompts import render_prompt
from symbolic_ir.schema import CanonicalExample, GenerationRequest, Source
from symbolic_ir.tokenization import create_token_counter

try:
    import llama_cpp
except ImportError:
    raise RuntimeError("llama_cpp required")


def get_llm(model_path: str, n_ctx: int = 4096):
    print(f"\n[Loading Model: {model_path} with n_ctx={n_ctx}]")
    llm = llama_cpp.Llama(
        model_path=model_path,
        n_ctx=n_ctx,
        n_gpu_layers=-1,
        main_gpu=0,
        offload_kqv=True,
        seed=202601,
        verbose=False,
    )
    return llm


def generate_chat(llm, prompt: str, max_tokens: int = 150, system_prompt: str | None = None):
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    res = llm.create_chat_completion(
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.0,
        seed=202601,
    )
    return res["choices"][0]["message"]["content"] or ""


def generate_raw_assistant(llm, prompt: str, assistant_prefill: str = "", max_tokens: int = 150):
    raw = f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n{assistant_prefill}"
    res = llm(
        raw,
        max_tokens=max_tokens,
        temperature=0.0,
        seed=202601,
    )
    return (assistant_prefill + (res["choices"][0]["text"] or "")).strip()


def run_diagnostics(models_to_test: list[str]):
    results = {}

    for model_path in models_to_test:
        model_name = Path(model_path).stem
        print(f"\n{'='*80}\nSTARTING DIAGNOSTIC FOR {model_name}\n{'='*80}")
        is_26b = "2.6B" in model_path
        llm = get_llm(model_path, n_ctx=8192 if "longproc" in sys.argv else 4096)

        model_results = {
            "stage1_citations": [],
            "stage3_musique": [],
            "stage5_reasoning": [],
            "longproc": [],
            "stage8_pii": [],
        }

        # -------------------------------------------------------------
        # 1. Stage 1: Single-hop Citations (5 and 20 sources)
        # -------------------------------------------------------------
        print("\n--- Running Stage 1: Single-Hop Citations (5 and 20 sources) ---")
        tokenizer = create_token_counter({"type": "llama_cpp", "model_path": model_path})

        for n_src in [5, 20]:
            st1_examples = generate_citation_examples(seed=202601, count=3, num_sources=n_src, task_type="single_hop")
            for i, eg in enumerate(st1_examples):
                for cond in ["structured", "uuid"]:
                    mapping = render_identifiers(eg.sources, cond, 202601, tokenizer)
                    rendered = render_prompt(eg, mapping, require_citations=True)
                    
                    # Test standard vs prefilled
                    out_default = generate_chat(llm, rendered.prompt, max_tokens=100)
                    eval_default = evaluate_output(rendered, out_default)

                    # For 2.6B, test with prefill closed think tag
                    out_prefill = None
                    eval_prefill = None
                    if is_26b:
                        out_prefill = generate_raw_assistant(llm, rendered.prompt, assistant_prefill="<think>\n</think>\n", max_tokens=100)
                        eval_prefill = evaluate_output(rendered, out_prefill)

                    model_results["stage1_citations"].append({
                        "num_sources": n_src,
                        "example_idx": i,
                        "condition": cond,
                        "expected_answer": rendered.expected_answer,
                        "allowed_citations": list(rendered.mapping.citation_by_source.values()),
                        "output_default": out_default,
                        "eval_default": {
                            "answer_correct": eval_default["answer_correct"],
                            "citation_recall": eval_default.get("citation_recall"),
                            "citation_precision": eval_default.get("citation_precision"),
                            "malformed_ids": eval_default["malformed_ids"],
                            "invalid_ids": eval_default["invalid_ids"],
                        },
                        "output_prefill": out_prefill,
                        "eval_prefill": {
                            "answer_correct": eval_prefill["answer_correct"],
                            "citation_recall": eval_prefill.get("citation_recall"),
                            "citation_precision": eval_prefill.get("citation_precision"),
                        } if eval_prefill else None,
                    })
                    print(f"[{model_name}] St1 (N={n_src}) Ex{i} {cond}: ans_corr={eval_default['answer_correct']}, recall={eval_default.get('citation_recall')}, out={repr(out_default[:60])}")
                    if is_26b:
                        print(f"       with prefill: ans_corr={eval_prefill['answer_correct']}, recall={eval_prefill.get('citation_recall')}, out={repr(out_prefill[:60])}")

        # -------------------------------------------------------------
        # 2. Stage 3: MuSiQue Multi-hop (3 examples)
        # -------------------------------------------------------------
        print("\n--- Running Stage 3: MuSiQue Multi-Hop (3 examples) ---")
        musique_config = {
            "data_path": "data/musique/musique_ans_v1.0_dev.jsonl",
            "selection_path": "configs/musique/musique_confirmatory_heldout_100.json",
            "num_sources": 15,
            "count": 3,
            "skip_insufficient_sources": True,
        }
        musique_examples = load_musique_examples(musique_config, seed=202601)

        for i, eg in enumerate(musique_examples):
            for cond in ["structured", "uuid"]:
                mapping = render_identifiers(eg.sources, cond, 202601, tokenizer)
                rendered = render_prompt(eg, mapping, require_citations=True)

                if is_26b:
                    out = generate_raw_assistant(llm, rendered.prompt, assistant_prefill="<think>\n</think>\n", max_tokens=120)
                else:
                    out = generate_chat(llm, rendered.prompt, max_tokens=120)

                ev = evaluate_output(rendered, out)
                model_results["stage3_musique"].append({
                    "example_idx": i,
                    "example_id": eg.example_id,
                    "condition": cond,
                    "expected_answer": rendered.expected_answer,
                    "output": out,
                    "answer_f1": ev["answer_f1"],
                    "citation_recall": ev.get("citation_recall"),
                    "malformed": ev["malformed_ids"],
                    "invalid": ev["invalid_ids"],
                })
                print(f"[{model_name}] MuSiQue Ex{i} {cond}: ans_f1={ev['answer_f1']:.2f}, recall={ev.get('citation_recall')}, malformed={len(ev['malformed_ids'])}, out={repr(out[:60])}")

        # -------------------------------------------------------------
        # 3. Stage 5: Scratchpad Reasoning (3 tasks: arithmetic, temporal, constraint)
        # -------------------------------------------------------------
        print("\n--- Running Stage 5: Scratchpad Reasoning (3 tasks) ---")
        from symbolic_ir.randomness import rng_for
        rng = rng_for(202601, "stage5_diag")

        tasks = [
            ("arithmetic", _arithmetic(rng)),
            ("temporal", _temporal(rng)),
            ("constraint", _constraint(rng)),
        ]

        from scripts.run_stage5 import final_prompt, reasoning_prompt

        for task_name, (facts, question, answer, needed) in tasks:
            distractors = _distractors(rng, 15 - len(facts))
            sources = facts + distractors
            rng.shuffle(sources)
            can_eg = CanonicalExample(
                example_id=f"diag-{task_name}",
                seed=202601,
                task_type=task_name,
                sources=tuple(sources),
                question=question,
                answer=answer,
                relevant_sources=tuple(f.key for f in facts),
                claims=(answer,),
                entities={},
            )

            for cond in ["structured", "uuid"]:
                mapping = render_identifiers(can_eg.sources, cond, 202601, tokenizer)
                rendered = render_prompt(can_eg, mapping, require_citations=True)

                # Pass 1: Scratchpad (budget = 256 tokens)
                p1_prompt = reasoning_prompt(rendered, budget=256)
                if is_26b:
                    scratchpad = generate_raw_assistant(llm, p1_prompt, assistant_prefill="<think>\n</think>\n", max_tokens=256)
                else:
                    scratchpad = generate_chat(llm, p1_prompt, max_tokens=256)

                # Pass 2: Final answer from scratchpad
                p2_prompt = final_prompt(rendered, scratchpad)
                if is_26b:
                    final_out = generate_raw_assistant(llm, p2_prompt, assistant_prefill="<think>\n</think>\n", max_tokens=100)
                else:
                    final_out = generate_chat(llm, p2_prompt, max_tokens=100)

                ev = evaluate_output(rendered, final_out)

                # Direct single-pass without scratchpad (diagnostic control)
                if is_26b:
                    direct_out = generate_raw_assistant(llm, rendered.prompt, assistant_prefill="<think>\n</think>\n", max_tokens=100)
                else:
                    direct_out = generate_chat(llm, rendered.prompt, max_tokens=100)
                ev_direct = evaluate_output(rendered, direct_out)

                model_results["stage5_reasoning"].append({
                    "task": task_name,
                    "condition": cond,
                    "expected_answer": answer,
                    "scratchpad": scratchpad,
                    "final_output": final_out,
                    "exact_match": ev["answer_correct"],
                    "binding_recall": ev.get("citation_recall"),
                    "direct_output": direct_out,
                    "direct_exact_match": ev_direct["answer_correct"],
                    "direct_binding_recall": ev_direct.get("citation_recall"),
                })
                print(f"[{model_name}] Stage5 {task_name} {cond}: 2-pass exact={ev['answer_correct']}, direct exact={ev_direct['answer_correct']}")
                print(f"       Scratchpad preview: {repr(scratchpad[:120])}")
                print(f"       Final out: {repr(final_out)}")
                print(f"       Direct out: {repr(direct_out)}")

        # -------------------------------------------------------------
        # 4. LongProc: Theory of Mind (3 examples)
        # -------------------------------------------------------------
        print("\n--- Running LongProc: ToM Tracking (3 examples) ---")
        longproc_data_path = Path("data/longproc/tom_tracking/tom_tracking_2k.json")
        if longproc_data_path.exists():
            import yaml
            prompts_yaml = yaml.safe_load(Path("data/longproc/tom_tracking/prompts.yaml").read_text(encoding="utf-8"))
            user_template = str(prompts_yaml["USER_PROMPT"])
            lp_data = json.loads(longproc_data_path.read_text(encoding="utf-8"))
            
            for idx in [0, 7, 12]:
                item = lp_data[idx]
                prompt = user_template.format(story=item["story"], question=item["question"])
                ref = str(item["solution"])
                
                # Let's generate up to 1024 tokens to see trace
                if is_26b:
                    out = generate_raw_assistant(llm, prompt, assistant_prefill="<think>\n</think>\n", max_tokens=1024)
                else:
                    out = generate_chat(llm, prompt, max_tokens=1024)

                ev_tom = evaluate_tom_trace(out, ref)
                model_results["longproc"].append({
                    "index": idx,
                    "steps_predicted": ev_tom["predicted_steps"],
                    "steps_reference": ev_tom["reference_steps"],
                    "partial_accuracy": ev_tom["partial_accuracy"],
                    "final_answer_accuracy": ev_tom["final_answer_accuracy"],
                    "first_error": ev_tom["error_report"],
                    "output_preview": out[:300],
                })
                print(f"[{model_name}] LongProc idx {idx}: steps={ev_tom['predicted_steps']}/{ev_tom['reference_steps']}, partial={ev_tom['partial_accuracy']:.3f}, final_acc={ev_tom['final_answer_accuracy']}")
                print(f"       First error: {ev_tom['error_report']}")

        # -------------------------------------------------------------
        # 5. Stage 8: PII Entity Resolution (3 examples)
        # -------------------------------------------------------------
        print("\n--- Running Stage 8: PII Resolution (3 examples) ---")
        pii_examples = generate_pii_examples(seed=202601, count=3, num_sources=8)

        for i, eg in enumerate(pii_examples):
            for cond in ["raw", "untyped", "typed"]:
                mapping = render_identifiers(eg.sources, "structured", 202601, tokenizer)
                # Override mapping condition to trigger _canonicalize_pii
                mapping_with_cond = dataclasses.replace(mapping, condition=cond)
                rendered = render_prompt(eg, mapping_with_cond, require_citations=True)

                if is_26b:
                    out = generate_raw_assistant(llm, rendered.prompt, assistant_prefill="<think>\n</think>\n", max_tokens=100)
                else:
                    out = generate_chat(llm, rendered.prompt, max_tokens=100)

                ev = evaluate_output(rendered, out)
                model_results["stage8_pii"].append({
                    "example_idx": i,
                    "condition": cond,
                    "expected_answer": rendered.expected_answer,
                    "output": out,
                    "exact_match": ev["answer_correct"],
                    "pii_leaks": ev["raw_pii_leakage_rate"],
                })
                print(f"[{model_name}] Stage8 Ex{i} {cond}: exact={ev['answer_correct']}, leaks={ev['raw_pii_leakage_rate']}, out={repr(out[:60])}")

        results[model_name] = model_results
        # Delete llm to free VRAM for next model
        del llm
        import gc
        gc.collect()

    out_file = Path("results/analysis/lfm_diagnostics_micro_eval.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nSaved all diagnostic results to {out_file}")


if __name__ == "__main__":
    models = [
        "models/lfm2.5-1.2b-instruct-q4_k_m.gguf",
        "models/LFM2.5-2.6B-Q4_K_M.gguf",
    ]
    run_diagnostics(models)
