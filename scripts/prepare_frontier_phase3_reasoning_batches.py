"""Prepare Phase 3 Reasoning Ablation batches offline.

Uses a fixed stratified subset of 100 MuSiQue questions (2/3/4 hops).
Adds:
- Luna with reasoning.effort="medium", max_output_tokens=1024
- Sonnet with adaptive thinking at effort low, max_output_tokens=1024
Calls per model: 100 questions x 2 source counts (15, 20) x 2 formats (numeric, uuid) = 400 requests.
"""

from __future__ import annotations

import copy
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from symbolic_ir.data.musique import load_musique_examples  # noqa: E402
from symbolic_ir.identifiers import render_identifiers  # noqa: E402
from symbolic_ir.inference.batch import AnthropicBatchManager, OpenAIBatchManager  # noqa: E402
from symbolic_ir.prompts import render_prompt  # noqa: E402
from symbolic_ir.tokenization import create_token_counter  # noqa: E402


def select_stratified_100_questions() -> list[str]:
    data_path = ROOT / "data/musique/musique_ans_v1.0_dev.jsonl"
    balanced_500_path = ROOT / "configs/musique/musique_balanced_500.json"
    records = [json.loads(line) for line in data_path.read_text(encoding="utf-8").splitlines() if line]
    by_id = {str(r["id"]): r for r in records}

    selected_500 = json.loads(balanced_500_path.read_text(encoding="utf-8"))["ids"]
    by_hop = defaultdict(list)
    for qid in selected_500:
        rec = by_id[str(qid)]
        hops = len(rec.get("question_decomposition", [])) or 2
        by_hop[hops].append(str(qid))

    # Stratified sample: 50 2-hop, 35 3-hop, 15 4-hop
    sampled = []
    sampled.extend(by_hop[2][:50])
    sampled.extend(by_hop[3][:35])
    sampled.extend(by_hop[4][:15])
    if len(sampled) < 100:
        remaining = [qid for qid in selected_500 if qid not in sampled]
        sampled.extend(remaining[: 100 - len(sampled)])
    return sampled[:100]


def main() -> int:
    seed = 202620
    qids = select_stratified_100_questions()
    assert len(qids) == 100

    tokenizer = create_token_counter({"type": "regex"})
    matrix_by_qid = defaultdict(list)

    for num_sources in [15, 20]:
        config = {
            "data_path": str(ROOT / "data/musique/musique_ans_v1.0_dev.jsonl"),
            "selection_path": str(ROOT / "configs/musique/musique_balanced_500.json"),
            "num_sources": num_sources,
            "count": 500,
        }
        examples = [ex for ex in load_musique_examples(config, seed) if ex.example_id.replace("musique-", "") in qids]
        for ex in examples:
            for condition in ["numeric", "uuid"]:
                mapping = render_identifiers(ex.sources, condition, seed, tokenizer)
                rendered = render_prompt(ex, mapping, require_citations=True)
                expected_citations = [mapping.citation_by_source[k] for k in ex.relevant_sources]
                matrix_by_qid[ex.example_id].append({
                    "example_id": ex.example_id,
                    "num_sources": num_sources,
                    "condition": condition,
                    "prompt": rendered.prompt,
                    "expected_answer": rendered.expected_answer or ex.answer,
                    "expected_citations": expected_citations,
                })

    out_dir = ROOT / "results/batches/prepared/reasoning_ablation_100"
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {}
    items_all = [it for qid in matrix_by_qid for it in matrix_by_qid[qid]]
    assert len(items_all) == 400, f"Expected 400 requests, got {len(items_all)}"

    # 1. OpenAI Luna reasoning.effort="medium"
    luna_items = []
    for it in items_all:
        clean_eid = it['example_id'].replace('musique-', '')
        cid = f"r_luna_{clean_eid}_{it['num_sources']}_{it['condition']}"
        item = OpenAIBatchManager.build_item(
            custom_id=cid,
            prompt=it["prompt"],
            model="gpt-6-luna",
            max_output_tokens=1024,
            reasoning_effort="medium",
            temperature=None,
        )
        luna_items.append(item)
        manifest[cid] = copy.deepcopy(it)

    luna_file = out_dir / "openai_luna_medium.jsonl"
    luna_file.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in luna_items) + "\n", encoding="utf-8")

    # 2. Anthropic Sonnet thinking={"type": "adaptive"}, effort="low"
    sonnet_items = []
    for it in items_all:
        clean_eid = it['example_id'].replace('musique-', '')
        cid = f"r_son_{clean_eid}_{it['num_sources']}_{it['condition']}"
        item = AnthropicBatchManager.build_item(
            custom_id=cid,
            prompt=it["prompt"],
            model="claude-sonnet-5-5",
            max_tokens=1024,
            thinking_type="adaptive",
            effort="low",
        )
        sonnet_items.append(item)
        manifest[cid] = copy.deepcopy(it)

    sonnet_file = out_dir / "anthropic_sonnet_adaptive.json"
    sonnet_file.write_text(json.dumps(sonnet_items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    manifest_file = out_dir / "manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Phase 3 Reasoning Ablation batches generated: 400 calls per model. Output saved to {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
