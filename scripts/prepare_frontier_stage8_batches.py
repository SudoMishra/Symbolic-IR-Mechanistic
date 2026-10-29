"""Prepare and validate paired Phase 4 Stage 8 PII entity-canonicalization batches offline.

Creates 4 blocks of 125 semantic cases each (500 requests per block).
Conditions: raw, random_masked, untyped, typed.
Ensures representations remain paired within blocks.
Outputs ready-to-submit batch payloads for:
- OpenAI gpt-6.1-sol (effort=low)
- Anthropic claude-sonnet-5-5 (between_tools, effort=low)
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from symbolic_ir.data.pii import generate_pii_examples  # noqa: E402
from symbolic_ir.identifiers import render_identifiers  # noqa: E402
from symbolic_ir.inference.batch import AnthropicBatchManager, OpenAIBatchManager  # noqa: E402
from symbolic_ir.prompts import render_prompt  # noqa: E402
from symbolic_ir.schema import IdentifierMapping  # noqa: E402
from symbolic_ir.tokenization import create_token_counter  # noqa: E402


def build_stage8_matrix(seed: int = 202618) -> list[dict[str, Any]]:
    tokenizer = create_token_counter({"type": "regex"})
    cases = []
    for num_sources in [15, 20]:
        examples = generate_pii_examples(
            seed=seed,
            count=250,
            num_sources=num_sources,
            task_type="account_resolution",
            long_context=True,
            filler_words=100,
        )
        for ex in examples:
            cases.append((ex, num_sources))

    assert len(cases) == 500, f"Expected 500 semantic cases, got {len(cases)}"

    matrix_by_case = []
    for case_idx, (ex, num_sources) in enumerate(cases):
        fixed = render_identifiers(ex.sources, "structured", seed, tokenizer)
        representations = []
        for cond in ["raw", "random_masked", "untyped", "typed"]:
            mapping = IdentifierMapping(
                condition=cond,
                display_by_source=fixed.display_by_source,
                citation_by_source=fixed.citation_by_source,
                token_lengths=fixed.token_lengths,
            )
            rendered = render_prompt(ex, mapping, require_citations=False)
            representations.append({
                "case_idx": case_idx,
                "example_id": ex.example_id,
                "num_sources": num_sources,
                "condition": cond,
                "prompt": rendered.prompt,
                "expected_answer": rendered.expected_answer or ex.answer,
                "protected_values": list(rendered.protected_values),
            })
        matrix_by_case.append(representations)
    return matrix_by_case


def main() -> int:
    seed = 202618
    print("Building Stage 8 PII matrix...")
    matrix_by_case = build_stage8_matrix(seed)
    assert len(matrix_by_case) == 500

    out_dir = ROOT / "results/batches/prepared/stage8_500"
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {}
    block_size = 125

    for block_idx in range(4):
        block_cases = matrix_by_case[block_idx * block_size : (block_idx + 1) * block_size]
        assert len(block_cases) == 125

        block_items = []
        for reps in block_cases:
            block_items.extend(reps)
        assert len(block_items) == 500, f"Block {block_idx} has {len(block_items)} requests instead of 500"

        # 1. OpenAI Sol
        sol_items = []
        for it in block_items:
            clean_eid = it['example_id'].replace('pii-', '')
            cid = f"s8_sol_b{block_idx}_{clean_eid}_{it['num_sources']}_{it['condition']}"
            item = OpenAIBatchManager.build_item(
                custom_id=cid,
                prompt=it["prompt"],
                model="gpt-6.1-sol",
                max_output_tokens=64,
                reasoning_effort="low",
                temperature=None,
            )
            sol_items.append(item)
            manifest[cid] = copy.deepcopy(it)

        sol_file = out_dir / f"openai_sol_block_{block_idx}.jsonl"
        sol_file.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in sol_items) + "\n", encoding="utf-8")

        # 2. Anthropic Sonnet
        sonnet_items = []
        for it in block_items:
            clean_eid = it['example_id'].replace('pii-', '')
            cid = f"s8_son_b{block_idx}_{clean_eid}_{it['num_sources']}_{it['condition']}"
            item = AnthropicBatchManager.build_item(
                custom_id=cid,
                prompt=it["prompt"],
                model="claude-sonnet-5-5",
                max_tokens=64,
                thinking_type="between_tools",
                effort="low",
            )
            sonnet_items.append(item)
            manifest[cid] = copy.deepcopy(it)

        sonnet_file = out_dir / f"anthropic_sonnet_block_{block_idx}.json"
        sonnet_file.write_text(json.dumps(sonnet_items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        print(f"Block {block_idx}: 125 semantic cases, 500 requests per model generated and paired.")

    manifest_file = out_dir / "manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Total Stage 8 manifest entries: {len(manifest)}. Output saved to {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
