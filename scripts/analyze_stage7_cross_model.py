#!/usr/bin/env python3
"""Create a compact cross-model synthesis from Stage 7 analyses."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


CONDITIONS = ("structured", "random_compact", "uuid")
LABELS = {"structured": "[S1]", "random_compact": "[XQ7M]", "uuid": "UUID"}


def short_model(name: str) -> str:
    return {
        "Qwen/Qwen2.5-1.5B-Instruct": "Qwen 1.5B",
        "LiquidAI/LFM2.5-1.2B-Instruct": "LFM 1.2B",
        "google/gemma-4-E2B-it": "Gemma E2B",
        "google/gemma-4-E4B-it": "Gemma E4B",
    }.get(name, name)


def effect(metric):
    low, high = metric["bootstrap_95_ci"]
    return f"{metric['mean']:.2f} [{low:.2f}, {high:.2f}]"


def build(results):
    lines = [
        "# Stage 7 cross-model causal synthesis", "",
        "The intervention swaps the identifiers assigned to one relevant source and one distractor while "
        "holding source text, identifier set, question, and answer fixed. Positive direct effects mean the "
        "model follows the relevant source to its newly assigned identifier.", "",
        "Cohort sizes differ because Gemma uses CPU offload on the 8 GiB GPU: Qwen and LFM use 8 semantic "
        "examples, Gemma E2B uses 4, and Gemma E4B is a 2-example diagnostic. Gemma intervals are therefore "
        "pilot-level and E4B is descriptive only.", "",
        "## Direct counterfactual rebinding", "",
        "| Model | n | [S1] swap effect | [XQ7M] swap effect | UUID swap effect | Decision |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for result in results:
        values = [effect(result["source_id_swap"][condition]["total_logprob"]) for condition in CONDITIONS]
        decision = ("correct rebinding" if result["checkpoint7"]["decision"] == "causal_correct_rebinding_evidence"
                    else "sensitive, inverted/old binding")
        lines.append(
            f"| {short_model(result['model'])} | {result['semantic_examples']} | {values[0]} | {values[1]} | "
            f"{values[2]} | {decision} |"
        )
    lines.extend((
        "", "## Where the counterfactual citation state becomes transferable", "",
        "Recovery is the patch effect divided by the model's own direct swap effect. The penultimate sampled "
        "layer is the Stage 6 late-output candidate; the final layer is a positive-control transplant of the "
        "fully formed citation state.", "",
        "| Model | Sampled late layer | [S1] recovery | [XQ7M] recovery | UUID recovery | Final-layer recovery range |",
        "|---|---:|---:|---:|---:|---:|",
    ))
    for result in results:
        late, final = result["layers"][-2], result["layers"][-1]
        late_values = [
            result["activation_patching"][condition][str(late)]["citation_context"]["aggregate_recovery_fraction"]
            for condition in CONDITIONS
        ]
        final_values = [
            result["activation_patching"][condition][str(final)]["citation_context"]["aggregate_recovery_fraction"]
            for condition in CONDITIONS
        ]
        lines.append(
            f"| {short_model(result['model'])} | {late} | {late_values[0]:.0%} | {late_values[1]:.0%} | "
            f"{late_values[2]:.0%} | {min(final_values):.0%}–{max(final_values):.0%} |"
        )
    lines.extend((
        "", "## Findings", "",
        "1. **The causal binding claim is model-dependent.** Qwen and both Gemma pilots follow the semantic "
        "source to its new identifier. LFM changes its citation distribution but, on average, favors the old "
        "association; compact IDs are significantly inverted.",
        "2. **Exact identifier reconstruction is late in every model.** Final-layer citation-state patches "
        "transfer approximately the full prompt-swap effect, while early controls are near zero.",
        "3. **The onset differs substantially.** Qwen has already transferred 74–108% at layer 24. Gemma E2B "
        "shows partial UUID transfer at layer 29. Gemma E4B's sampled layer 32 does not yet carry the short-ID "
        "effect in the correct direction, and its UUID effect is only 2%, placing reconstruction very late.",
        "4. **Source-local endpoint patches are not sufficient.** Across models, patching one label endpoint or "
        "one relevant fact span is much smaller and less consistent than patching the citation-generation "
        "trajectory. The source→identifier association is therefore not localized to the sampled endpoint alone.",
        "5. **Stage 6's shared geometry does not imply shared causal behavior.** All four models passed the "
        "representation gate, yet LFM fails correct counterfactual rebinding and the Gemma/Qwen output timelines "
        "differ. That dissociation is the central Stage 7 result.", "",
        "## Next mechanistic step", "",
        "Run component-level patching in the model-specific transition region, not at a common normalized depth:",
        "",
        "- Qwen: attention and MLP outputs in layers 20–24;",
        "- LFM: layers 6–13, treating it as an inverted-binding control;",
        "- Gemma E2B: layers 29–35;",
        "- Gemma E4B: densely sample layers 33–42 before head/MLP decomposition.", "",
        "Use a larger independent Stage 7 cohort before making population-level claims for either Gemma model.", "",
    ))
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    results = [json.loads(Path(path).read_text(encoding="utf-8")) for path in args.inputs]
    Path(args.output).write_text(build(results), encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
