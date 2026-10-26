"""Stable random streams that do not depend on Python's salted hash."""

from __future__ import annotations

import hashlib
import random


def derive_seed(seed: int, *parts: object) -> int:
    material = "\x1f".join([str(seed), *(str(part) for part in parts)])
    return int.from_bytes(hashlib.sha256(material.encode()).digest()[:8], "big")


def rng_for(seed: int, *parts: object) -> random.Random:
    return random.Random(derive_seed(seed, *parts))

