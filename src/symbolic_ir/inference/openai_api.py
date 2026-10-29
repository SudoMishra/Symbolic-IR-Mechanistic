"""OpenAI Responses API backend with reasoning controls, retry handling, and cost tracking."""

from __future__ import annotations

import copy
import hashlib
import os
import time
from pathlib import Path
from typing import Any

from symbolic_ir.budget import calculate_cost
from symbolic_ir.schema import GenerationRequest, GenerationResponse

from .base import ModelBackend


def _ensure_api_key() -> str | None:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        env_path = Path(".env")
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() == "OPENAI_API_KEY":
                        key = v.strip()
                        os.environ["OPENAI_API_KEY"] = key
                        break
    return key


class OpenAIBackend(ModelBackend):
    def __init__(
        self,
        model: str,
        revision: str | None = None,
        reasoning_effort: str | None = None,
        temperature: float | None = None,
        is_batch: bool = False,
        **client_kwargs,
    ) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install openai to use the OpenAI backend") from exc

        _ensure_api_key()
        self._client = OpenAI(**client_kwargs)
        self._model = model
        self._revision = revision
        self._reasoning_effort = reasoning_effort
        self._temperature = temperature
        self._is_batch = is_batch

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def model_revision(self) -> str | None:
        return self._revision

    def build_request_body(self, request: GenerationRequest) -> dict[str, Any]:
        prompt = request.prompt
        max_tokens = max(int(request.max_output_tokens or 256), 16)
        body: dict[str, Any] = {
            "model": self._model,
            "input": prompt,
            "max_output_tokens": max_tokens,
        }

        # Determine reasoning effort
        effort = None
        if request.reasoning_budget is not None and str(request.reasoning_budget).lower() != "none_budget":
            effort = str(request.reasoning_budget).lower()
        elif self._reasoning_effort is not None:
            effort = str(self._reasoning_effort).lower()

        if effort is not None:
            body["reasoning"] = {"effort": effort}

        # Temperature handling: Never send temperature if reasoning is configured,
        # or if model is Sol (which rejects temperature outright), or if temperature is None
        temp = request.temperature if request.temperature is not None else self._temperature
        is_sol = "sol" in self._model.lower()
        has_reasoning = "reasoning" in body and body["reasoning"].get("effort") not in (None, "none")
        if temp is not None and not is_sol and not has_reasoning:
            body["temperature"] = float(temp)

        return body

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        import openai

        body = self.build_request_body(request)
        prompt_hash = hashlib.sha256(request.prompt.encode("utf-8")).hexdigest()

        retries = 0
        max_retries = 2
        delay = 1.0
        response = None
        started = time.perf_counter()

        while True:
            try:
                response = self._client.responses.create(**body)
                break
            except (openai.RateLimitError, openai.APIConnectionError, openai.InternalServerError) as exc:
                if retries >= max_retries:
                    raise RuntimeError(f"OpenAI request failed after {retries} retries: {exc}") from exc
                retries += 1
                time.sleep(delay)
                delay *= 2.0
            except openai.APIStatusError as exc:
                if exc.status_code in (429, 500, 502, 503, 504) and retries < max_retries:
                    retries += 1
                    time.sleep(delay)
                    delay *= 2.0
                else:
                    raise

        latency = time.perf_counter() - started
        usage = getattr(response, "usage", None)
        input_details = getattr(usage, "input_tokens_details", None)
        output_details = getattr(usage, "output_tokens_details", None)

        input_tokens = getattr(usage, "input_tokens", None)
        output_tokens = getattr(usage, "output_tokens", None)
        cached_tokens = getattr(input_details, "cached_tokens", None)
        reasoning_tokens = getattr(output_details, "reasoning_tokens", None)

        cost = calculate_cost(
            self._model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            mode="batch" if self._is_batch else "sync",
            cached_tokens=cached_tokens,
        )

        returned_model = getattr(response, "model", self._model)
        request_id = getattr(response, "id", None)
        status = getattr(response, "status", "completed")

        return GenerationResponse(
            text=response.output_text,
            model=returned_model,
            model_revision=self._revision,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            reasoning_tokens=reasoning_tokens,
            cached_tokens=cached_tokens,
            latency_seconds=latency,
            request_id=request_id,
            stop_reason=status,
            prompt_hash=prompt_hash,
            request_body=copy.deepcopy(body),
            retry_count=retries,
            calculated_cost=cost,
            raw=response.model_dump(mode="json"),
        )
