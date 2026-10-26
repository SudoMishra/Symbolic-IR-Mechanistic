from __future__ import annotations

from collections.abc import Sequence


def token_positions_for_char_span(
    offsets: Sequence[Sequence[int]], start: int, end: int,
) -> list[int]:
    """Return token positions whose non-empty character offsets overlap a span."""
    if start < 0 or end <= start:
        raise ValueError(f"Invalid character span: ({start}, {end})")
    positions = [
        index for index, (token_start, token_end) in enumerate(offsets)
        if token_end > token_start and token_start < end and token_end > start
    ]
    if not positions:
        raise ValueError(f"No tokens overlap character span ({start}, {end})")
    return positions


def find_after(text: str, needle: str, start: int = 0) -> tuple[int, int]:
    """Locate a required substring at or after a known boundary."""
    position = text.find(needle, start)
    if position < 0:
        raise ValueError(f"Could not locate required text after character {start}: {needle!r}")
    return position, position + len(needle)
