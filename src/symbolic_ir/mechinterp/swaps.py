from __future__ import annotations

from symbolic_ir.schema import IdentifierMapping


def swap_source_identifiers(mapping: IdentifierMapping, left: str, right: str) -> IdentifierMapping:
    if left not in mapping.display_by_source or right not in mapping.display_by_source:
        raise KeyError("Both source keys must exist in the mapping")
    display = dict(mapping.display_by_source)
    citations = dict(mapping.citation_by_source)
    display[left], display[right] = display[right], display[left]
    citations[left], citations[right] = citations[right], citations[left]
    lengths = dict(mapping.token_lengths)
    lengths[left], lengths[right] = lengths[right], lengths[left]
    return IdentifierMapping(mapping.condition + ":swap", display, citations, lengths)

