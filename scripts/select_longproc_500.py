#!/usr/bin/env python3
"""Assemble balanced 500-item procedural reasoning manifest across LongProc splits."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    items = []

    # 1. ToM Tracking 2k (200 items)
    tom_2k_path = ROOT / "data/longproc/tom_tracking/tom_tracking_2k.json"
    tom_2k_data = json.loads(tom_2k_path.read_text(encoding="utf-8"))
    for idx, ex in enumerate(tom_2k_data):
        items.append({
            "task": "tom_tracking_2k",
            "index": idx,
            "source_file": "data/longproc/tom_tracking/tom_tracking_2k.json",
            "prompt_file": "data/longproc/tom_tracking/prompts.yaml",
            "story": ex["story"],
            "question": ex["question"],
            "solution": ex["solution"],
            "answer": ex["answer"],
        })

    # 2. ToM Tracking 0.5k (100 items)
    tom_05k_path = ROOT / "data/longproc/tom_tracking/tom_tracking_0.5k.json"
    tom_05k_data = json.loads(tom_05k_path.read_text(encoding="utf-8"))[:100]
    for idx, ex in enumerate(tom_05k_data):
        items.append({
            "task": "tom_tracking_0.5k",
            "index": idx,
            "source_file": "data/longproc/tom_tracking/tom_tracking_0.5k.json",
            "prompt_file": "data/longproc/tom_tracking/prompts.yaml",
            "story": ex["story"],
            "question": ex["question"],
            "solution": ex["solution"],
            "answer": ex["answer"],
        })

    # 3. Path Traversal 2k (100 items)
    path_2k_path = ROOT / "data/longproc/path_traversal/path_traversal_2k.json"
    path_2k_data = json.loads(path_2k_path.read_text(encoding="utf-8"))[:100]
    for idx, ex in enumerate(path_2k_data):
        items.append({
            "task": "path_traversal_2k",
            "index": idx,
            "source_file": "data/longproc/path_traversal/path_traversal_2k.json",
            "prompt_file": "data/longproc/path_traversal/prompts.yaml",
            "context": ex["context_nl"],
            "question": ex["question_nl"],
            "solution": ex["answer_nl"],
            "answer": ex["answer_repr"],
        })

    # 4. Countdown 2k (100 items)
    count_2k_path = ROOT / "data/longproc/countdown/countdown_2k.json"
    count_2k_data = json.loads(count_2k_path.read_text(encoding="utf-8"))[:100]
    for idx, ex in enumerate(count_2k_data):
        items.append({
            "task": "countdown_2k",
            "index": idx,
            "source_file": "data/longproc/countdown/countdown_2k.json",
            "prompt_file": "data/longproc/countdown/prompts.yaml",
            "nums": ex["nums"],
            "target": ex["target"],
            "solution": ex["solution_text"],
            "answer": ex["solution"],
        })

    assert len(items) == 500, f"Expected 500 items, got {len(items)}"
    out_path = ROOT / "configs/longproc/longproc_500.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(items, indent=2), encoding="utf-8")
    print(f"Wrote 500 LongProc items to {out_path}")

if __name__ == "__main__":
    main()
