"""Anthropic Messages API backend with thinking controls, retry handling, and cost tracking."""

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
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        env_path = Path(".env")
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() == "ANTHROPIC_API_KEY":
                        key = v.strip()
                        os.environ["ANTHROPIC_API_KEY"] = key
                        break
    return key


class AnthropicBackend(ModelBackend):
    def __init__(
        self,
        model: str,
        revision: str | None = None,
        thinking_type: str = "disabled",
        effort: str | None = "low",
        is_batch: bool = False,
        **client_kwargs,
    ) -> None:
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise RuntimeError("Install anthropic to use the Anthropic backend") from exc

        _ensure_api_key()
        self._client = Anthropic(**client_kwargs)
        self._model = model
        self._revision = revision
        self._thinking_type = thinking_type
        self._effort = effort
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
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }

        # Thinking setting
        t_type = request.thinking_type or self._thinking_type
        if t_type in ("disabled", "none"):
            body["thinking"] = {"type": "disabled"}
        elif t_type == "between_tools":
            body["thinking"] = {"type": "between_tools"}
        elif t_type == "adaptive":
            body["thinking"] = {"type": "adaptive"}
        elif t_type == "enabled":
            budget = int(request.reasoning_budget or 1024)
            body["thinking"] = {"type": "enabled", "budget_tokens": budget}

        # Effort setting
        eff = request.effort or self._effort
        if eff:
            body["output_config"] = {"effort": eff}

        return body

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        import anthropic

        body = self.build_request_body(request)
        prompt_hash = hashlib.sha256(request.prompt.encode("utf-8")).hexdigest()

        retries = 0
        max_retries = 2
        delay = 1.0
        response = None
        started = time.perf_counter()

        while True:
            try:
                response = self._client.messages.create(**body)
                break
            except (anthropic.RateLimitError, anthropic.APIConnectionError, anthropic.InternalServerError) as exc:
                if retries >= max_retries:
                    raise RuntimeError(f"Anthropic request failed after {retries} retries: {exc}") from exc
                retries += 1
                time.sleep(delay)
                delay *= 2.0
            except anthropic.APIStatusError as exc:
                if exc.status_code in (429, 500, 502, 503, 504) and retries < max_retries:
                    retries += 1
                    time.sleep(delay)
                    delay *= 2.0
                else:
                    raise

        latency = time.perf_counter() - started
        text_parts = [b.text for b in response.content if getattr(b, "type", "") == "text" or hasattr(b, "text")]
        output_text = "".join(text_parts)

        usage = getattr(response, "usage", None)
        output_details = getattr(usage, "output_tokens_details", None)

        input_tokens = getattr(usage, "input_tokens", None)
        output_tokens = getattr(usage, "output_tokens", None)
        cached_tokens = getattr(usage, "cache_read_input_tokens", None)
        reasoning_tokens = getattr(output_details, "thinking_tokens", None)

        cost = calculate_cost(
            self._model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            mode="batch" if self._is_batch else "sync",
            cached_tokens=cached_tokens,
        )

        returned_model = getattr(response, "model", self._model)
        request_id = getattr(response, "id", None)
        stop_reason = getattr(response, "stop_reason", None)

        return GenerationResponse(
            text=output_text,
            model=returned_model,
            model_revision=self._revision,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            reasoning_tokens=reasoning_tokens,
            cached_tokens=cached_tokens,
            latency_seconds=latency,
            request_id=request_id,
            stop_reason=stop_reason,
            prompt_hash=prompt_hash,
            request_body=copy.deepcopy(body),
            retry_count=retries,
            calculated_cost=cost,
            raw=response.model_dump(mode="json"),
        )
