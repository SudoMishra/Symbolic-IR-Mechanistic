from __future__ import annotations


def classify_failure(
    *, answer_correct: bool, citation_exact: bool, citations: tuple[str, ...],
    invalid_ids: tuple[str, ...], malformed_ids: tuple[str, ...],
    expected_citations: tuple[str, ...], has_citation_field: bool,
) -> str:
    if answer_correct and citation_exact:
        return "correct"
    if not answer_correct and not citation_exact:
        return "wrong_answer_and_citation"
    if answer_correct and malformed_ids:
        return "correct_source_malformed_identifier"
    if answer_correct and invalid_ids:
        return "hallucinated_identifier"
    if answer_correct and (not has_citation_field or not citations):
        return "missing_citation"
    if answer_correct and set(citations) != set(expected_citations):
        return "wrong_source_selected"
    return "other"

