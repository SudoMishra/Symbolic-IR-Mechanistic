#!/usr/bin/env python3
"""Run Stage 7 source-ID swaps with causal residual-stream patching."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from contextlib import nullcontext
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from symbolic_ir.config import ExperimentConfig, expand_grid, load_config  # noqa: E402
from symbolic_ir.data import generate_examples  # noqa: E402
from symbolic_ir.identifiers import render_identifiers  # noqa: E402
from symbolic_ir.mechinterp.patching import (  # noqa: E402
    BatchPositionActivationPatcher, PositionActivationPatcher,
)
from symbolic_ir.mechinterp.spans import find_after, token_positions_for_char_span  # noqa: E402
from symbolic_ir.mechinterp.swaps import swap_source_identifiers  # noqa: E402
from symbolic_ir.prompts import render_prompt  # noqa: E402
from symbolic_ir.runner import reproducibility_metadata  # noqa: E402
from symbolic_ir.tokenization import create_token_counter  # noqa: E402

from run_stage6 import factual_text, find_transformer_stack  # noqa: E402


SPAN_TYPES = ("source_label", "source_content", "citation_context", "question_control")


def resolve(path: str) -> Path:
    value = Path(path)
    return value if value.is_absolute() else ROOT / value


def stable_key(*values: object) -> str:
    payload = json.dumps(values, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode()).hexdigest()[:20]


def format_prompt(tokenizer, rendered, chat_template_kwargs: dict[str, Any] | None = None) -> str:
    return tokenizer.apply_chat_template(
        [{"role": "user", "content": rendered.prompt}], tokenize=False,
        add_generation_prompt=True, **(chat_template_kwargs or {}),
    )


def prefix_text(tokenizer, rendered, chat_template_kwargs: dict[str, Any] | None = None) -> str:
    formatted = format_prompt(tokenizer, rendered, chat_template_kwargs)
    answer = rendered.expected_answer or rendered.canonical.answer
    return f"{formatted}ANSWER: {answer}\nCITATIONS: "


def text_and_spans(tokenizer, rendered, target_label: str, chat_template_kwargs=None):
    formatted = format_prompt(tokenizer, rendered, chat_template_kwargs)
    answer = rendered.expected_answer or rendered.canonical.answer
    prefix = f"{formatted}ANSWER: {answer}\nCITATIONS: "
    text = prefix + target_label
    encoded = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True)
    offsets = encoded["offset_mapping"]
    prompt_start, _ = find_after(formatted, rendered.prompt)
    relevant_key = rendered.canonical.relevant_sources[0]
    cursor = prompt_start
    relevant_label_positions = None
    relevant_content_positions = None
    for source in rendered.canonical.sources:
        label = rendered.mapping.display_by_source[source.key]
        label_start, label_end = find_after(text, label, cursor)
        content = factual_text(source.text)
        content_start, content_end = find_after(text, content, label_end)
        if source.key == relevant_key:
            relevant_label_positions = token_positions_for_char_span(offsets, label_start, label_end)
            relevant_content_positions = token_positions_for_char_span(offsets, content_start, content_end)
        cursor = content_end
    if relevant_label_positions is None or relevant_content_positions is None:
        raise ValueError(f"Relevant source {relevant_key!r} was not found")
    question_start, question_end = find_after(text, rendered.canonical.question, cursor)
    question_positions = token_positions_for_char_span(offsets, question_start, question_end)
    target_positions = token_positions_for_char_span(offsets, len(prefix), len(text))
    if min(target_positions) == 0:
        raise ValueError("Citation target cannot begin at token zero")
    return text, {
        "source_label": [relevant_label_positions[-1]],
        "source_content": relevant_content_positions,
        "citation_context": [position - 1 for position in target_positions],
        "question_control": [question_positions[-1]],
        "target": target_positions,
    }, len(encoded["input_ids"])


def make_cases(config: ExperimentConfig, tokenizer) -> list[dict[str, Any]]:
    counter = create_token_counter(config.generation.get("tokenizer"))
    cases = []
    for cell_index, cell in enumerate(expand_grid(config)):
        for example in generate_examples(cell, config.seed):
            relevant = example.relevant_sources[0]
            distractor = next(source.key for source in example.sources if source.key not in example.relevant_sources)
            for condition in config.identifiers:
                clean_mapping = render_identifiers(example.sources, condition, config.seed, counter)
                swapped_mapping = swap_source_identifiers(clean_mapping, relevant, distractor)
                clean = render_prompt(example, clean_mapping, require_citations=True)
                swapped = render_prompt(example, swapped_mapping, require_citations=True)
                clean_label = clean_mapping.citation_by_source[relevant]
                swapped_label = swapped_mapping.citation_by_source[relevant]
                _, clean_spans, clean_tokens = text_and_spans(
                    tokenizer, clean, clean_label, config.generation.get("chat_template_kwargs")
                )
                _, swapped_spans, swapped_tokens = text_and_spans(
                    tokenizer, swapped, swapped_label, config.generation.get("chat_template_kwargs")
                )
                if len(clean_spans["source_content"]) != len(swapped_spans["source_content"]):
                    raise ValueError("The identical relevant source fact tokenized to different lengths after an ID swap")
                cases.append({
                    "case_key": stable_key(config.digest, cell_index, example.example_id, condition),
                    "cell": cell, "clean": clean, "swapped": swapped,
                    "relevant_source": relevant, "distractor_source": distractor,
                    "clean_label": clean_label, "swapped_label": swapped_label,
                    "clean_tokens": clean_tokens, "swapped_tokens": swapped_tokens,
                })
    return cases


class DonorRecorder:
    def __init__(self, layer_modules, spans: dict[str, list[int]]):
        self.states: dict[tuple[int, str], Any] = {}
        self.handles = []
        for layer_number, module in layer_modules.items():
            def capture(_module, _inputs, output, layer_number=layer_number):
                primary = output[0] if isinstance(output, (tuple, list)) else output
                for span_type in SPAN_TYPES:
                    positions = spans[span_type]
                    self.states[(layer_number, span_type)] = primary[0, positions, :].detach().cpu()
            self.handles.append(module.register_forward_hook(capture))

    def close(self):
        for handle in self.handles:
            handle.remove()


def input_device(model):
    embedding = model.get_input_embeddings()
    device = embedding.weight.device
    if device.type == "meta" and hasattr(embedding, "_hf_hook"):
        device = embedding._hf_hook.execution_device
    return device


def score_pair(model, tokenizer, rendered, clean_label, swapped_label, chat_template_kwargs=None,
               patch: tuple[str, Any, Any] | None = None, candidate_batch_size: int = 2):
    import torch
    import torch.nn.functional as functional

    built = [text_and_spans(tokenizer, rendered, label, chat_template_kwargs)
             for label in (clean_label, swapped_label)]
    texts = [item[0] for item in built]
    spans = [item[1] for item in built]
    for span_type in SPAN_TYPES:
        if span_type == "citation_context":
            continue
        if spans[0][span_type] != spans[1][span_type]:
            raise ValueError(f"Recipient {span_type} positions change across citation candidates")
    if candidate_batch_size not in (1, 2):
        raise ValueError("candidate_batch_size must be 1 or 2")
    batches = [[0, 1]] if candidate_batch_size == 2 else [[0], [1]]
    result_by_index = {}
    for batch_indices in batches:
        encoded = tokenizer(
            [texts[index] for index in batch_indices], add_special_tokens=False,
            padding=True, return_tensors="pt",
        )
        device = input_device(model)
        input_ids = encoded["input_ids"].to(device)
        attention_mask = encoded["attention_mask"].to(device)
        context = nullcontext()
        if patch is not None:
            module_name, donor_state, target_positions = patch
            if isinstance(donor_state, (tuple, list)):
                selected_states = [donor_state[index] for index in batch_indices]
                selected_positions = [target_positions[index] for index in batch_indices]
                if len(batch_indices) == 1:
                    context = PositionActivationPatcher(
                        model, module_name, selected_states[0], selected_positions[0]
                    )
                else:
                    context = BatchPositionActivationPatcher(
                        model, module_name, selected_states, selected_positions
                    )
            else:
                context = PositionActivationPatcher(model, module_name, donor_state, target_positions)
        with context, torch.inference_mode():
            output = model.model(
                input_ids=input_ids, attention_mask=attention_mask,
                output_hidden_states=False, use_cache=False, return_dict=True,
            )
            head = model.get_output_embeddings()
            for row, original_index in enumerate(batch_indices):
                row_spans = spans[original_index]
                targets = torch.tensor(row_spans["target"], device=input_ids.device)
                hidden = output.last_hidden_state[row, targets - 1, :]
                if head.weight.device.type != "meta":
                    hidden = hidden.to(head.weight.device)
                logits = head(hidden).float()
                losses = functional.cross_entropy(
                    logits, input_ids[row, targets].to(logits.device), reduction="none"
                )
                values = losses.detach().cpu().tolist()
                result_by_index[original_index] = {
                    "tokens": len(values), "total_logprob": -float(sum(values)),
                    "mean_logprob": -float(sum(values) / len(values)), "token_nll": values,
                }
        del output, input_ids, attention_mask
    result = [result_by_index[0], result_by_index[1]]
    return {"clean_label": result[0], "swapped_label": result[1]}, spans


def preference(scores: dict[str, Any], field: str) -> float:
    return float(scores["swapped_label"][field] - scores["clean_label"][field])


def load_model(config: ExperimentConfig):
    import torch
    from transformers import AutoConfig, AutoModelForCausalLM, AutoModelForMultimodalLM, AutoTokenizer

    model_path = resolve(str(config.backend["model_path"]))
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True, use_fast=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    dtype = {"bfloat16": torch.bfloat16, "float16": torch.float16}[str(config.backend.get("dtype", "bfloat16"))]
    device = str(config.backend.get("device", "cuda:0"))
    if device.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is not available")
    kwargs: dict[str, Any] = {"local_files_only": True, "dtype": dtype, "low_cpu_mem_usage": True}
    if config.backend.get("device_map"):
        kwargs["device_map"] = config.backend["device_map"]
        if config.backend.get("max_memory"):
            kwargs["max_memory"] = {
                int(key) if str(key).isdigit() else key: value
                for key, value in config.backend["max_memory"].items()
            }
        if config.backend.get("offload_folder"):
            kwargs["offload_folder"] = str(resolve(str(config.backend["offload_folder"])))
    if config.backend.get("text_only"):
        hf_config = AutoConfig.from_pretrained(model_path, local_files_only=True)
        if hasattr(hf_config, "vision_config"):
            hf_config.vision_config = None
        if hasattr(hf_config, "audio_config"):
            hf_config.audio_config = None
        kwargs["config"] = hf_config
    loader = AutoModelForMultimodalLM if config.backend.get("auto_class") == "multimodal_lm" else AutoModelForCausalLM
    model = loader.from_pretrained(model_path, **kwargs)
    if not config.backend.get("device_map"):
        model = model.to(device)
    model.eval()
    return model, tokenizer


def run(config: ExperimentConfig, validate_only=False, limit_examples: int | None = None):
    import torch
    import transformers

    model, tokenizer = load_model(config) if not validate_only else (None, None)
    if validate_only:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(resolve(str(config.backend["model_path"])), local_files_only=True, use_fast=True)
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token = tokenizer.eos_token
    cases = make_cases(config, tokenizer)
    example_ids = []
    for case in cases:
        example_id = case["clean"].canonical.example_id
        if example_id not in example_ids:
            example_ids.append(example_id)
    if limit_examples is not None:
        selected = set(example_ids[:limit_examples])
        cases = [case for case in cases if case["clean"].canonical.example_id in selected]
    prompt_tokens = [len(tokenizer(case["clean"].prompt, add_special_tokens=False)["input_ids"]) for case in cases]
    bounds = config.dataset.get("prompt_tokens")
    if bounds and any(not int(bounds["min"]) <= value <= int(bounds["max"]) for value in prompt_tokens):
        raise ValueError("At least one Stage 7 prompt is outside the configured token range")
    layers_requested = [int(value) for value in config.generation["intervention_layers"]]
    summary = {
        "cases": len(cases), "semantic_examples": len(set(case["clean"].canonical.example_id for case in cases)),
        "conditions": list(config.identifiers), "layers": layers_requested, "span_types": list(SPAN_TYPES),
        "prompt_tokens": {"min": min(prompt_tokens), "mean": sum(prompt_tokens) / len(prompt_tokens), "max": max(prompt_tokens)},
    }
    if validate_only:
        return summary

    layers, _ = find_transformer_stack(model)
    if min(layers_requested) < 1 or max(layers_requested) > len(layers):
        raise ValueError(f"Intervention layers must be in [1, {len(layers)}]")
    layer_modules = {number: layers[number - 1] for number in layers_requested}
    names_by_id = {id(module): name for name, module in model.named_modules()}
    layer_names = {number: names_by_id[id(module)] for number, module in layer_modules.items()}
    output_dir = resolve(config.output_dir) / config.name / config.digest
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.jsonl"
    completed = set()
    if manifest_path.exists():
        completed = {
            json.loads(line)["request_key"] for line in manifest_path.read_text(encoding="utf-8").splitlines() if line.strip()
        }
    metadata_path = output_dir / "metadata.json"
    if not metadata_path.exists():
        metadata = reproducibility_metadata(config, f"hf:{resolve(str(config.backend['model_path']))}")
        metadata.update(summary)
        metadata.update({
            "torch": torch.__version__, "transformers": transformers.__version__,
            "model_class": model.__class__.__name__, "num_hidden_layers": len(layers),
            "layer_module_names": layer_names,
            "cuda_device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "estimand": "change in swapped-minus-clean exact citation log probability after donor-to-recipient patching",
        })
        metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    started = time.perf_counter()
    candidate_batch_size = int(config.generation.get(
        "candidate_batch_size", 1 if config.backend.get("device_map") else 2
    ))
    total = len(cases) * len(layers_requested) * len(SPAN_TYPES)
    progressed = 0
    for case in cases:
        case_request_keys = {
            stable_key(case["case_key"], layer, span_type)
            for layer in layers_requested for span_type in SPAN_TYPES
        }
        if case_request_keys.issubset(completed):
            progressed += len(case_request_keys)
            continue
        kwargs = config.generation.get("chat_template_kwargs")
        clean_scores, clean_candidate_spans = score_pair(
            model, tokenizer, case["clean"], case["clean_label"], case["swapped_label"], kwargs,
            candidate_batch_size=candidate_batch_size,
        )
        swapped_scores, swapped_candidate_spans = score_pair(
            model, tokenizer, case["swapped"], case["clean_label"], case["swapped_label"], kwargs,
            candidate_batch_size=candidate_batch_size,
        )
        donor_recorders = []
        for donor_label in (case["clean_label"], case["swapped_label"]):
            donor_text, donor_spans, _ = text_and_spans(
                tokenizer, case["swapped"], donor_label, kwargs
            )
            donor_encoded = tokenizer(donor_text, add_special_tokens=False, return_tensors="pt")
            donor_ids = donor_encoded["input_ids"].to(input_device(model))
            donor_mask = donor_encoded["attention_mask"].to(input_device(model))
            recorder = DonorRecorder(layer_modules, donor_spans)
            try:
                with torch.inference_mode():
                    model.model(input_ids=donor_ids, attention_mask=donor_mask, use_cache=False, return_dict=True)
            finally:
                recorder.close()
            donor_recorders.append(recorder)
            del donor_ids, donor_mask
        clean_total_pref = preference(clean_scores, "total_logprob")
        swap_total_pref = preference(swapped_scores, "total_logprob")
        clean_mean_pref = preference(clean_scores, "mean_logprob")
        swap_mean_pref = preference(swapped_scores, "mean_logprob")
        for layer in layers_requested:
            for span_type in SPAN_TYPES:
                request_key = stable_key(case["case_key"], layer, span_type)
                progressed += 1
                if request_key in completed:
                    continue
                if span_type == "citation_context":
                    donor_state = [
                        recorder.states[(layer, span_type)] for recorder in donor_recorders
                    ]
                    target_positions = [spans[span_type] for spans in clean_candidate_spans]
                    if any(values.shape[0] != len(positions)
                           for values, positions in zip(donor_state, target_positions)):
                        raise ValueError(f"Unaligned {span_type} at layer {layer}")
                    donor_token_count = [int(values.shape[0]) for values in donor_state]
                    recipient_token_count = [len(positions) for positions in target_positions]
                else:
                    donor_state = donor_recorders[1].states[(layer, span_type)]
                    target_positions = clean_candidate_spans[0][span_type]
                    if donor_state.shape[0] != len(target_positions):
                        raise ValueError(f"Unaligned {span_type} at layer {layer}")
                    donor_token_count = int(donor_state.shape[0])
                    recipient_token_count = len(target_positions)
                patched_scores, _ = score_pair(
                    model, tokenizer, case["clean"], case["clean_label"], case["swapped_label"], kwargs,
                    patch=(layer_names[layer], donor_state, target_positions),
                    candidate_batch_size=candidate_batch_size,
                )
                patched_total_pref = preference(patched_scores, "total_logprob")
                patched_mean_pref = preference(patched_scores, "mean_logprob")
                denominator = swap_total_pref - clean_total_pref
                record = {
                    "request_key": request_key, "case_key": case["case_key"],
                    "example_id": case["clean"].canonical.example_id,
                    "task_type": case["clean"].canonical.task_type,
                    "dataset_cell": case["cell"], "identifier_condition": case["clean"].mapping.condition,
                    "model": config.backend["model"], "model_revision": config.backend.get("revision"),
                    "relevant_source": case["relevant_source"], "distractor_source": case["distractor_source"],
                    "clean_label": case["clean_label"], "swapped_label": case["swapped_label"],
                    "layer": layer, "module_name": layer_names[layer], "span_type": span_type,
                    "donor_span_tokens": donor_token_count, "recipient_span_tokens": recipient_token_count,
                    "clean_prompt_scores": clean_scores, "swapped_prompt_scores": swapped_scores,
                    "patched_clean_prompt_scores": patched_scores,
                    "clean_baseline_swap_preference_total": clean_total_pref,
                    "swapped_baseline_swap_preference_total": swap_total_pref,
                    "patched_swap_preference_total": patched_total_pref,
                    "causal_effect_total": patched_total_pref - clean_total_pref,
                    "recovery_fraction_total": ((patched_total_pref - clean_total_pref) / denominator)
                    if abs(denominator) > 1e-9 else None,
                    "clean_baseline_swap_preference_mean": clean_mean_pref,
                    "swapped_baseline_swap_preference_mean": swap_mean_pref,
                    "patched_swap_preference_mean": patched_mean_pref,
                    "causal_effect_mean": patched_mean_pref - clean_mean_pref,
                    "prompt_tokens": len(tokenizer(case["clean"].prompt, add_special_tokens=False)["input_ids"]),
                }
                with manifest_path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(record, sort_keys=True) + "\n")
                    handle.flush()
                completed.add(request_key)
                if progressed % 16 == 0 or progressed == total:
                    print(json.dumps({
                        "progress": progressed, "planned": total, "completed": len(completed),
                        "seconds": round(time.perf_counter() - started, 1),
                        "max_cuda_mb": round(torch.cuda.max_memory_allocated() / 2**20, 1),
                    }), flush=True)
        del donor_recorders
    return {**summary, "output_dir": str(output_dir), "planned_interventions": total,
            "completed_interventions": len(completed)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--limit-examples", type=int)
    args = parser.parse_args()
    result = run(load_config(resolve(args.config)), args.validate_only, args.limit_examples)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
