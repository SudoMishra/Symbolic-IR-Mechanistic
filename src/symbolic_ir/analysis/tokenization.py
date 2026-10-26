from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable


def identifier_length_summary(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    values: dict[str, list[int]] = defaultdict(list)
    for record in records:
        values[record["identifier_condition"]].extend(record["identifier_token_lengths"].values())
    return [
        {"identifier_condition": condition, "n": len(lengths), "mean_tokens": sum(lengths) / len(lengths), "min_tokens": min(lengths), "max_tokens": max(lengths)}
        for condition, lengths in sorted(values.items()) if lengths
    ]

