# LLM Symbolic IR

A reproducible research harness for testing whether compact, canonical identifiers improve LLM citation fidelity, reference tracking, reasoning efficiency, and privacy-sensitive entity handling.

The repository implements the supplied roadmap as an experiment platform and contains matched local-model results. See [FINDINGS_MUSIQUE_STAGES_2_4.md](FINDINGS_MUSIQUE_STAGES_2_4.md) for the public multi-hop Qwen/LiquidAI/Gemma/Tiny-Aya experiment, [FINDINGS_STAGE5_CONFIRMATORY.md](FINDINGS_STAGE5_CONFIRMATORY.md) for the independent 3,200-generation reasoning-budget confirmation, [FINDINGS_STAGE6_CROSS_MODEL.md](FINDINGS_STAGE6_CROSS_MODEL.md) for the four-model paired hidden-state replication, [FINDINGS_STAGE7_CROSS_MODEL.md](FINDINGS_STAGE7_CROSS_MODEL.md) for causal source-ID swaps and activation patching, [FINDINGS_STAGE8_CROSS_MODEL.md](FINDINGS_STAGE8_CROSS_MODEL.md) for the five-model synthetic entity-canonicalization study, [FINDINGS_STAGE9.md](FINDINGS_STAGE9.md) for the systems synthesis and validated IR boundary, [FINDINGS_CROSS_MODEL.md](FINDINGS_CROSS_MODEL.md) for the earlier 2,000-generation comparison, [FINDINGS_LONGPROC_GPU.md](FINDINGS_LONGPROC_GPU.md) for the complete public 2K-output GPU experiment, and [MODEL_PROVENANCE.md](MODEL_PROVENANCE.md) for exact model revisions and hashes.

## What is implemented

- deterministic canonical citation, multi-source arithmetic, and synthetic PII datasets;
- paired rendering of the same examples under numeric, structured, semantic, random, hex, UUID, typed, untyped, and length-controlled identifiers;
- alias-only, UUID-with-alias, and no-citation controls;
- versioned prompts and tokenizer-specific identifier-length logging;
- interchangeable oracle, replay, llama.cpp/GGUF, OpenAI Responses API, and Hugging Face backends;
- append-only JSONL logging with complete prompts, mappings, raw responses, model metadata, token usage, latency, and evaluation;
- resumable experiments keyed by config, example, condition, control, and reasoning budget;
- exact citation parsing, adversarial malformed/invalid-ID detection, answer scoring, source-selection failure categories, and PII leakage measurement;
- grouped metrics, paired bootstrap confidence intervals, token-length summaries, budget curves, and optional plots;
- source-ID swap, activation recording and patching, attention-mass, logit-trajectory, linear-probe, cosine-similarity, and CKA primitives;
- a request-scoped typed IR with trusted-schema canonicalization, strict output validation, redacted audit records, and deterministic rehydration;
- experiment configs and entry points for roadmap Stages 0 through 9.

## Installation

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
pytest
```

The base environment can validate the same tests without installing pytest:

```bash
python3 scripts/run_tests.py
```

Optional extras:

```bash
pip install -e '.[analysis]'
pip install -e '.[openai]'
pip install -e '.[hf,mechinterp]'
```

## Quick start

Run the 20-example offline smoke test:

```bash
PYTHONPATH=src python3 -m symbolic_ir.cli run \
  --config configs/experiments/smoke_test.yaml
```

Re-running the command resumes the same run and skips completed request keys. Summarize its append-only output:

```bash
PYTHONPATH=src python3 -m symbolic_ir.cli summarize \
  results/raw/00_smoke_test/<config-digest>.jsonl
```

Inspect a matrix without generating outputs:

```bash
PYTHONPATH=src python3 -m symbolic_ir.cli validate \
  --config configs/experiments/citation_mve.yaml --preview
```

The Stage 1 config expands to 400 paired generations: 100 examples × 2 source counts × 2 identifier conditions.

## Running a real model

The generic research configs default to `backend: {type: oracle}` so an accidental command cannot spend API credits or download a model. The explicitly named Qwen, LiquidAI, and Gemma configs point to local revision-pinned GGUF artifacts.

OpenAI Responses API:

```yaml
backend:
  type: openai
  model: YOUR_PINNED_MODEL_ID
  revision: YOUR_RECORDED_REVISION
generation:
  reasoning_budgets: [low, medium, high]
  temperature: 0
```

Set `OPENAI_API_KEY` in the environment. The adapter stores the complete serialized response in `raw_response`.

Local Hugging Face model:

```yaml
backend:
  type: huggingface
  model: YOUR_ORGANIZATION/YOUR_MODEL
  revision: FULL_COMMIT_HASH
  device_map: auto
generation:
  tokenizer:
    type: huggingface
    model: YOUR_ORGANIZATION/YOUR_MODEL
```

Use a tokenizer matching the tested model for publishable token-length comparisons. `regex-v1` is only a deterministic offline approximation.

The completed cross-model run can be reproduced from:

```text
configs/experiments/citation_mve_{qwen15b,lfm25_12b,gemma4_e2b,gemma4_e4b}.yaml
configs/pilots/token_matched_numeric_{qwen15b,lfm25_12b,gemma4_e2b,gemma4_e4b}.yaml
```

Generate the unified report with `scripts/analyze_cross_model.py`; its CLI accepts one repeated `--model LABEL STAGE1_JSONL NUMERIC_JSONL` triple per model.

## Public 2K-output benchmark

The long-context extension uses the public Apache-2.0 LongProc
`tom_tracking_2k` benchmark. Its model output is a deterministic, step-by-step
belief-state trace, which supports stricter evaluation than free-form summaries.
The 25-example manifest was filtered using all four real model tokenizers; every
selected example has a 2,048–4,096-token prompt and a 1,024–2,048-token reference
under Qwen, LFM, Gemma E2B, and Gemma E4B. See
[`DATASET_PROVENANCE.md`](DATASET_PROVENANCE.md) for hashes and exact distributions.

Fetch and verify the revision-pinned public files:

```bash
.venv/bin/python scripts/fetch_longproc.py
```

Validate a model-specific config without loading the inference backend:

```bash
.venv/bin/python scripts/run_longproc.py \
  --config configs/longproc/tom_tracking_2k_qwen15b.yaml \
  --validate-only
```

Run one resumable smoke example, or omit `--limit` for all 25:

```bash
.venv/bin/python scripts/run_longproc.py \
  --config configs/longproc/tom_tracking_2k_qwen15b.yaml \
  --limit 1
```

Equivalent configs are provided for LFM2.5 1.2B and Gemma 4 E2B/E4B. All use
an 8,192-token context, deterministic decoding, and a 2,048-token generation cap.

## Public multi-hop Stages 2–4

The roadmap's scaling, representation-control, and failure-decomposition stages
use 100 balanced examples from MuSiQue-Answerable v1.0. Each prompt contains 15
or 20 passages and is 2,000–3,700 raw tokens under every tested tokenizer.

```bash
.venv/bin/python scripts/fetch_musique.py
.venv/bin/python scripts/run_musique_stages.py \
  --config configs/musique/stages_2_4_qwen15b.yaml --validate-only
.venv/bin/python scripts/run_musique_stages.py \
  --config configs/musique/stages_2_4_qwen15b.yaml
.venv/bin/python scripts/analyze_musique_stages.py
```

Equivalent configs cover LFM2.5 1.2B, Gemma 4 E2B/E4B, and Tiny Aya Global.
Each run is resumable and contains 1,500 generations: 800 Stage 2, 500 Stage 3,
and 200 Stage 4.

## Experiment sequence

| Stage | Config | Purpose | Gate |
|---|---|---|---|
| 0 | `smoke_test.yaml` | End-to-end reproducibility | 20 records run, resume, and score |
| 1 | `citation_mve.yaml` | `[S1]` vs UUID at 5/20 sources | Inspect behavioral effect |
| 2 | `identifier_scaling.yaml` | Identifier family × source count × task | Select 2–4 conditions |
| 3 | `token_length.yaml` | Length and representation controls | Separate length from structure |
| 4 | `failure_decomposition.yaml` | Alias, UUID, and citation-required controls | Attribute failure mechanism |
| 5 | `reasoning_budget.yaml` | Identifier × budget interaction | Establish compute competition |
| 6 | `symbolic_compression.yaml` | Cross-format representation runs | Require a reproducible signature |
| 7 | `mechinterp.yaml` | Causal open-weight instrumentation | Require causal evidence |
| 8 | `pii_masking.yaml` | Raw/random/untyped/typed synthetic entities | Test non-citation generalization |
| 9 | `experiments/09_system_ir.py` | Canonicalize, validate, and rehydrate | Produce the systems synthesis |

Stages 0–8 use versioned experiment configs. An optional first positional
argument limits generation count, which is useful when checking a newly
configured backend:

```bash
PYTHONPATH=src python3 experiments/01_citation_mve.py 4
```

Stage 9 is a deterministic systems evaluation and has its own request/record
arguments rather than a model-generation config.

## Result integrity

Raw records live at:

```text
results/raw/<experiment-name>/<config-digest>.jsonl
```

The runner never truncates this file. It writes one compact record, flushes it to disk, and uses stable request keys to resume. The adjacent metadata file captures the full config, config digest, Python/platform versions, tokenizer, timestamp, and Git revision. To collect an independent replicate, change the seed or add replicate metadata so the config digest changes.

The canonical datasets contain source keys and semantic ground truth—not rendered identifiers. Identifier mappings are created afterward, so every condition receives the same task content and source order within a paired example.

## Analysis

Aggregate a result:

```bash
symbolic-ir summarize results/raw/.../run.jsonl
```

Estimate a paired delta (`condition_b - condition_a`) with a bootstrap 95% interval:

```bash
symbolic-ir bootstrap results/raw/.../run.jsonl structured uuid \
  --metric citation_exact_match --samples 10000
```

Programmatic helpers are in `symbolic_ir.analysis`. Optional plotting deliberately consumes aggregated tables rather than raw generations.

## Mechanistic workflow

`symbolic_ir.mechinterp` provides small framework-agnostic pieces:

1. use `swap_source_identifiers` for the clean binding intervention;
2. capture named module outputs with `ActivationRecorder`;
3. patch selected token positions with `ActivationPatcher`;
4. quantify attention to source/ID spans and trace target-token logits;
5. compare aligned representations with cosine similarity or linear CKA;
6. fit probes only as supporting evidence, not as a substitute for intervention.

Model architectures expose different module names and output structures, so the repository does not pretend one universal patching script is valid for all Transformers. Pin the architecture and record the exact module/position selection in the experiment metadata.

The completed Stage 7 protocol is implemented in `scripts/run_stage7.py`. It
swaps a relevant source's identifier with a distractor, scores the exact old and
new citation strings, and patches source-label, source-content, question-control,
and full citation-prediction residual states. Model-specific configs are
`configs/experiments/stage7_{qwen25_15b,lfm25_12b,gemma4_e2b,gemma4_e4b}.yaml`.
Generate model reports with `scripts/analyze_stage7.py` and the synthesis with
`scripts/analyze_stage7_cross_model.py`.

## Stage 8 entity-canonicalization workflow

Stage 8 uses synthetic account-resolution records so no real PII is processed.
It compares raw values, arbitrary masked values, untyped canonical handles, and
typed canonical handles while holding `[S1]` source labels and semantic content
fixed. Citations are disabled, making this a non-citation binding test.

```bash
.venv/bin/python scripts/run_stage8.py \
  --config configs/experiments/stage8_pii_qwen15b.yaml --validate-only
.venv/bin/python scripts/run_stage8.py \
  --config configs/experiments/stage8_pii_qwen15b.yaml
.venv/bin/python scripts/analyze_stage8.py \
  results/raw/stage8_pii_qwen25_15b/02832ba6fcee.jsonl \
  --label 'Qwen 1.5B' --report FINDINGS_STAGE8_QWEN.md \
  --json results/analysis/stage8_pii_qwen15b.json
.venv/bin/python scripts/analyze_stage8_cross_model.py
```

Equivalent configs cover LFM2.5 1.2B, Gemma 4 E2B/E4B, and Tiny Aya Global.
Each completed run contains 160 generations: 40 semantic examples × four
entity representations.

## Stage 9 reference IR boundary

`symbolic_ir.ir` implements the roadmap's trusted application boundary:

```text
raw state → typed model view → symbolic JSON → validation → rehydration
              ↘ request-scoped mapping vault ↗
```

The model-facing payload and reversible mapping are separate objects. The
validator checks strict schema, raw-value exposure, handle syntax, request
registry membership, field types, and tool policy before same-request
rehydration. A handle is only a reference; application authorization and
semantic verification still happen after resolution.

Run the 500-request, 5,000-attack operational evaluation with:

```bash
.venv/bin/python experiments/09_system_ir.py \
  --requests 500 --records-per-request 20
```

See `FINDINGS_STAGE9.md` for the contract, measured results, limitations, and
RAG/agent recommendations.

## Privacy scope

The PII dataset is synthetic. Typed, untyped, and random masking replace entity values before prompt construction and evaluate raw-value leakage in the output. This can measure reduced model exposure when literal values are unnecessary; placeholder substitution alone is not a complete privacy or security system. Production rehydration maps should remain outside model context, access-controlled, and validated before use.

## Repository layout

```text
configs/experiments/     versioned experiment matrices
experiments/             one entry point per roadmap stage
src/symbolic_ir/data/    canonical synthetic generators
src/symbolic_ir/identifiers/ deterministic representation layer
src/symbolic_ir/prompts/ prompt and PII canonicalization
src/symbolic_ir/inference/ model adapters
src/symbolic_ir/evaluation/ parser, metrics, taxonomy
src/symbolic_ir/analysis/ aggregation and statistics
src/symbolic_ir/mechinterp/ causal-analysis primitives
src/symbolic_ir/ir/       canonicalization, validation, audit, rehydration
tests/                   deterministic and adversarial tests
results/                 ignored raw/processed/figure outputs
```
