"""Optional OpenAI Responses API backend."""

from __future__ import annotations

import time

from symbolic_ir.schema import GenerationRequest, GenerationResponse

from .base import ModelBackend


class OpenAIBackend(ModelBackend):
    def __init__(self, model: str, revision: str | None = None, **client_kwargs) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install llm-symbolic-ir[openai] to use the OpenAI backend") from exc
        self._client = OpenAI(**client_kwargs)
        self._model = model
        self._revision = revision

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def model_revision(self) -> str | None:
        return self._revision

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        kwargs = {
            "model": self._model, "input": request.prompt,
            "max_output_tokens": request.max_output_tokens,
            "temperature": request.temperature,
        }
        if isinstance(request.reasoning_budget, str):
            kwargs["reasoning"] = {"effort": request.reasoning_budget}
        started = time.perf_counter()
        response = self._client.responses.create(**kwargs)
        latency = time.perf_counter() - started
        usage = getattr(response, "usage", None)
        output_details = getattr(usage, "output_tokens_details", None)
        return GenerationResponse(
            text=response.output_text,
            model=self._model,
            model_revision=self._revision,
            input_tokens=getattr(usage, "input_tokens", None),
            output_tokens=getattr(usage, "output_tokens", None),
            reasoning_tokens=getattr(output_details, "reasoning_tokens", None),
            latency_seconds=latency,
            raw=response.model_dump(mode="json"),
        )
