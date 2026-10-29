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
    strict_format: bool = False


_BRACKETED = re.compile(r"\[[^\]\n]+\]|<[^>\n]+>")
_UUID = re.compile(r"(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b")


def _deduplicate(values: list[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def check_strict_two_line(text: str) -> bool:
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    if len(lines) != 2:
        return False
    if not re.match(r"^ANSWER\s*:", lines[0], re.IGNORECASE):
        return False
    if re.search(r"\bCITATIONS?\s*:", lines[0], re.IGNORECASE):
        return False
    if not re.match(r"^CITATIONS?\s*:", lines[1], re.IGNORECASE):
        return False
    return True


def parse_output(text: str, allowed_ids: list[str] | tuple[str, ...]) -> ParsedOutput:
    clean_text = text.strip()
    if "</think>" in clean_text:
        post_think = clean_text.split("</think>")[-1].strip()
        if post_think:
            clean_text = post_think

    strict_fmt = check_strict_two_line(clean_text)

    # Find ANSWER and CITATION markers
    m_ans = re.search(r"(?i)\bANSWER\s*:", clean_text)
    m_cit = re.search(r"(?i)\bCITATIONS?\s*:", clean_text)

    citation_text = ""
    has_citation_field = m_cit is not None

    if m_ans and m_cit:
        if m_ans.start() < m_cit.start():
            # ANSWER comes before CITATIONS
            raw_answer = clean_text[m_ans.end():m_cit.start()]
            answer = raw_answer.strip().rstrip(" ,;.-")
            # For citations, take text from m_cit.end() up to next ANSWER if any
            rest_cit = clean_text[m_cit.end():]
            m_next_ans = re.search(r"(?i)\bANSWER\s*:", rest_cit)
            if m_next_ans:
                citation_text = rest_cit[:m_next_ans.start()].strip()
            else:
                citation_text = rest_cit.strip()
        else:
            # CITATIONS comes before ANSWER
            rest_cit = clean_text[m_cit.end():m_ans.start()]
            citation_text = rest_cit.strip()
            rest_ans = clean_text[m_ans.end():]
            lines = rest_ans.strip().splitlines()
            answer = lines[0].strip().rstrip(" ,;.-") if lines else ""
    elif m_ans:
        # Only ANSWER present
        raw_ans = clean_text[m_ans.end():]
        lines = raw_ans.strip().splitlines()
        answer = lines[0].strip().rstrip(" ,;.-") if lines else ""
    elif m_cit:
        # Only CITATIONS present
        before_cit = clean_text[:m_cit.start()].strip().rstrip(" ,;.-")
        answer = before_cit.splitlines()[-1].strip() if before_cit else ""
        citation_text = clean_text[m_cit.end():].strip()
    else:
        # Neither marker present
        lines = clean_text.splitlines()
        answer = lines[0].strip() if lines else ""

    allowed = tuple(sorted(allowed_ids, key=len, reverse=True))

    exact: list[str] = []
    occupied: list[tuple[int, int]] = []
    for identifier in allowed:
        for match in re.finditer(re.escape(identifier), citation_text):
            if not any(match.start() < end and start < match.end() for start, end in occupied):
                exact.append(identifier)
                occupied.append(match.span())
        bare = identifier.strip("[]<>")
        if bare and bare != identifier:
            pattern = rf"(?<![0-9a-zA-Z]){re.escape(bare)}(?![0-9a-zA-Z])"
            for match in re.finditer(pattern, citation_text):
                if not any(match.start() < end and start < match.end() for start, end in occupied):
                    exact.append(identifier)
                    occupied.append(match.span())

    candidates = _BRACKETED.findall(citation_text)
    if not candidates:
        candidates = _UUID.findall(citation_text)
    exact_stripped = {e.strip("[]<>") for e in exact}
    unknown = [
        candidate for candidate in candidates
        if candidate not in allowed and candidate not in exact and candidate.strip("[]<>") not in exact_stripped
    ]
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
        has_citation_field=has_citation_field,
        strict_format=strict_fmt,
    )

