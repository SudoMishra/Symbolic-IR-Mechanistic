"""Optional local Transformers backend with deterministic defaults."""

from __future__ import annotations

import time

from symbolic_ir.schema import GenerationRequest, GenerationResponse

from .base import ModelBackend


class HuggingFaceBackend(ModelBackend):
    def __init__(self, model: str, revision: str | None = None, device_map: str = "auto") -> None:
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError("Install llm-symbolic-ir[hf] to use the Hugging Face backend") from exc
        self._model_name = model
        self._revision = revision
        self.tokenizer = AutoTokenizer.from_pretrained(model, revision=revision)
        self.model = AutoModelForCausalLM.from_pretrained(model, revision=revision, device_map=device_map)

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def model_revision(self) -> str | None:
        return self._revision

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        import torch
        inputs = self.tokenizer(request.prompt, return_tensors="pt").to(self.model.device)
        started = time.perf_counter()
        generation_kwargs = {
            "max_new_tokens": request.max_output_tokens,
            "do_sample": request.temperature > 0,
        }
        if request.temperature > 0:
            generation_kwargs["temperature"] = request.temperature
        with torch.inference_mode():
            result = self.model.generate(**inputs, **generation_kwargs)
        latency = time.perf_counter() - started
        generated = result[0, inputs["input_ids"].shape[1]:]
        text = self.tokenizer.decode(generated, skip_special_tokens=True)
        return GenerationResponse(
            text=text, model=self.model_name, model_revision=self.model_revision,
            input_tokens=int(inputs["input_ids"].numel()), output_tokens=int(generated.numel()),
            latency_seconds=latency,
        )
