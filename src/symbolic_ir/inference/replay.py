from __future__ import annotations

import json
from pathlib import Path

from symbolic_ir.schema import GenerationRequest, GenerationResponse

from .base import ModelBackend


class ReplayBackend(ModelBackend):
    def __init__(self, path: str, model_name: str = "replay") -> None:
        self._model_name = model_name
        self._responses: dict[str, dict] = {}
        with Path(path).open("r", encoding="utf-8") as handle:
            for line in handle:
                record = json.loads(line)
                self._responses[str(record["request_key"])] = record

    @property
    def model_name(self) -> str:
        return self._model_name

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        key = str(request.metadata["request_key"])
        try:
            record = self._responses[key]
        except KeyError as exc:
            raise KeyError(f"No replay response for request_key={key}") from exc
        return GenerationResponse(
            text=str(record["raw_output"]), model=self.model_name,
            model_revision=record.get("model_revision"),
            input_tokens=record.get("token_counts", {}).get("input"),
            output_tokens=record.get("token_counts", {}).get("output"),
            reasoning_tokens=record.get("token_counts", {}).get("reasoning"),
            latency_seconds=record.get("latency"), raw={"replayed": True},
        )

