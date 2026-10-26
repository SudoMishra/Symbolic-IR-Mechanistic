from __future__ import annotations

from typing import Any

from symbolic_ir.schema import RenderedExample

from .answer import answer_exact_match, answer_f1
from .citation import citation_scores
from .entity_binding import leakage_rate
from .error_taxonomy import classify_failure
from .parser import parse_output


def evaluate_output(rendered: RenderedExample, output: str) -> dict[str, Any]:
    allowed = tuple(rendered.mapping.citation_by_source.values())
    parsed = parse_output(output, allowed)
    expected_citations = tuple(rendered.mapping.citation_by_source[key] for key in rendered.canonical.relevant_sources)
    expected_answer = rendered.expected_answer or rendered.canonical.answer
    answer_aliases = [expected_answer, *map(str, rendered.canonical.metadata.get("answer_aliases", []))]
    answer_correct = any(answer_exact_match(parsed.answer, candidate) for candidate in answer_aliases)
    citation = citation_scores(parsed.citations, expected_citations) if rendered.require_citations else {
        "citation_exact_match": None, "citation_precision": None, "citation_recall": None,
    }
    taxonomy = "not_applicable" if not rendered.require_citations else classify_failure(
        answer_correct=answer_correct,
        citation_exact=bool(citation["citation_exact_match"]),
        citations=parsed.citations,
        invalid_ids=parsed.invalid_ids,
        malformed_ids=parsed.malformed_ids,
        expected_citations=expected_citations,
        has_citation_field=parsed.has_citation_field,
    )
    return {
        "parsed_answer": parsed.answer,
        "parsed_citations": list(parsed.citations),
        "expected_answer": expected_answer,
        "accepted_answers": answer_aliases,
        "expected_citations": list(expected_citations),
        "answer_correct": answer_correct,
        "answer_f1": answer_f1(parsed.answer, answer_aliases),
        **citation,
        "invalid_ids": list(parsed.invalid_ids),
        "malformed_ids": list(parsed.malformed_ids),
        "invalid_id_rate": float(bool(parsed.invalid_ids)),
        "malformed_id_rate": float(bool(parsed.malformed_ids)),
        "failure_category": taxonomy,
        "raw_pii_leakage_rate": leakage_rate(output, rendered.protected_values),
    }
