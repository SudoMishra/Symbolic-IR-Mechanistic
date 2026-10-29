"""Prepare and validate paired Phase 2 MuSiQue batches offline.

Creates 4 blocks of 125 semantic questions each (500 requests per block).
Ensures paired numeric and uuid conditions are never split across batches.
Outputs ready-to-submit batch payloads for:
- OpenAI gpt-6-luna
- OpenAI gpt-6.1-sol
- Anthropic claude-haiku-5-5
- Anthropic claude-sonnet-5-5
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from symbolic_ir.data.musique import load_musique_examples  # noqa: E402
from symbolic_ir.identifiers import render_identifiers  # noqa: E402
from symbolic_ir.inference.batch import AnthropicBatchManager, OpenAIBatchManager  # noqa: E402
from symbolic_ir.prompts import render_prompt  # noqa: E402
from symbolic_ir.tokenization import create_token_counter  # noqa: E402


def build_musique_500_matrix(seed: int = 202620) -> list[dict[str, Any]]:
    tokenizer = create_token_counter({"type": "regex"})
    records_by_qid = {}

    for num_sources in [15, 20]:
        config = {
            "data_path": str(ROOT / "data/musique/musique_ans_v1.0_dev.jsonl"),
            "selection_path": str(ROOT / "configs/musique/musique_balanced_500.json"),
            "num_sources": num_sources,
            "count": 500,
        }
        examples = load_musique_examples(config, seed)
        for ex in examples:
            if ex.example_id not in records_by_qid:
                records_by_qid[ex.example_id] = []
            for condition in ["numeric", "uuid"]:
                mapping = render_identifiers(ex.sources, condition, seed, tokenizer)
                rendered = render_prompt(ex, mapping, require_citations=True)
                expected_citations = [mapping.citation_by_source[k] for k in ex.relevant_sources]
                records_by_qid[ex.example_id].append({
                    "example_id": ex.example_id,
                    "num_sources": num_sources,
                    "condition": condition,
                    "prompt": rendered.prompt,
                    "expected_answer": rendered.expected_answer or ex.answer,
                    "expected_citations": expected_citations,
                    "source_order": list(rendered.source_order),
                    "relevant_sources": list(ex.relevant_sources),
                })
    return records_by_qid


def main() -> int:
    seed = 202620
    print("Building MuSiQue 500 matrix...")
    matrix_by_qid = build_musique_500_matrix(seed)
    qids = list(matrix_by_qid.keys())
    assert len(qids) == 500, f"Expected 500 questions, got {len(qids)}"

    for qid, items in matrix_by_qid.items():
        assert len(items) == 4, f"Question {qid} has {len(items)} items instead of 4"
        # Verify 15-num, 15-uuid, 20-num, 20-uuid
        keys = {(item["num_sources"], item["condition"]) for item in items}
        assert keys == {(15, "numeric"), (15, "uuid"), (20, "numeric"), (20, "uuid")}

    out_dir = ROOT / "results/batches/prepared/musique_500"
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {}
    block_size = 125

    for block_idx in range(4):
        block_qids = qids[block_idx * block_size : (block_idx + 1) * block_size]
        assert len(block_qids) == 125

        block_items = []
        for qid in block_qids:
            block_items.extend(matrix_by_qid[qid])
        assert len(block_items) == 500, f"Block {block_idx} has {len(block_items)} requests instead of 500"

        def make_cid(model_key: str, it: dict[str, Any]) -> str:
            clean_eid = it["example_id"].replace("musique-", "")
            if block_idx == 0:
                # Retain exact legacy prefix for block 0 (max len was 59)
                return f"musique500_{model_key}_b0_{it['example_id']}_{it['num_sources']}_{it['condition']}"
            return f"m5_{model_key[:3]}_b{block_idx}_{clean_eid}_{it['num_sources']}_{it['condition']}"

        # 1. OpenAI Luna
        luna_items = []
        for it in block_items:
            cid = make_cid("luna", it)
            item = OpenAIBatchManager.build_item(
                custom_id=cid,
                prompt=it["prompt"],
                model="gpt-6-luna",
                max_output_tokens=512,
                reasoning_effort="none",
                temperature=0.0,
            )
            luna_items.append(item)
            manifest[cid] = copy.deepcopy(it)

        luna_file = out_dir / f"openai_luna_block_{block_idx}.jsonl"
        luna_file.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in luna_items) + "\n", encoding="utf-8")

        # 2. OpenAI Sol
        sol_items = []
        for it in block_items:
            cid = make_cid("sol", it)
            item = OpenAIBatchManager.build_item(
                custom_id=cid,
                prompt=it["prompt"],
                model="gpt-6.1-sol",
                max_output_tokens=512,
                reasoning_effort="low",
                temperature=None,
            )
            sol_items.append(item)
            manifest[cid] = copy.deepcopy(it)

        sol_file = out_dir / f"openai_sol_block_{block_idx}.jsonl"
        sol_file.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in sol_items) + "\n", encoding="utf-8")

        # 3. Anthropic Haiku
        haiku_items = []
        for it in block_items:
            cid = make_cid("haiku", it)
            item = AnthropicBatchManager.build_item(
                custom_id=cid,
                prompt=it["prompt"],
                model="claude-haiku-5-5",
                max_tokens=512,
                thinking_type="disabled",
                effort="low",
            )
            haiku_items.append(item)
            manifest[cid] = copy.deepcopy(it)

        haiku_file = out_dir / f"anthropic_haiku_block_{block_idx}.json"
        haiku_file.write_text(json.dumps(haiku_items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        # 4. Anthropic Sonnet
        sonnet_items = []
        for it in block_items:
            cid = make_cid("sonnet", it)
            item = AnthropicBatchManager.build_item(
                custom_id=cid,
                prompt=it["prompt"],
                model="claude-sonnet-5-5",
                max_tokens=512,
                thinking_type="between_tools",
                effort="low",
            )
            sonnet_items.append(item)
            manifest[cid] = copy.deepcopy(it)

        sonnet_file = out_dir / f"anthropic_sonnet_block_{block_idx}.json"
        sonnet_file.write_text(json.dumps(sonnet_items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        print(f"Block {block_idx}: 125 questions, 500 requests per model generated and paired.")

    manifest_file = out_dir / "manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Total manifest entries: {len(manifest)}. Output saved to {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
