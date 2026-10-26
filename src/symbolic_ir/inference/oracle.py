"""Deterministic non-model backend for pipeline validation only."""

from __future__ import annotations

import time

from symbolic_ir.schema import GenerationRequest, GenerationResponse
from symbolic_ir.tokenization import RegexTokenCounter

from .base import ModelBackend


class OracleBackend(ModelBackend):
    model_name = "oracle-test-backend"
    model_revision = "v1"

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        started = time.perf_counter()
        answer = str(request.metadata["expected_answer"])
        citations = list(request.metadata.get("expected_citations", []))
        require_citations = bool(request.metadata.get("require_citations", True))
        text = f"ANSWER: {answer}"
        if require_citations:
            text += f"\nCITATIONS: {', '.join(citations)}"
        counter = RegexTokenCounter()
        return GenerationResponse(
            text=text,
            model=self.model_name,
            model_revision=self.model_revision,
            input_tokens=counter.count(request.prompt),
            output_tokens=counter.count(text),
            reasoning_tokens=0,
            latency_seconds=time.perf_counter() - started,
            raw={"warning": "oracle backend is for harness verification, not research results"},
        )

