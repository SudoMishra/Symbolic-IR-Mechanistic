"""Tokenizer adapters with an explicit, reproducible fallback."""

from __future__ import annotations

import re
from typing import Protocol


class TokenCounter(Protocol):
    name: str

    def count(self, text: str) -> int: ...


class RegexTokenCounter:
    """Deterministic approximation for offline tests; not a model tokenizer."""

    name = "regex-v1"
    _pattern = re.compile(r"[A-Za-z]+|\d+|[^\w\s]", re.UNICODE)

    def count(self, text: str) -> int:
        return len(self._pattern.findall(text))


class HuggingFaceTokenCounter:
    def __init__(self, model_name: str) -> None:
        try:
            from transformers import AutoTokenizer
        except ImportError as exc:
            raise RuntimeError("Install llm-symbolic-ir[hf] for HF tokenization") from exc
        self._tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.name = f"hf:{model_name}"

    def count(self, text: str) -> int:
        return len(self._tokenizer.encode(text, add_special_tokens=False))


class LlamaCppTokenCounter:
    def __init__(self, model_path: str) -> None:
        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise RuntimeError("Install llm-symbolic-ir[local] for GGUF tokenization") from exc
        self._model = Llama(model_path=model_path, vocab_only=True, verbose=False)
        self.name = f"llama.cpp:{model_path}"

    def count(self, text: str) -> int:
        return len(self._model.tokenize(text.encode("utf-8"), add_bos=False, special=True))


def create_token_counter(config: dict | None = None) -> TokenCounter:
    config = config or {}
    kind = config.get("type", "regex")
    if kind == "regex":
        return RegexTokenCounter()
    if kind == "huggingface":
        return HuggingFaceTokenCounter(str(config["model"]))
    if kind == "llama_cpp":
        return LlamaCppTokenCounter(str(config["model_path"]))
    raise ValueError(f"Unknown tokenizer type: {kind}")
