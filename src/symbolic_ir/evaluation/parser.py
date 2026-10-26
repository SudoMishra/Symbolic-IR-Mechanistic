"""Conservative output parsing driven by the identifiers valid for one prompt."""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass(frozen=True)
class ParsedOutput:
    answer: str
    citations: tuple[str, ...]
    invalid_ids: tuple[str, ...]
    malformed_ids: tuple[str, ...]
    has_citation_field: bool


_ANSWER = re.compile(r"(?im)^\s*ANSWER\s*:\s*(.*?)\s*$")
_CITATIONS = re.compile(r"(?im)^\s*CITATIONS?\s*:\s*(.*?)\s*$")
_BRACKETED = re.compile(r"\[[^\]\n]+\]|<[^>\n]+>")
_UUID = re.compile(r"(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b")


def _deduplicate(values: list[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def parse_output(text: str, allowed_ids: list[str] | tuple[str, ...]) -> ParsedOutput:
    answer_match = _ANSWER.search(text)
    answer = answer_match.group(1).strip() if answer_match else text.strip().splitlines()[0] if text.strip() else ""
    citation_match = _CITATIONS.search(text)
    citation_text = citation_match.group(1).strip() if citation_match else ""
    allowed = tuple(sorted(allowed_ids, key=len, reverse=True))

    exact: list[str] = []
    occupied: list[tuple[int, int]] = []
    for identifier in allowed:
        for match in re.finditer(re.escape(identifier), citation_text):
            if not any(match.start() < end and start < match.end() for start, end in occupied):
                exact.append(identifier)
                occupied.append(match.span())

    candidates = _BRACKETED.findall(citation_text)
    if not candidates:
        candidates = _UUID.findall(citation_text)
    unknown = [candidate for candidate in candidates if candidate not in allowed]
    malformed: list[str] = []
    invalid: list[str] = []
    for candidate in unknown:
        similarity = max((SequenceMatcher(None, candidate, known).ratio() for known in allowed), default=0.0)
        if similarity >= 0.65:
            malformed.append(candidate)
        else:
            invalid.append(candidate)
    return ParsedOutput(
        answer=answer,
        citations=_deduplicate(exact),
        invalid_ids=_deduplicate(invalid),
        malformed_ids=_deduplicate(malformed),
        has_citation_field=citation_match is not None,
    )

