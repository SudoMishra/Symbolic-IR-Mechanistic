"""Local GGUF inference through llama.cpp."""

from __future__ import annotations

import time

from symbolic_ir.schema import GenerationRequest, GenerationResponse

from .base import ModelBackend


class LlamaCppBackend(ModelBackend):
    def __init__(
        self,
        model_path: str,
        model: str,
        revision: str | None = None,
        n_ctx: int = 4096,
        n_threads: int | None = None,
        n_gpu_layers: int = 0,
        main_gpu: int = 0,
        offload_kqv: bool = True,
        seed: int = 0,
        chat_format: str | None = None,
        assistant_prefill: str | None = None,
    ) -> None:
        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise RuntimeError("Install llm-symbolic-ir[local] to use the llama.cpp backend") from exc
        options = {
            "model_path": model_path,
            "n_ctx": n_ctx,
            "n_gpu_layers": n_gpu_layers,
            "main_gpu": main_gpu,
            "offload_kqv": offload_kqv,
            "seed": seed,
            "verbose": False,
        }
        if n_threads is not None:
            options["n_threads"] = n_threads
            options["n_threads_batch"] = n_threads
        if chat_format:
            options["chat_format"] = chat_format
        self._llm = Llama(**options)
        self._model_name = model
        self._revision = revision
        self._assistant_prefill = assistant_prefill

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def model_revision(self) -> str | None:
        return self._revision

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        started = time.perf_counter()
        if self._assistant_prefill is not None:
            raw_prompt = f"<|im_start|>user\n{request.prompt}<|im_end|>\n<|im_start|>assistant\n{self._assistant_prefill}"
            response = self._llm(
                raw_prompt,
                temperature=request.temperature,
                max_tokens=request.max_output_tokens,
                seed=int(request.metadata.get("generation_seed", 0)),
            )
            latency = time.perf_counter() - started
            text = str(response["choices"][0]["text"] or "").strip()
            usage = response.get("usage", {})
        else:
            response = self._llm.create_chat_completion(
                messages=[{"role": "user", "content": request.prompt}],
                temperature=request.temperature,
                max_tokens=request.max_output_tokens,
                seed=int(request.metadata.get("generation_seed", 0)),
            )
            latency = time.perf_counter() - started
            text = str(response["choices"][0]["message"]["content"] or "")
            usage = response.get("usage", {})
        return GenerationResponse(
            text=text,
            model=self.model_name,
            model_revision=self.model_revision,
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
            latency_seconds=latency,
            raw=response,
        )
