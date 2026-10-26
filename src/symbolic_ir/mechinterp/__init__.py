"""Small, model-agnostic building blocks for post-behavioral causal analysis."""

from .similarity import centered_kernel_alignment, cosine_similarity
from .spans import find_after, token_positions_for_char_span
from .swaps import swap_source_identifiers

__all__ = [
    "centered_kernel_alignment", "cosine_similarity", "find_after",
    "swap_source_identifiers", "token_positions_for_char_span",
]
