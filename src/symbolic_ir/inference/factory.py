from __future__ import annotations

from typing import Any

from .base import ModelBackend
from .huggingface import HuggingFaceBackend
from .llama_cpp import LlamaCppBackend
from .openai_api import OpenAIBackend
from .oracle import OracleBackend
from .replay import ReplayBackend


def create_backend(config: dict[str, Any]) -> ModelBackend:
    kind = str(config.get("type", "oracle"))
    options = {key: value for key, value in config.items() if key != "type"}
    if kind == "oracle":
        return OracleBackend()
    if kind == "replay":
        return ReplayBackend(**options)
    if kind == "openai":
        return OpenAIBackend(**options)
    if kind == "huggingface":
        return HuggingFaceBackend(**options)
    if kind == "llama_cpp":
        return LlamaCppBackend(**options)
    raise ValueError(f"Unknown backend type: {kind}")
