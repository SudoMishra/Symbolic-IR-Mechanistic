#!/usr/bin/env python3
"""Select a held-out MuSiQue cohort valid under every tested GGUF tokenizer."""

from __future__ import annotations

import argparse
import gc
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from symbolic_ir.data.musique import load_musique_examples  # noqa: E402
from symbolic_ir.identifiers import render_identifiers  # noqa: E402
from symbolic_ir.prompts import render_prompt  # noqa: E402
from symbolic_ir.randomness import derive_seed  # noqa: E402
from symbolic_ir.tokenization import create_token_counter  # noqa: E402


MODELS = {
    "qwen25_15b": "models/qwen2.5-1.5b-instruct-q4_k_m.gguf",
    "lfm25_12b": "models/lfm2.5-1.2b-instruct-q4_k_m.gguf",
    "gemma4_e2b": "models/gemma-4-e2b-it-q4_0.gguf",
    "gemma4_e4b": "models/gemma-4-e4b-it-q4_0.gguf",
    "tiny_aya": "models/tiny-aya-global-q4_k_m.gguf",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/musique/musique_ans_v1.0_dev.jsonl")
    parser.add_argument("--exclude", default="configs/musique/musique_balanced_100.json")
    parser.add_argument("--output", default="configs/musique/musique_confirmatory_heldout_100.json")
    parser.add_argument("--seed", type=int, default=202603)
    parser.add_argument("--min-tokens", type=int, default=2000)
    parser.add_argument("--max-tokens", type=int, default=3700)
    args = parser.parse_args()

    excluded = set(json.loads((ROOT / args.exclude).read_text(encoding="utf-8"))["ids"])
    by_sources = {}
    for num_sources in (15, 20):
        examples = load_musique_examples({
            "data_path": str(ROOT / args.data), "count": 10000,
            "num_sources": num_sources, "skip_insufficient_sources": True,
        }, args.seed)
        by_sources[num_sources] = {
            str(example.metadata["source_id"]): example for example in examples
            if str(example.metadata["source_id"]) not in excluded
        }
    eligible = set(by_sources[15]) & set(by_sources[20])
    lengths: dict[str, dict[str, list[int]]] = {}
    for model_name, relative_path in MODELS.items():
        tokenizer = create_token_counter({"type": "llama_cpp", "model_path": str(ROOT / relative_path)})
        model_lengths: dict[str, list[int]] = {}
        keep = set()
        for example_id in sorted(eligible):
            values = []
            valid = True
            for num_sources in (15, 20):
                example = by_sources[num_sources][example_id]
                for condition in ("numeric", "uuid"):
                    mapping = render_identifiers(example.sources, condition, args.seed, tokenizer)
                    prompt = render_prompt(example, mapping, require_citations=True).prompt
                    count = tokenizer.count(prompt)
                    values.append(count)
                    valid = valid and args.min_tokens <= count <= args.max_tokens
            model_lengths[example_id] = values
            if valid:
                keep.add(example_id)
        lengths[model_name] = model_lengths
        eligible &= keep
        del tokenizer
        gc.collect()
        print(f"{model_name}: {len(eligible)} jointly eligible")

    groups = {hop: [] for hop in (2, 3, 4)}
    for example_id in eligible:
        hop = int(by_sources[20][example_id].metadata["hop_count"])
        if hop in groups:
            groups[hop].append(example_id)
    targets = {2: 34, 3: 33, 4: 33}
    selected = []
    for hop, target in targets.items():
        ordered = sorted(groups[hop], key=lambda value: derive_seed(args.seed, "heldout-cohort", value))
        if len(ordered) < target:
            raise RuntimeError(f"Only {len(ordered)} eligible {hop}-hop examples; need {target}")
        selected.extend(ordered[:target])
    selected.sort(key=lambda value: (int(by_sources[20][value].metadata["hop_count"]), derive_seed(args.seed, "heldout-order", value)))

    tokenizer_stats = {}
    for model_name, model_lengths in lengths.items():
        values = [value for example_id in selected for value in model_lengths[example_id]]
        tokenizer_stats[model_name] = {
            "min": min(values), "mean": round(sum(values) / len(values), 1), "max": max(values),
        }
    manifest = {
        "dataset": "MuSiQue-Answerable v1.0 development split",
        "selection_seed": args.seed,
        "held_out_from": args.exclude,
        "selection_rule": "34 two-hop, 33 three-hop, and 33 four-hop examples; excludes the original cohort; every numeric/UUID prompt at 15/20 sources is 2000-3700 raw tokens under all five native tokenizers",
        "tokenizer_prompt_stats": tokenizer_stats,
        "ids": selected,
    }
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "eligible": len(eligible), "selected": len(selected), "stats": tokenizer_stats}, indent=2))


if __name__ == "__main__":
    main()
