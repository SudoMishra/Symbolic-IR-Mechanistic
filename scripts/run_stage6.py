#!/usr/bin/env python3
"""Collect paired, span-pooled hidden states for Stage 6."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from symbolic_ir.config import ExperimentConfig, expand_grid, load_config  # noqa: E402
from symbolic_ir.data import generate_examples  # noqa: E402
from symbolic_ir.identifiers import render_identifiers  # noqa: E402
from symbolic_ir.mechinterp.spans import find_after, token_positions_for_char_span  # noqa: E402
from symbolic_ir.prompts import render_prompt  # noqa: E402
from symbolic_ir.runner import reproducibility_metadata  # noqa: E402
from symbolic_ir.tokenization import create_token_counter  # noqa: E402


def resolve(path: str) -> Path:
    value = Path(path)
    return value if value.is_absolute() else ROOT / value


def stable_key(*values: object) -> str:
    payload = json.dumps(values, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode()).hexdigest()[:20]


def factual_text(text: str) -> str:
    sentence_end = text.find(".")
    if sentence_end < 0:
        raise ValueError(f"Source has no factual sentence terminator: {text!r}")
    return text[:sentence_end + 1]


def teacher_continuation(rendered) -> tuple[str, list[str]]:
    answer = rendered.expected_answer or rendered.canonical.answer
    citations = [rendered.mapping.citation_by_source[key] for key in rendered.canonical.relevant_sources]
    return f"ANSWER: {answer}\nCITATIONS: {', '.join(citations)}", citations


def build_text_and_spans(
    tokenizer, rendered, chat_template_kwargs: dict[str, Any] | None = None,
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    prompt = rendered.prompt
    formatted = tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}], tokenize=False, add_generation_prompt=True,
        **(chat_template_kwargs or {}),
    )
    continuation, citations = teacher_continuation(rendered)
    full_text = formatted + continuation
    encoded = tokenizer(full_text, add_special_tokens=False, return_offsets_mapping=True)
    offsets = encoded["offset_mapping"]
    prompt_start, _ = find_after(formatted, prompt)

    label_positions, content_positions = [], []
    cursor = prompt_start
    for source in rendered.canonical.sources:
        label = rendered.mapping.display_by_source[source.key]
        label_start, label_end = find_after(full_text, label, cursor)
        content = factual_text(source.text)
        content_start, content_end = find_after(full_text, content, label_end)
        label_positions.append(token_positions_for_char_span(offsets, label_start, label_end))
        content_positions.append(token_positions_for_char_span(offsets, content_start, content_end))
        cursor = content_end

    question_start, question_end = find_after(full_text, rendered.canonical.question, cursor)
    question_positions = token_positions_for_char_span(offsets, question_start, question_end)
    continuation_start = len(formatted)
    answer_text = rendered.expected_answer or rendered.canonical.answer
    answer_start, answer_end = find_after(full_text, answer_text, continuation_start)
    answer_positions = token_positions_for_char_span(offsets, answer_start, answer_end)
    citation_positions: list[int] = []
    citation_cursor = full_text.find("CITATIONS:", continuation_start)
    for citation in citations:
        cite_start, cite_end = find_after(full_text, citation, citation_cursor)
        positions = token_positions_for_char_span(offsets, cite_start, cite_end)
        citation_positions.extend(positions)
        citation_cursor = cite_end
    citation_positions = sorted(set(citation_positions))
    if min(answer_positions) == 0 or min(citation_positions) == 0:
        raise ValueError("Teacher-forced target cannot begin at token zero")
    spans = {
        "source_label": label_positions,
        "source_content": content_positions,
        "question": question_positions,
        "answer": answer_positions,
        "citation": citation_positions,
        "pre_answer": [min(answer_positions) - 1],
        "pre_citation": [min(citation_positions) - 1],
    }
    details = {
        "input_ids": encoded["input_ids"], "offset_mapping": offsets,
        "prompt_tokens": len(tokenizer(prompt, add_special_tokens=False)["input_ids"]),
        "formatted_prompt_tokens": len(tokenizer(formatted, add_special_tokens=False)["input_ids"]),
        "sequence_tokens": len(encoded["input_ids"]), "continuation": continuation,
    }
    return full_text, spans, details


def matrix(config: ExperimentConfig, tokenizer) -> list[dict[str, Any]]:
    counter = create_token_counter(config.generation.get("tokenizer"))
    rows: list[dict[str, Any]] = []
    for cell_index, cell in enumerate(expand_grid(config)):
        for example in generate_examples(cell, config.seed):
            for condition in config.identifiers:
                mapping = render_identifiers(example.sources, condition, config.seed, counter)
                rendered = render_prompt(example, mapping, require_citations=True)
                _, spans, details = build_text_and_spans(
                    tokenizer, rendered, config.generation.get("chat_template_kwargs")
                )
                rows.append({
                    "request_key": stable_key(config.digest, cell_index, example.example_id, condition),
                    "cell_index": cell_index, "cell": cell, "rendered": rendered,
                    "spans": spans, "details": details,
                })
    return rows


def validate(config: ExperimentConfig, tokenizer) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = matrix(config, tokenizer)
    prompt_lengths = [row["details"]["prompt_tokens"] for row in rows]
    sequence_lengths = [row["details"]["sequence_tokens"] for row in rows]
    bounds = config.dataset.get("prompt_tokens")
    if bounds and any(not int(bounds["min"]) <= value <= int(bounds["max"]) for value in prompt_lengths):
        outside = [value for value in prompt_lengths if not int(bounds["min"]) <= value <= int(bounds["max"])]
        raise ValueError(f"{len(outside)} prompts fall outside the configured token range; first={outside[0]}")
    maximum = int(config.generation.get("max_sequence_tokens", 8192))
    if max(sequence_lengths) > maximum:
        raise ValueError(f"Maximum teacher-forced sequence {max(sequence_lengths)} exceeds {maximum}")
    summary = {
        "requests": len(rows),
        "semantic_examples": len({row["rendered"].canonical.example_id for row in rows}),
        "prompt_tokens": {"min": min(prompt_lengths), "mean": round(sum(prompt_lengths) / len(prompt_lengths), 1),
                          "max": max(prompt_lengths)},
        "sequence_tokens": {"min": min(sequence_lengths), "mean": round(sum(sequence_lengths) / len(sequence_lengths), 1),
                            "max": max(sequence_lengths)},
    }
    return rows, summary


class SpanPooler:
    """Pool selected spans inside layer hooks without retaining full hidden states."""

    VECTOR_FIELDS = ("question", "pre_answer", "answer", "pre_citation", "citation")

    def __init__(self, model, spans: dict[str, Any]):
        import torch

        self.torch = torch
        self.spans = spans
        self.num_sources = len(spans["source_label"])
        self.states: dict[int, np.ndarray] = {}
        self.handles = []
        self.layers, self.final_norm = find_transformer_stack(model)
        self.handles.append(model.get_input_embeddings().register_forward_hook(self._hook(0)))
        for index, layer in enumerate(self.layers, 1):
            self.handles.append(layer.register_forward_hook(self._hook(index)))
        # Hugging Face hidden_states convention stores the final normalized state
        # at index num_hidden_layers, rather than the last pre-norm block output.
        if self.final_norm is not None:
            self.handles.append(self.final_norm.register_forward_hook(self._hook(len(self.layers))))

    @staticmethod
    def _tensor(output):
        if hasattr(output, "last_hidden_state"):
            return output.last_hidden_state
        if isinstance(output, (tuple, list)):
            return output[0]
        return output

    def _hook(self, index: int):
        def capture(_module, _inputs, output):
            hidden = self._tensor(output)
            position_sets = (
                list(self.spans["source_label"])
                + list(self.spans["source_content"])
                + [self.spans[field] for field in self.VECTOR_FIELDS]
            )
            pooled = self.torch.stack(
                [hidden[0, positions, :].mean(dim=0) for positions in position_sets]
            )
            self.states[index] = pooled.detach().to(device="cpu", dtype=self.torch.float16).numpy()
        return capture

    def close(self) -> None:
        for handle in self.handles:
            handle.remove()

    def arrays(self) -> dict[str, np.ndarray]:
        expected = set(range(len(self.layers) + 1))
        if set(self.states) != expected:
            raise RuntimeError(f"Missing pooled states: expected {sorted(expected)}, got {sorted(self.states)}")
        values = np.stack([self.states[index] for index in sorted(self.states)])
        count = self.num_sources
        arrays = {
            "source_label": values[:, :count],
            "source_content": values[:, count:2 * count],
        }
        for offset, field in enumerate(self.VECTOR_FIELDS, 2 * count):
            arrays[field] = values[:, offset]
        return arrays


def find_transformer_stack(model):
    """Find the text decoder layer list and its final norm across HF architectures."""
    import torch

    config = getattr(model.config, "text_config", model.config)
    expected = int(config.num_hidden_layers)
    candidates = []
    for name, module in model.named_modules():
        if isinstance(module, torch.nn.ModuleList) and len(module) == expected:
            score = (name.endswith("layers"), "language" in name or "text" in name, -name.count("."))
            candidates.append((score, name, module))
    if not candidates:
        raise RuntimeError(f"Could not locate a {expected}-layer decoder stack in {model.__class__.__name__}")
    _, name, layers = max(candidates, key=lambda item: item[0])
    parent = model.get_submodule(name.rsplit(".", 1)[0]) if "." in name else model
    norm = getattr(parent, "norm", None)
    return layers, norm


def target_nll(model, final_hidden, input_ids, positions: list[int]) -> tuple[float, list[float]]:
    import torch
    import torch.nn.functional as functional
    targets = torch.tensor(positions, device=input_ids.device)
    previous = targets - 1
    output_head = model.get_output_embeddings()
    head_device = output_head.weight.device
    selected = final_hidden[0, previous, :]
    if head_device.type != "meta":
        selected = selected.to(head_device)
    logits = output_head(selected).float()
    losses = functional.cross_entropy(logits, input_ids[0, targets].to(logits.device), reduction="none")
    values = [float(value) for value in losses.detach().cpu()]
    return float(sum(values) / len(values)), values


def run(config: ExperimentConfig, *, validate_only: bool = False, limit: int | None = None) -> dict[str, Any]:
    import transformers
    from transformers import AutoConfig, AutoModelForCausalLM, AutoModelForMultimodalLM, AutoTokenizer

    model_path = resolve(str(config.backend["model_path"]))
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True, use_fast=True)
    rows, summary = validate(config, tokenizer)
    if validate_only:
        return summary

    import torch

    dtype_name = str(config.backend.get("dtype", "bfloat16"))
    dtype = {"bfloat16": torch.bfloat16, "float16": torch.float16}[dtype_name]
    device = str(config.backend.get("device", "cuda:0"))
    if device.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is not available")
    load_kwargs: dict[str, Any] = {
        "local_files_only": True, "dtype": dtype, "low_cpu_mem_usage": True,
    }
    device_map = config.backend.get("device_map")
    if device_map:
        load_kwargs["device_map"] = device_map
        if config.backend.get("max_memory"):
            load_kwargs["max_memory"] = {
                int(key) if str(key).isdigit() else key: value
                for key, value in config.backend["max_memory"].items()
            }
        if config.backend.get("offload_folder"):
            load_kwargs["offload_folder"] = str(resolve(str(config.backend["offload_folder"])))
    auto_class = str(config.backend.get("auto_class", "causal_lm"))
    model_loader = AutoModelForMultimodalLM if auto_class == "multimodal_lm" else AutoModelForCausalLM
    if config.backend.get("text_only"):
        hf_config = AutoConfig.from_pretrained(model_path, local_files_only=True)
        if hasattr(hf_config, "vision_config"):
            hf_config.vision_config = None
        if hasattr(hf_config, "audio_config"):
            hf_config.audio_config = None
        load_kwargs["config"] = hf_config
    model = model_loader.from_pretrained(model_path, **load_kwargs)
    if not device_map:
        model = model.to(device)
    model.eval()
    layers, _ = find_transformer_stack(model)
    text_config = getattr(model.config, "text_config", model.config)
    output_dir = resolve(config.output_dir) / config.name / config.digest
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.jsonl"
    completed = set()
    if manifest_path.exists():
        for line in manifest_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                record = json.loads(line)
                if (output_dir / record["activation_file"]).exists():
                    completed.add(record["request_key"])
    metadata_path = output_dir / "metadata.json"
    if not metadata_path.exists():
        metadata = reproducibility_metadata(config, f"hf:{model_path}")
        metadata.update(summary)
        metadata.update({
            "torch": torch.__version__, "transformers": transformers.__version__,
            "transformers_model_class": model.__class__.__name__,
            "hidden_size": int(text_config.hidden_size), "num_hidden_layers": len(layers),
            "stored_layers": len(layers) + 1, "storage_dtype": "float16",
            "collection_method": "forward_hooks_span_pooling",
            "cuda_device": torch.cuda.get_device_name(0) if device.startswith("cuda") else None,
        })
        metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    selected = rows[:limit]
    started = time.perf_counter()
    completed_now = 0
    for index, row in enumerate(selected, 1):
        if row["request_key"] in completed:
            continue
        rendered = row["rendered"]
        full_text, spans, details = build_text_and_spans(
            tokenizer, rendered, config.generation.get("chat_template_kwargs")
        )
        encoded = tokenizer(full_text, add_special_tokens=False, return_tensors="pt")
        input_embedding = model.get_input_embeddings()
        input_device = input_embedding.weight.device
        if input_device.type == "meta" and hasattr(input_embedding, "_hf_hook"):
            input_device = input_embedding._hf_hook.execution_device
        input_ids = encoded["input_ids"].to(input_device)
        attention_mask = encoded["attention_mask"].to(input_device)
        pooler = SpanPooler(model, spans)
        try:
            with torch.inference_mode():
                outputs = model.model(
                    input_ids=input_ids, attention_mask=attention_mask,
                    output_hidden_states=False, use_cache=False, return_dict=True,
                )
                arrays = pooler.arrays()
                answer_nll, answer_token_nll = target_nll(
                    model, outputs.last_hidden_state, input_ids, spans["answer"]
                )
                citation_nll, citation_token_nll = target_nll(
                    model, outputs.last_hidden_state, input_ids, spans["citation"]
                )
        finally:
            pooler.close()
        activation_name = f"{row['request_key']}.npz"
        activation_path = output_dir / activation_name
        with activation_path.open("wb") as handle:
            np.savez_compressed(handle, **arrays)
        digest = hashlib.sha256(activation_path.read_bytes()).hexdigest()
        source_keys = [source.key for source in rendered.canonical.sources]
        relevant = set(rendered.canonical.relevant_sources)
        record = {
            "request_key": row["request_key"], "activation_file": activation_name,
            "activation_sha256": digest, "example_id": rendered.canonical.example_id,
            "seed": rendered.canonical.seed, "task_type": rendered.canonical.task_type,
            "model": config.backend["model"], "model_revision": config.backend.get("revision"),
            "identifier_condition": rendered.mapping.condition,
            "identifier_mapping": rendered.mapping.to_dict(), "source_order": source_keys,
            "relevant_sources": list(rendered.canonical.relevant_sources),
            "relevant_mask": [key in relevant for key in source_keys],
            "answer": rendered.expected_answer or rendered.canonical.answer,
            "continuation": details["continuation"], "prompt_tokens": details["prompt_tokens"],
            "formatted_prompt_tokens": details["formatted_prompt_tokens"],
            "sequence_tokens": details["sequence_tokens"],
            "span_token_counts": {
                key: [len(value) for value in positions] if key.startswith("source_") else len(positions)
                for key, positions in spans.items()
            },
            "answer_nll": answer_nll, "answer_token_nll": answer_token_nll,
            "citation_nll": citation_nll, "citation_token_nll": citation_token_nll,
            "dataset_cell": row["cell"],
        }
        with manifest_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
            handle.flush()
        completed.add(row["request_key"])
        completed_now += 1
        del outputs, arrays, input_ids, attention_mask, pooler
        if index % 5 == 0 or index == len(selected):
            elapsed = time.perf_counter() - started
            print(json.dumps({"progress": index, "planned": len(selected), "completed_now": completed_now,
                              "seconds": round(elapsed, 1), "max_cuda_mb": round(torch.cuda.max_memory_allocated() / 2**20, 1)}),
                  flush=True)
    return {**summary, "output_dir": str(output_dir), "planned": len(selected),
            "completed_now": completed_now, "total_completed": len(completed)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    result = run(load_config(resolve(args.config)), validate_only=args.validate_only, limit=args.limit)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
