# Technical Appendix: Symbolic IR Experiments

This appendix supports [The Hidden Cost of UUIDs](symbolic-ir-engineering-blog.md).
It separates completed empirical measurements from interpretation and proposed systems
guidance.

## Evidence ledger

| Experiment | Scale | Models | Primary question | Main conclusion |
|---|---:|---|---|---|
| Stage 0 | 20 records | Oracle smoke backend | Does the complete pipeline run, resume, and score? | Yes; infrastructure gate passed. |
| Stage 1 MVE ($N=500$) | 12,000 generations | Six primary local models | Do compact identifiers change transport cost and citation binding? | UUID cost is high; single-hop binding deficits replicate at scale. |
| MuSiQue Stages 2–4 | 7,500 generations | Five primary local models | Does the effect survive multi-hop retrieval and controls? | UUID binding is directionally worse across primary cells. |
| Held-out MuSiQue | 2,400 generations | Six primary local models | Does the primary binding result replicate on unseen items? | All 12 cell estimates favor numeric; 7/12 intervals exclude zero. |
| MuSiQue Scaled ($N=500$) | 12,000 generations | Six primary local models | Is multi-hop binding degradation universal at scale? | Yes; all 12 cells negative, all 12 paired bootstrap CIs strictly exclude zero. |
| LongProc ToM Tracking | 150 generations | Six primary local models | Does long generation imply procedural correctness? | No; endpoint, trace, completion, and length diverge sharply. |
| Stage 5 Pilot | 2,880 model calls | Six primary local models | Does identifier cost interact monotonically with scratchpad budget? | Pilot effects were heterogeneous across architectures. |
| Stage 5 Confirmation | 4,800 model calls | Six primary local models | Does the interaction replicate under balanced design? | No monotonic recovery; reasoning expansion does not erase identifier penalty. |
| Stage 6 Geometry | 1,440 forward passes | Six primary local models | Do different surfaces converge internally? | Fact geometry is stable; labels converge; citation states specialize late. |
| Stage 7 Interventions | 144 swaps, 2,160 patches | Six primary local models | Is the source-to-ID relationship causal and transferable? | Yes; causal rebinding confirmed across all 6 models with architecture-dependent onset. |
| Stage 8 Entity Resolution ($N=500$) | 12,000 local + 4,000 frontier | Six local + 2 frontier models | Do typed handles prevent PII exposure and aid resolution? | Significant gains in 4 models (2 ceiling-limited); 0.0% PII leakage under IR. |
| Stage 9 Systems Boundary | 500 valid + 5,000 attacks + 500 probes | Deterministic reference system | Can a typed IR enforce representation integrity? | Yes for structural classes; not for a wrong but registered handle. |
| Frontier Behavioral Validation | 13,760 completed calls | Four frontier API models | Do closed-weights commercial APIs replicate behavioral patterns? | Replicates attribution deficits; adaptive reasoning reduces surface sensitivity. |

The primary local behavioral program comprises **46,230 completed model calls** across Stages 1, 5, 8, MuSiQue, and LongProc. The commercial frontier API extension adds **13,760 completed model calls** (6,880 Anthropic and 6,880 OpenAI across all four frontier models). Mechanistic investigations comprise **1,440 paired BF16 forward passes** (Stage 6) and **2,304 causal interventions** (144 counterfactual prompt swaps and 2,160 activation patches across Stage 7) across all six primary open-weights models. Software evaluations include **6,000 deterministic systems executions** (500 valid requests, 5,000 adversarial payloads, and 500 semantic boundary probes, plus 499 cross-request isolation checks). Forward passes, causal interventions, and deterministic software tests are reported separately.

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

### Primary Local Cohort (Six Models)

Behavioral experiments use revision-pinned local GGUF artifacts across six primary edge model configurations (1.5B to 4B parameters) spanning three architectural families:

- **Qwen family:** Qwen2.5-1.5B-Instruct (`91cad511`), Qwen3.5-2B-Instruct (`f6d5376b`), Qwen3.5-4B-Instruct (`e87f1764`);
- **Google Gemma family:** Gemma 4 E2B Instruct (`675cff42`), Gemma 4 E4B Instruct (`4b4a2c1d`);
- **Cohere Tiny Aya family:** Tiny Aya Global 3.35B (`a602ea7e`).

### Mechanistically Evaluated Cohort (All Six Local Models)

Stage 6 and Stage 7 require direct access to hidden states, attention matrices, and residual-stream activations, and therefore use official Hugging Face BF16 checkpoints across the complete local fleet:
- Qwen2.5-1.5B-Instruct (`models/qwen2.5-1.5b-instruct-hf`)
- Gemma 4 E2B Instruct (`models/gemma-4-e2b-it-hf`)
- Gemma 4 E4B Instruct (`models/gemma-4-e4b-it-hf`)
- Tiny Aya Global (`models/tiny-aya-global-hf`)
- Qwen 3.5 2B (`models/qwen3.5-2b-hf`)
- Qwen 3.5 4B (`models/qwen3.5-4b-hf`)

### Frontier Behavioral Cohort (Four Models)

To test whether proprietary commercial APIs exhibit similar sensitivity to identifier formats, four frontier models were evaluated via batch APIs:
- Claude Haiku 5.5 (`claude-haiku-5-5`)
- Claude Sonnet 5.5 (`claude-sonnet-5-5`)
- GPT-6.1 Sol (`gpt-6-1-sol`)
- GPT-6 Luna (`gpt-6-luna`)

Because closed commercial APIs do not expose internal representations, frontier models are strictly excluded from mechanistic experiments (Stages 6 & 7) and are reported separately from local open-weights aggregates.

### Model Exclusion Note (Decision D-02)

During preliminary exploratory testing, two Liquid Foundation Model checkpoints (`lfm25_12b` and `lfm25_26b`) were evaluated. Under multi-hop retrieval contexts (15–20 passages), both checkpoints exhibited severe tokenizer anomalies, persistent repetition loops, and near-total format non-compliance resulting in massive truncation rates (up to 84–100% under standard decoding budgets). Post-hoc attempts to remediate these issues via closed-thinking prefill wrappers or budget expansion (up to 512 tokens) confirmed that the format failure was an intrinsic tokenizer/runtime incompatibility rather than a representation signal. Consequently, per Decision D-02, all LFM checkpoints were formally excluded from the primary study cohort and do not contribute to any published table, figure, or pooled statistic.

Exact revisions and hashes are recorded in [`../MODEL_PROVENANCE.md`](../MODEL_PROVENANCE.md). Hardware, drivers, CUDA toolkit, build configuration, and offload settings are recorded in [`../GPU_PROVENANCE.md`](../GPU_PROVENANCE.md).

## Datasets

### Synthetic citation tasks

The initial tasks are deterministic fictional QA datasets with canonical source
keys and rendered identifier mappings. They isolate identifier effects but do
not represent real retrieval quality.

### MuSiQue

The primary multi-hop cohort contains 100 balanced answerable examples: 34
two-hop, 33 three-hop, and 33 four-hop. The held-out confirmation uses a disjoint
balanced cohort of 100 examples. Prompts were jointly screened with all native tokenizers and retained only when they fell within the configured 2,000–3,700-token range. The scaled confirmatory benchmark expands this protocol to 500 balanced items.

### LongProc

The cross-tokenizer subset contains 25 `tom_tracking_2k` examples. Every prompt
is 2,048–4,096 tokens and every reference trace is 1,024–2,048 tokens under all
tested tokenizers. Dataset revisions, filtering rules, and hashes are in
[`../DATASET_PROVENANCE.md`](../DATASET_PROVENANCE.md).

### Synthetic entity resolution

Stage 8 uses synthetic account-resolution examples under four entity
representations (40 items in pilot, 500 items in scaled confirmation). No real PII is processed. Stage 9 likewise uses deterministic synthetic requests and records.

## Selected results

### Scaled Stage 1 citation effects ($N=500$, 12,000 generations across 6 primary models)

| Model Family | Sources | Structured Content | UUID Content | Structured Strict | UUID Strict | Structured Binding | UUID Binding | Paired Binding Δ (95% CI) | Exact p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen 1.5B | 5 | 99.4% | 99.6% | 72.8% | 53.8% | 98.6% | 81.2% | **-17.4 pp** [-21.0, -14.0] | 1.68e-22 |
| Qwen 1.5B | 20 | 85.4% | 88.8% | 12.6% | 36.6% | 68.8% | 40.4% | **-28.4 pp** [-34.0, -22.6] | 6.14e-20 |
| Qwen 3.5 2B | 5 | 100.0% | 99.8% | 99.4% | 98.0% | 99.4% | 98.0% | -1.4 pp [-2.8, +0.0] | 0.0923 |
| Qwen 3.5 2B | 20 | 100.0% | 100.0% | 97.0% | 94.0% | 97.0% | 94.0% | **-3.0 pp** [-5.6, -0.4] | 0.0357 |
| Qwen 3.5 4B | 5 | 100.0% | 100.0% | 100.0% | 96.0% | 100.0% | 100.0% | +0.0 pp [+0.0, +0.0] | 1.0000 |
| Qwen 3.5 4B | 20 | 100.0% | 100.0% | 99.8% | 97.4% | 99.8% | 98.0% | **-1.8 pp** [-3.2, -0.6] | 0.0117 |
| Gemma E2B | 5 | 100.0% | 100.0% | 98.0% | 99.4% | 99.8% | 99.6% | -0.2 pp [-1.0, +0.4] | 1.0000 |
| Gemma E2B | 20 | 99.8% | 99.8% | 76.4% | 99.6% | 99.2% | 99.8% | +0.6 pp [-0.2, +1.6] | 0.3750 |
| Gemma E4B | 5 | 100.0% | 100.0% | 100.0% | 91.8% | 100.0% | 100.0% | +0.0 pp [+0.0, +0.0] | 1.0000 |
| Gemma E4B | 20 | 100.0% | 100.0% | 96.2% | 82.6% | 100.0% | 100.0% | +0.0 pp [+0.0, +0.0] | 1.0000 |
| Tiny Aya | 5 | 100.0% | 100.0% | 52.0% | 64.0% | 96.0% | 79.6% | **-16.4 pp** [-20.2, -12.6] | 3.30e-16 |
| Tiny Aya | 20 | 99.4% | 99.8% | 43.6% | 70.0% | 76.8% | 73.6% | -3.2 pp [-8.4, +2.0] | 0.2635 |

### Held-out MuSiQue binding effects (100-item pilot, 2,400 generations across 6 primary models)

Effects are UUID minus numeric binding recall in percentage points across 100 held-out questions:

| Model Family | 15 sources | 20 sources |
|---|---:|---:|
| Tiny Aya Global | **-11.4 pp** [-17.1, -6.1] | **-14.8 pp** [-20.2, -9.7] |
| Qwen 2.5 1.5B | **-6.8 pp** [-12.3, -1.2] | -0.8 pp [-5.1, +3.2] |
| Qwen 3.5 2B | -0.3 pp [-4.7, +4.1] | **-5.8 pp** [-11.4, -0.3] |
| Qwen 3.5 4B | -3.2 pp [-7.8, +1.3] | -2.9 pp [-7.9, +1.9] |
| Gemma 4 E2B | -3.1 pp [-8.3, +2.4] | -4.8 pp [-10.1, +0.1] |
| Gemma 4 E4B | **-5.8 pp** [-10.9, -0.9] | -3.4 pp [-9.1, +2.3] |

### Scaled MuSiQue confirmation ($N=500$, 12,000 generations across 6 primary models)

Effects are UUID minus numeric binding recall across 500 balanced MuSiQue questions across all six primary models. All 12 cells show strictly negative point estimates, and all 12 unadjusted paired 95% bootstrap confidence intervals (10,000 resamples) strictly exclude zero in the negative direction. An analysis-only sensitivity restricted to the 401 disjoint items confirms the result with 12/12 cells negative and 12/12 intervals excluding zero.

| Model Family | Sources | Numeric binding | UUID binding | UUID − numeric binding (95% CI) | Numeric answer F1 | UUID answer F1 |
|---|---:|---:|---:|---:|---:|---:|
| Tiny Aya Global | 15 | 42.4% | 29.4% | **-13.0 pp** [-15.5, -10.5] | 26.3% | 33.7% |
| Tiny Aya Global | 20 | 39.4% | 23.6% | **-15.8 pp** [-18.4, -13.3] | 26.7% | 29.3% |
| Qwen 2.5 1.5B | 15 | 21.8% | 15.8% | **-6.0 pp** [-8.6, -3.4] | 18.8% | 18.9% |
| Qwen 2.5 1.5B | 20 | 17.0% | 8.9% | **-8.0 pp** [-10.5, -5.6] | 17.5% | 19.3% |
| Gemma 4 E2B | 15 | 45.7% | 41.7% | **-4.0 pp** [-6.2, -1.8] | 16.3% | 16.1% |
| Gemma 4 E2B | 20 | 44.9% | 40.2% | **-4.7 pp** [-6.9, -2.5] | 14.5% | 15.0% |
| Gemma 4 E4B | 15 | 47.0% | 40.6% | **-6.4 pp** [-8.9, -3.9] | 23.6% | 23.6% |
| Gemma 4 E4B | 20 | 43.0% | 36.0% | **-7.0 pp** [-9.2, -4.7] | 22.9% | 20.7% |
| Qwen 3.5 2B | 15 | 36.0% | 29.8% | **-6.2 pp** [-8.6, -3.9] | 29.7% | 29.1% |
| Qwen 3.5 2B | 20 | 33.1% | 28.3% | **-4.8 pp** [-7.0, -2.6] | 29.1% | 28.6% |
| Qwen 3.5 4B | 15 | 61.7% | 58.6% | **-3.2 pp** [-5.4, -0.9] | 42.0% | 39.3% |
| Qwen 3.5 4B | 20 | 58.5% | 56.3% | **-2.1 pp** [-4.2, -0.1] | 40.1% | 38.8% |

### LongProc Belief-State Tracking (150 GPU Generations across 6 Models)

| Model Family | Exact trace | Mean correct prefix | Final answer | Full trace emitted | Mean output |
|---|---:|---:|---:|---:|---:|
| Tiny Aya Global | 0.0% | 2.4% | 12.0% | 88% | 1,845 |
| Qwen 2.5 1.5B | 0.0% | 1.2% | 4.0% | 96% | 2,027 |
| Qwen 3.5 2B | 0.0% | 1.2% | 28.0% | 72% | 1,921 |
| Qwen 3.5 4B | 16.0% | 40.6% | 68.0% | 100% | 1,929 |
| Gemma 4 E2B | 0.0% | 9.4% | 16.0% | 80% | 1,987 |
| Gemma 4 E4B | 8.0% | 38.0% | 76.0% | 96% | 1,996 |

### Stage 6 Representation Gate (All Six Local Models)

| Model | Label CKA embedding -> peak | Min fact CKA | Final question / pre-citation / citation cosine | Gate |
|---|---:|---:|---:|---|
| Qwen 2.5 1.5B | 0.325 -> 0.858 (L13) | 0.969 | 0.999 / 0.828 / 0.721 | Pass |
| Gemma 4 E2B | 0.434 -> 0.931 (L15) | 0.941 | 0.994 / 0.825 / 0.798 | Pass |
| Gemma 4 E4B | 0.435 -> 0.952 (L25) | 0.979 | 0.991 / 0.497 / 0.512 | Pass |
| Tiny Aya Global | 0.413 -> 0.915 (L12) | 0.610 | 0.990 / 0.435 / 0.447 | Pass (Descriptive) |
| Qwen 3.5 2B | 0.316 -> 0.908 (L16) | 0.985 | 0.998 / 0.779 / 0.586 | Pass |
| Qwen 3.5 4B | 0.330 -> 0.919 (L17) | 0.984 | 0.998 / 0.733 / 0.606 | Pass |

### Stage 7 Direct Source-ID Swaps (All Six Local Models)

Effects are total citation log-probability changes across 144 prompt-level swaps. Positive values follow the relevant source to the new identifier.

| Model | n swaps | Structured | Random compact | UUID |
|---|---:|---:|---:|---:|
| Qwen 2.5 1.5B | 8 | +2.63 [0.78, 4.35] | +4.98 [2.45, 7.44] | +1.90 [-1.32, 4.93] |
| Gemma 4 E2B | 8 | +8.32 [-4.51, 21.47] | +5.18 [-0.17, 10.47] | +14.63 [7.35, 22.35] |
| Gemma 4 E4B | 8 | +37.41 [19.38, 54.95] | +50.91 [33.81, 66.98] | +48.30 [35.80, 63.53] |
| Tiny Aya Global | 8 | +2.17 [0.48, 3.84] | +5.38 [1.66, 9.08] | +7.56 [0.83, 14.73] |
| Qwen 3.5 2B | 8 | +1.91 [0.89, 3.19] | +6.20 [1.87, 10.96] | +4.67 [2.52, 6.53] |
| Qwen 3.5 4B | 8 | +4.23 [2.50, 5.95] | +5.04 [1.69, 8.01] | +3.58 [1.49, 6.14] |

### Scaled Stage 8 Entity Canonicalization ($N=500$, 12,000 Local Generations)

| Model Family | Raw | Random masked | Untyped | Typed | Typed − untyped (95% CI) | Exact p | Classification |
|---|---:|---:|---:|---:|---:|---:|---|
| Tiny Aya Global | 82.4% | 77.8% | 91.2% | 97.6% | **+6.4 pp** [+4.0, +9.0] | 4.43e-07 | Supported |
| Qwen 2.5 1.5B | 94.8% | 82.0% | 81.0% | 92.4% | **+11.4 pp** [+8.0, +14.6] | 7.66e-12 | Supported |
| Gemma 4 E2B | 100.0% | 100.0% | 85.8% | 98.8% | **+13.0 pp** [+10.0, +16.2] | 8.19e-18 | Supported |
| Gemma 4 E4B | 100.0% | 99.6% | 86.4% | 99.8% | **+13.4 pp** [+10.4, +16.4] | 1.36e-20 | Supported |
| Qwen 3.5 2B | 48.6% | 61.0% | 96.6% | 98.6% | **+2.0 pp** [+0.6, +3.4] | 0.0129 | Ceiling-limited |
| Qwen 3.5 4B | 100.0% | 99.8% | 99.6% | 100.0% | +0.4 pp [+0.0, +1.0] | 0.5000 | Ceiling-limited |

Across the 6 primary local models, 4 models demonstrate statistically supported accuracy improvements from typed handles under matched conditions, while 2 models exhibit ceiling-limited performance (at least 95% untyped and typed accuracy). Evaluated across 12,000 local generations (9,000 under masked conditions, 6,000 under typed/untyped), typed representations showed 251 pairwise improvements against 18 losses. Output PII exposure was 98.4%–100% under raw prompts and **0.0% across all 9,000 local masked generations and 3,000 frontier masked generations**.

## Figure-to-evidence index

Every visual figure in the study is generated directly from authoritative manifest and processed artifacts:

| Figure Asset | Figure Name | Associated Experiment ID | Evidence Tier | Model Scope | Primary Artifact Source |
|---|---|---|---|---|---|
| `01_raw_vs_symbolic.svg` | Representation Boundary | Systems Architecture | Conceptual Model | Universal | `src/symbolic_ir/` |
| `02_evidence_funnel.svg` | Study Evidence Accounting | Study Accounting | Meta-Evaluation | 6 Local + 4 Frontier | `results/audit/study_accounting.json` |
| `03_musique_confirmation.svg` | MuSiQue N=500 Citation Recall | `musique_scaled_500` | Primary Confirmation | 6 Primary Local Models | `results/processed/musique_500_confirmatory.json` |
| `03b_frontier_musique.svg` | Frontier MuSiQue Citation Gaps | `musique_scaled_500` (Frontier) | Behavioral Validation | 4 Frontier Models | `results/reports/frontier_evaluation_final.md` |
| `04_reasoning_budget.svg` | Stage 5 Reasoning Confirmation | `stage5_confirmatory` | Confirmatory Scaling | 6 Primary Local Models | `results/processed/stage5_confirmatory.json` |
| `04b_anthropic_reasoning.svg` | Frontier Reasoning Token Ablation | `frontier_reasoning_ablation` | Exploratory Behavioral | 2 Frontier Models | `results/processed/frontier_reasoning_summary.json` |
| `05_longproc.svg` | LongProc Multi-Step Trace | `long_context_tracking` | Confirmatory Procedural | 6 Primary Local Models | `results/processed/longproc_gpu_summary.json` |
| `06_stage6_geometry.svg` | Internal Representation Geometry | `stage6_geometry` | Mechanistic Correlational | 6 Eligible Local Models | `results/processed/stage6_qwen25_15b.json` |
| `07_stage7_swaps.svg` | Source-ID Causal Swaps (Figure 7A) | `stage7_interventions` | Mechanistic Causal | 6 Eligible Local Models | `results/processed/stage7_qwen25_15b.json` |
| `07b_stage7_patching.svg` | Residual-Stream Activation Patching (Figure 7B) | `stage7_interventions` | Mechanistic Causal | 6 Eligible Local Models | `results/processed/stage7_qwen25_15b.json` |
| `08_stage8_entities.svg` | Stage 8 Synthetic Resolution | `stage8_pii_500` | Confirmatory Canonicalization | 6 Local + 2 Frontier | `results/processed/stage8_pii_500_cross_model.json` |
| `09_trust_boundary.svg` | Trust & Operational Boundary | `stage9_systems_boundary` | Engineering Evaluation | Deterministic Software | `results/processed/stage9_system_eval.json` |

## Reproduction

Run the deterministic test suite:

```bash
.venv/bin/python -m pytest tests/
```

Regenerate all publication-grade figures:

```bash
.venv/bin/python blog/scripts/build_figures.py
```

Run or validate representative experiment families:

```bash
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

## Interpretation boundaries

- The findings do not establish that aliases universally improve answer accuracy.
- The token-matched controls reject the idea that one structured syntax is universally best.
- Stage 5 does not establish a universal monotonic reasoning-budget recovery.
- Stage 6 geometry is correlational; Stage 7 causal effects are architecture-dependent.
- Masking reduces model exposure but does not provide anonymity, encryption, or authorization.
- Structural validation rejects malformed references but cannot detect every semantically wrong registered reference.
- Stage 9 is a reference implementation and research boundary, not a production security certification.

For the full per-model and per-stage reports, see [`../IMPLEMENTATION_STATUS.md`](../IMPLEMENTATION_STATUS.md) and the `FINDINGS_*.md` files in the repository root.
