# Technical Appendix: Symbolic IR Experiments

This appendix supports [The Hidden Cost of UUIDs](symbolic-ir-engineering-blog.md).
It separates completed measurements from interpretation and proposed systems
guidance.

## Evidence ledger

| Experiment | Scale | Models | Primary question | Main conclusion |
|---|---:|---|---|---|
| Stage 0 | 20 records | Oracle smoke backend | Does the complete pipeline run, resume, and score? | Yes; infrastructure gate passed. |
| Stage 1 and controls | 2,000 generations | Qwen, LFM, Gemma E2B/E4B | Do compact identifiers change cost and citation binding? | UUID cost is large; binding direction initially varies by model. |
| MuSiQue Stages 2–4 | 7,500 generations | Qwen, LFM, Gemma E2B/E4B, Tiny Aya | Does the effect survive multi-hop retrieval and controls? | UUID binding is directionally worse in every primary cell; answer effects are smaller. |
| Held-out MuSiQue | 2,000 generations | Same five | Does the primary binding result replicate? | UUID binding is lower in 10/10 cells; 6/10 intervals exclude zero. |
| LongProc | 100 generations | Qwen, LFM, Gemma E2B/E4B | Does long generation imply procedural correctness? | No; endpoint, trace, completion, and length diverge sharply. |
| Stage 5 pilot | 2,400 two-pass generations | Five models | Does identifier cost interact monotonically with scratchpad budget? | Pilot effects were heterogeneous and required confirmation. |
| Stage 5 confirmation | 3,200 two-pass generations | Qwen, Gemma E2B, Tiny Aya retained cells | Does the interaction replicate? | No broad monotonic interaction; output cost persists. |
| Stage 6 | 960 paired forward passes | Qwen, LFM, Gemma E2B/E4B BF16 | Do different surfaces converge internally? | Fact geometry is stable; labels converge; citation states specialize late. |
| Stage 7 | 66 swaps and 1,056 interventions | Qwen, LFM, Gemma E2B/E4B | Is the source-to-ID relationship causal and transferable? | Yes, but causal direction and timing are architecture-dependent. |
| Stage 8 | 800 generations | Five models | Do typed handles help beyond citation formatting? | Significant controlled gains appear in Qwen and Tiny Aya; not universal. |
| Stage 9 | 500 valid requests and 5,000 attacks | Deterministic reference system | Can a typed IR enforce representation integrity? | Yes for structural classes; not for a wrong but registered handle. |

The behavioral model-generation total is 18,020. Forward passes,
interventions, valid systems requests, and adversarial tests are reported
separately.

## Metric definitions

### Answer exact match and answer F1

Answer exact match compares a normalized answer with the gold short answer.
Answer F1 gives partial credit based on normalized token overlap. Some early
synthetic tasks also report `answer_content`, which accepts the gold short answer
inside an otherwise verbose answer field.

### Strict citation

Strict citation requires the exact expected identifier strings, including
wrappers, with no extra identifiers. It intentionally combines source choice,
literal reconstruction, and formatting.

### Relaxed source binding

Relaxed binding maps emitted identifiers back to canonical sources while
tolerating specified surface variations such as omitted brackets. Binding exact
requires the complete correct source set. Binding recall measures the fraction
of gold supporting sources recovered.

### Surface-only failure

The canonical source selection is correct but the emitted identifier surface
violates the required syntax or wrapper.

### Malformed and invalid identifiers

A malformed identifier resembles the requested family but violates its syntax.
An invalid identifier may be syntactically plausible but is not present in the
request registry.

### LongProc strict and prefix accuracy

Strict trace accuracy requires every emitted belief-state transition to match.
Correct-prefix accuracy is the fraction of the reference trace completed before
the first discrepancy. Final-answer accuracy evaluates only the endpoint.

### Representation metrics

Linear CKA measures similarity between aligned representational geometries.
Cosine similarity measures aligned state-vector direction. Stage 6 reports both
across model layers and span types. These metrics are correlational.

### Source-ID swap effect

Stage 7 swaps the identifier assigned to a relevant source with one assigned to
a distractor. The reported direct effect is the change in total log probability
favoring the new correct identifier over the old association. Positive values
mean the model follows the semantic source to its newly assigned identifier.

### Patch recovery

Activation-patching recovery divides the patch-induced log-probability change by
the model's own full prompt-swap effect. Approximately 100% means the patched
state transfers the complete observed counterfactual response. Values outside
0–100% are possible when a patch amplifies or reverses the direct effect.

## Models and execution scope

Behavioral experiments use revision-pinned local GGUF artifacts for:

- Qwen2.5-1.5B-Instruct Q4_K_M;
- LiquidAI LFM2.5-1.2B-Instruct Q4_K_M;
- Gemma 4 E2B instruction-tuned Q4_0;
- Gemma 4 E4B instruction-tuned Q4_0;
- Tiny Aya Global Q4_K_M where specified.

Stage 6 and Stage 7 require hidden states and therefore use official Hugging Face
BF16 Qwen, LFM, and Gemma checkpoints. Tiny Aya is excluded from the
mechanistic experiments because its official Transformers checkpoint is gated
and the local GGUF runtime does not expose residual states.

Exact revisions and hashes are recorded in
[`../MODEL_PROVENANCE.md`](../MODEL_PROVENANCE.md). Hardware, drivers, CUDA
toolkit, build configuration, and offload settings are recorded in
[`../GPU_PROVENANCE.md`](../GPU_PROVENANCE.md).

## Datasets

### Synthetic citation tasks

The initial tasks are deterministic fictional QA datasets with canonical source
keys and rendered identifier mappings. They isolate identifier effects but do
not represent real retrieval quality.

### MuSiQue

The primary multi-hop cohort contains 100 balanced answerable examples: 34
two-hop, 33 three-hop, and 33 four-hop. The held-out confirmation uses a disjoint
balanced cohort of 100 examples. Prompts were jointly screened with all five
native tokenizers and retained only when they fell within the configured
2,000–3,700-token range.

### LongProc

The cross-tokenizer subset contains 25 `tom_tracking_2k` examples. Every prompt
is 2,048–4,096 tokens and every reference trace is 1,024–2,048 tokens under all
four tested tokenizers. Dataset revisions, filtering rules, and hashes are in
[`../DATASET_PROVENANCE.md`](../DATASET_PROVENANCE.md).

### Synthetic entity resolution

Stage 8 uses 40 synthetic account-resolution examples under four entity
representations. No real PII is processed. Stage 9 likewise uses deterministic
synthetic requests and records.

## Selected results

### Stage 1 Qwen result

| Sources | Identifier | Answer content | Strict citation | Exact binding | Input tokens | Output tokens | Latency |
|---:|---|---:|---:|---:|---:|---:|---:|
| 5 | Structured | 100% | 68% | 96% | 234.6 | 13.6 | 1.74 s |
| 5 | UUID | 98% | 29% | 63% | 385.5 | 49.9 | 4.36 s |
| 20 | Structured | 90% | 7% | 66% | 639.3 | 14.8 | 5.27 s |
| 20 | UUID | 92% | 34% | 37% | 1,237.4 | 46.5 | 11.96 s |

The reversal between strict citation and relaxed binding at twenty sources is a
formatting effect, not evidence of better UUID source selection.

### Held-out MuSiQue binding effects

Effects are UUID minus numeric binding recall in percentage points.

| Model | 15 sources | 20 sources |
|---|---:|---:|
| Tiny Aya | -11.4 [-17.1, -6.1] | -14.8 [-20.2, -9.7] |
| LFM 1.2B | -7.5 [-13.4, -1.6] | -6.1 [-12.1, -0.5] |
| Qwen 1.5B | -6.8 [-12.3, -1.2] | -0.8 [-5.1, +3.2] |
| Gemma E2B | -3.1 [-8.3, +2.4] | -4.8 [-10.1, +0.1] |
| Gemma E4B | -5.8 [-10.9, -0.9] | -3.4 [-9.1, +2.3] |

### LongProc

| Model | Exact trace | Mean correct prefix | Final answer | Full trace emitted | Mean output |
|---|---:|---:|---:|---:|---:|
| Qwen | 0% | 1.2% | 4% | 96% | 2,027 |
| LFM | 0% | 0.9% | 28% | 0% | 434 |
| Gemma E2B | 0% | 9.4% | 16% | 80% | 1,987 |
| Gemma E4B | 8% | 38.0% | 76% | 96% | 1,996 |

### Stage 6 representation gate

| Model | Label CKA embedding -> peak | Min fact CKA | Final question / pre-citation / citation cosine | Gate |
|---|---:|---:|---:|---|
| Qwen | 0.325 -> 0.858 | 0.969 | 0.999 / 0.828 / 0.721 | Pass |
| LFM | 0.697 -> 0.895 | 0.970 | 0.983 / 0.598 / 0.372 | Pass |
| Gemma E2B | 0.434 -> 0.931 | 0.941 | 0.994 / 0.825 / 0.798 | Pass |
| Gemma E4B | 0.435 -> 0.952 | 0.979 | 0.991 / 0.497 / 0.512 | Pass |

### Stage 7 direct source-ID swaps

Effects are total citation log-probability changes. Positive follows the
relevant source to the new identifier.

| Model | n | Structured | Random compact | UUID |
|---|---:|---:|---:|---:|
| Qwen | 8 | +2.63 [0.78, 4.35] | +4.98 [2.45, 7.44] | +1.90 [-1.32, 4.93] |
| LFM | 8 | -0.78 [-5.26, 3.88] | -9.08 [-16.98, -1.00] | -2.56 [-10.28, 6.82] |
| Gemma E2B | 4 | +2.16 [-16.25, 25.78] | +7.50 [1.33, 15.42] | +18.62 [7.52, 29.71] |
| Gemma E4B | 2 | +11.56 [-14.02, 37.14] | +15.17 [9.09, 21.25] | +48.73 [26.70, 70.75] |

Gemma results are pilot-level because of GPU-memory-constrained cohort sizes.

### Stage 8 aggregate accuracy

| Model | Raw | Random masked | Untyped | Typed | Typed - untyped |
|---|---:|---:|---:|---:|---:|
| Qwen | 90.0% | 85.0% | 80.0% | 97.5% | +17.5 pp [7.5, 30.0] |
| LFM | 27.5% | 2.5% | 0.0% | 7.5% | +7.5 pp [0.0, 17.5] |
| Gemma E2B | 100% | 100% | 92.5% | 100% | +7.5 pp [0.0, 17.5] |
| Gemma E4B | 100% | 100% | 92.5% | 100% | +7.5 pp [0.0, 17.5] |
| Tiny Aya | 87.5% | 82.5% | 97.5% | 97.5% | 0.0 pp |

Raw-value exposure was 85–100% in raw-condition outputs and 0% in every masked
condition. This describes controlled prompt exposure, not anonymity.

## Reproduction

Run the deterministic test suite:

```bash
.venv/bin/python scripts/run_tests.py
```

Regenerate all article figures:

```bash
.venv/bin/python blog/scripts/build_figures.py
```

Run or validate representative experiment families:

```bash
# Initial citation experiment
PYTHONPATH=src .venv/bin/python experiments/01_citation_mve.py

# Public MuSiQue stages
.venv/bin/python scripts/run_musique_stages.py \
  --config configs/musique/stages_2_4_qwen15b.yaml

# LongProc
.venv/bin/python scripts/run_longproc.py \
  --config configs/longproc/tom_tracking_2k_qwen15b.yaml

# Reasoning-budget confirmation
.venv/bin/python scripts/run_stage5.py \
  --config configs/experiments/stage5_confirm_qwen15b.yaml

# Hidden-state recording and causal interventions
.venv/bin/python scripts/run_stage6.py \
  --config configs/experiments/stage6_qwen25_15b.yaml
.venv/bin/python scripts/run_stage7.py \
  --config configs/experiments/stage7_qwen25_15b.yaml

# Synthetic entity canonicalization
.venv/bin/python scripts/run_stage8.py \
  --config configs/experiments/stage8_pii_qwen15b.yaml

# Operational IR boundary
.venv/bin/python experiments/09_system_ir.py \
  --requests 500 --records-per-request 20
```

Model experiments can require large local artifacts, CUDA support, and
substantial runtime. The checked-in raw and processed results allow the reports
and figures to be reproduced without rerunning inference.

## Interpretation boundaries

- The findings do not establish that aliases universally improve answer
  accuracy.
- The token-matched controls reject the idea that one structured syntax is
  universally best.
- Stage 5 does not establish a universal monotonic reasoning-budget penalty.
- Stage 6 geometry is correlational; Stage 7 causal effects are
  architecture-dependent.
- Masking reduces model exposure but does not provide anonymity, encryption, or
  authorization.
- Structural validation rejects malformed references but cannot detect every
  semantically wrong registered reference.
- Stage 9 is a reference implementation and research boundary, not a production
  security certification.

For the full per-model and per-stage reports, start with
[`../IMPLEMENTATION_STATUS.md`](../IMPLEMENTATION_STATUS.md) and the `FINDINGS_*.md`
files in the repository root.
