from __future__ import annotations


def leakage_rate(output: str, protected_values: tuple[str, ...]) -> float:
    if not protected_values:
        return 0.0
    leaked = sum(value.casefold() in output.casefold() for value in protected_values)
    return leaked / len(protected_values)

