#!/usr/bin/env python3
"""Rescore all raw JSONL experimental runs using the updated parser."""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from symbolic_ir.evaluation.answer import answer_exact_match, answer_f1
from symbolic_ir.evaluation.citation import citation_scores
from symbolic_ir.evaluation.error_taxonomy import classify_failure
from symbolic_ir.evaluation.parser import parse_output


def rescore_record(row: dict[str, Any]) -> dict[str, Any]:
    raw_output = row.get("raw_output", "")
    mapping = row.get("identifier_mapping", {}).get("citation_by_source", {})
    allowed = tuple(mapping.values()) if mapping else ()
    parsed = parse_output(raw_output, allowed)

    row["parsed_answer"] = parsed.answer
    row["parsed_citations"] = list(parsed.citations)

    evaluation = row.get("evaluation")
    if evaluation is not None and isinstance(evaluation, dict):
        expected_ans = evaluation.get("expected_answer", "")
        accepted_ans = evaluation.get("accepted_answers", [expected_ans])
        ans_correct = any(answer_exact_match(parsed.answer, cand) for cand in accepted_ans)
        ans_f1 = answer_f1(parsed.answer, accepted_ans)

        evaluation["parsed_answer"] = parsed.answer
        evaluation["parsed_citations"] = list(parsed.citations)
        evaluation["answer_correct"] = ans_correct
        evaluation["answer_f1"] = ans_f1
        evaluation["strict_format"] = parsed.strict_format

        require_cit = row.get("require_citations", True)
        if require_cit and mapping:
            expected_cits = tuple(mapping[s] for s in row.get("relevant_sources", []) if s in mapping)
            cit_scores = citation_scores(parsed.citations, expected_cits)
            taxonomy = classify_failure(
                answer_correct=ans_correct,
                citation_exact=bool(cit_scores["citation_exact_match"]),
                citations=parsed.citations,
                invalid_ids=parsed.invalid_ids,
                malformed_ids=parsed.malformed_ids,
                expected_citations=expected_cits,
                has_citation_field=parsed.has_citation_field,
            )
            evaluation.update({
                **cit_scores,
                "invalid_ids": list(parsed.invalid_ids),
                "malformed_ids": list(parsed.malformed_ids),
                "invalid_id_rate": float(bool(parsed.invalid_ids)),
                "malformed_id_rate": float(bool(parsed.malformed_ids)),
                "failure_category": taxonomy,
            })
    return row


def main() -> int:
    raw_paths = sorted(glob.glob("results/raw/**/*.jsonl", recursive=True))
    updated_files = 0
    total_records = 0

    for path_str in raw_paths:
        path = Path(path_str)
        lines = path.read_text(encoding="utf-8").splitlines()
        if not lines:
            continue
        new_lines = []
        file_modified = False
        for line in lines:
            if not line.strip():
                continue
            row = json.loads(line)
            rescored = rescore_record(row)
            new_lines.append(json.dumps(rescored, sort_keys=True))
            total_records += 1
            file_modified = True

        if file_modified:
            path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
            updated_files += 1

    print(f"Rescored {total_records} records across {updated_files} raw files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
