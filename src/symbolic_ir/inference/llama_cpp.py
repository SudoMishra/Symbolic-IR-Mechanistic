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
        self._model_path = model_path

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def model_revision(self) -> str | None:
        return self._revision

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        started = time.perf_counter()
        if self._assistant_prefill is not None:
            handler = self._llm.chat_handler or self._llm._chat_handlers.get(self._llm.chat_format)
            if handler is None or not hasattr(handler, "__closure__") or not handler.__closure__:
                raise RuntimeError(
                    f"No chat template handler available for model {self.model_name} (chat_format={self._llm.chat_format})"
                )
            try:
                formatter = handler.__closure__[0].cell_contents
                rendered_chat = formatter(messages=[{"role": "user", "content": request.prompt}])
            except Exception as exc:
                raise RuntimeError(
                    f"Failed to render canonical chat template for model {self.model_name}: {exc}"
                ) from exc

            clean_prompt = rendered_chat.prompt
            for bos_str in ("<|startoftext|>", "<s>", "<bos>"):
                if clean_prompt.startswith(bos_str):
                    clean_prompt = clean_prompt[len(bos_str):]
                    break
            if clean_prompt.endswith("<think>"):
                raw_prompt = clean_prompt + "\n</think>\n"
            else:
                raw_prompt = clean_prompt + self._assistant_prefill
            stop_tokens = rendered_chat.stop

            call_kwargs = {
                "prompt": raw_prompt,
                "temperature": request.temperature,
                "max_tokens": request.max_output_tokens,
                "seed": int(request.metadata.get("generation_seed", 0)),
            }
            if stop_tokens:
                call_kwargs["stop"] = stop_tokens
            response = self._llm(**call_kwargs)
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
