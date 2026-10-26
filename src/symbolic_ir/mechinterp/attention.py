from __future__ import annotations


def attention_mass(attention, query_position: int, key_positions: list[int]) -> float:
    """Sum one head's attention from a query position to selected key positions."""
    return float(attention[..., query_position, key_positions].sum().item())

