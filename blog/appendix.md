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
| Held-out MuSiQue | 2,400 generations | Six models | Does the primary binding result replicate? | All 12 cell estimates favor numeric; 7/12 intervals exclude zero. |
| LongProc | 125 generations | Five models | Does long generation imply procedural correctness? | No; endpoint, trace, completion, and length diverge sharply. |
| Stage 5 pilot | 2,400 two-pass generations | Five models | Does identifier cost interact monotonically with scratchpad budget? | Pilot effects were heterogeneous and required confirmation. |
| Stage 5 confirmation | 3,200 two-pass generations | Qwen, Gemma E2B, Tiny Aya retained cells | Does the interaction replicate? | No broad monotonic interaction; output cost persists. |
| Stage 6 | 960 paired forward passes | Qwen, LFM, Gemma E2B/E4B BF16 | Do different surfaces converge internally? | Fact geometry is stable; labels converge; citation states specialize late. |
| Stage 7 | 66 swaps and 1,056 interventions | Qwen, LFM, Gemma E2B/E4B | Is the source-to-ID relationship causal and transferable? | Yes, but causal direction and timing are architecture-dependent. |
| Stage 8 | 960 generations | Six models | Do typed handles help beyond citation formatting? | Significant controlled gains appear in Qwen, Tiny Aya, and LFM 2.6B; not universal. |
| Stage 9 | 500 valid requests and 5,000 adversarial test cases | Deterministic reference system | Can a typed IR enforce representation integrity? | Yes for structural classes; not for a wrong but registered handle. |
| Stage 1 factorial ablation | 1,600 generations | LFM 2.6B | Is Stage 1 failure decoding or capacity? | Truncation was a decoding artifact; closed-thinking prefill eliminates budget sensitivity (100% 5-src, 60% 20-src UUID recall). |
| MuSiQue budget sensitivity | 400 generations | LFM 2.6B | Does doubling budget to 512 tokens eliminate 15-source UUID penalty? | No; penalty remains -10.58 pp [-16.83, -4.50]; truncation drops to 37%. |
| Stage 1 scaled (N=500) | 16,000 generations | 8 models | Does the single-hop attribution deficit replicate at scale? | Yes; UUID binding drops up to -28.4 pp (p=6.14e-20) on Qwen 1.5B, -42.0 pp on LFM 1.2B. |
| MuSiQue scaled (N=500) | 16,000 generations | 8 models | Is the multi-hop attribution deficit universal at scale? | Yes; 16/16 cells negative, 16/16 paired intervals strictly exclude zero in negative direction. |
| Stage 8 scaled (N=500) | 16,000 generations | 8 models | Do typed handles outperform untyped across diverse architectures? | Yes; +8.0 pp gain on token-matched models (p=4.74e-48), 757 typed wins vs 20 losses fleet-wide. |
| Stage 5 full fleet | 3,840 two-pass generations (7,680 calls) | 8 models | How does reasoning budget interact with UUIDs across regimes? | Severe UUID penalties at small budgets (up to -54.2 pp); monotonic recovery fails. |
| LongProc 7-model suite | 175 generations | 7 models | How do advanced small models track belief states? | Qwen 3.5 4B achieves 68% answer, 100% full trace, and 16.0% strict trace (fleet highest). |

The evidence base comprises 18,605 primary behavioral records (24,205 primary model
calls) plus 2,000 post-hoc validation generations, totaling 20,605 records and
26,205 model calls across Stages 0–8. Each Stage 5 record contains two sequential
model calls. Stage 5 therefore comprises 5,600 two-pass generations and 11,200 model calls:
2,400 pilot generations (4,800 calls) plus 3,200 confirmatory generations (6,400 calls).
Systematically expanding the fleet to full parity across all eight models and executing a
48,000-generation scaled confirmatory program ($N=500$ across Stages 1, 8, and MuSiQue) brings
the grand total to **76,515 behavioral records and 83,555 model calls**, alongside
960 BF16 forward passes, 1,056 causal interventions, and 5,500 deterministic systems executions.
Forward passes, causal interventions, valid systems requests, and adversarial test cases
are reported separately.

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

Behavioral experiments use revision-pinned local GGUF artifacts across eight model configurations:

- Qwen2.5-1.5B-Instruct Q4_K_M;
- Qwen3.5-2B-Instruct Q4_K_M;
- Qwen3.5-4B-Instruct Q4_K_M;
- LiquidAI LFM2.5-1.2B-Instruct Q4_K_M;
- LiquidAI LFM2.5-2.6B-Instruct Q4_K_M;
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

This baseline was model-dependent. Gemma E2B showed the opposite binding
direction in the unrescored pilot: UUID minus structured was +37 points at five sources (95% CI +24 to
+50) and +25 points at twenty sources (+16 to +34). Gemma E4B was at ceiling
for both formats. Crucially, offline inspection revealed that the apparent Gemma E2B
advantage was driven by the parser dropping same-line citations (`ANSWER: ..., CITATIONS: ...`).
Upon full offline rescoring with relaxed same-line citation extraction, Gemma E2B is at ceiling
in both formats (-0.2 pp at 5 sources, +0.6 pp at 20 sources). The later held-out MuSiQue experiment is therefore the primary
cross-model confirmation rather than evidence that Stage 1 generalized
uniformly.

### Scaled Stage 1 citation effects ($N=500$, 16,000 generations)

| Model Family | Sources | Structured Content | UUID Content | Structured Strict | UUID Strict | Structured Binding | UUID Binding | Paired Binding Δ (95% CI) | Exact p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen 1.5B | 5 | 99.4% | 99.6% | 72.8% | 53.8% | 98.6% | 81.2% | **-17.4 pp** [-21.0, -14.0] | 1.68e-22 |
| Qwen 1.5B | 20 | 85.4% | 88.8% | 12.6% | 36.6% | 68.8% | 40.4% | **-28.4 pp** [-34.0, -22.6] | 6.14e-20 |
| Qwen 3.5 2B | 5 | 100.0% | 99.8% | 99.4% | 98.0% | 99.4% | 98.0% | -1.4 pp [-2.8, +0.0] | 0.0923 |
| Qwen 3.5 2B | 20 | 100.0% | 100.0% | 97.0% | 94.0% | 97.0% | 94.0% | **-3.0 pp** [-5.6, -0.4] | 0.0357 |
| Qwen 3.5 4B | 5 | 100.0% | 100.0% | 100.0% | 96.0% | 100.0% | 100.0% | +0.0 pp [+0.0, +0.0] | 1.0000 |
| Qwen 3.5 4B | 20 | 100.0% | 100.0% | 99.8% | 97.4% | 99.8% | 98.0% | **-1.8 pp** [-3.2, -0.6] | 0.0117 |
| LFM 1.2B | 5 | 100.0% | 99.8% | 2.0% | 11.2% | 55.0% | 13.0% | **-42.0 pp** [-47.4, -36.6] | 1.06e-40 |
| LFM 1.2B | 20 | 96.4% | 96.2% | 0.0% | 1.8% | 3.8% | 2.2% | -1.6 pp [-3.4, +0.0] | 0.0963 |
| LFM 2.6B | 5 | 98.2% | 99.6% | 66.0% | 95.8% | 97.0% | 96.4% | -0.6 pp [-2.6, +1.4] | 0.7011 |
| LFM 2.6B | 20 | 66.8% | 85.4% | 40.0% | 61.8% | 62.0% | 61.8% | -0.2 pp [-5.0, +4.6] | 1.0000 |
| Gemma E2B | 5 | 100.0% | 100.0% | 98.0% | 99.4% | 99.8% | 99.6% | -0.2 pp [-1.0, +0.4] | 1.0000 |
| Gemma E2B | 20 | 99.8% | 99.8% | 76.4% | 99.6% | 99.2% | 99.8% | +0.6 pp [-0.2, +1.6] | 0.3750 |
| Gemma E4B | 5 | 100.0% | 100.0% | 100.0% | 91.8% | 100.0% | 100.0% | +0.0 pp [+0.0, +0.0] | 1.0000 |
| Gemma E4B | 20 | 100.0% | 100.0% | 96.2% | 82.6% | 100.0% | 100.0% | +0.0 pp [+0.0, +0.0] | 1.0000 |
| Tiny Aya | 5 | 100.0% | 100.0% | 52.0% | 64.0% | 96.0% | 79.6% | **-16.4 pp** [-20.2, -12.6] | 3.30e-16 |
| Tiny Aya | 20 | 99.4% | 99.8% | 43.6% | 70.0% | 76.8% | 73.6% | -3.2 pp [-8.4, +2.0] | 0.2635 |

### Held-out MuSiQue binding effects (100-item pilot)

Effects are UUID minus numeric binding recall in percentage points across 100 held-out questions (2,400 initial generations, expanded to 3,200 across 8 models).

| Model | 15 sources | 20 sources |
|---|---:|---:|
| Tiny Aya | -11.4 [-17.1, -6.1] | -14.8 [-20.2, -9.7] |
| LFM 1.2B | -7.5 [-13.4, -1.6] | -6.1 [-12.1, -0.5] |
| LFM 2.6B | -10.4 [-16.3, -4.5] | -4.7 [-10.2, +0.8] |
| Qwen 1.5B | -6.8 [-12.3, -1.2] | -0.8 [-5.1, +3.2] |
| Qwen 3.5 2B | -0.3 [-4.7, +4.1] | -5.8 [-11.4, -0.3] |
| Qwen 3.5 4B | -3.2 [-7.8, +1.3] | -2.9 [-7.9, +1.9] |
| Gemma E2B | -3.1 [-8.3, +2.4] | -4.8 [-10.1, +0.1] |
| Gemma E4B | -5.8 [-10.9, -0.9] | -3.4 [-9.1, +2.3] |

### Scaled MuSiQue confirmation ($N=500$, 16,000 generations)

Effects are UUID minus numeric binding recall across 500 balanced MuSiQue questions across all eight models. The cohort encompasses 51 items from the initial 100-item cohort, 48 from the held-out cohort, and 401 genuinely new items. All 16 cells show negative deltas; all 16 unadjusted paired 95% bootstrap confidence intervals (ordinary paired percentile bootstrap, 10,000 resamples) strictly exclude zero in the negative direction. Under Holm-Bonferroni correction at $\alpha=0.05$, 14 of 16 cells survive. An analysis-only sensitivity restricted to the 401 disjoint items (`results/analysis/musique_500_disjoint_401.json`) confirms the result with 16/16 cells negative and 15/16 intervals excluding zero.

| Model | Sources | Numeric binding | UUID binding | UUID − numeric binding (95% CI) | Numeric answer F1 | UUID answer F1 |
|---|---:|---:|---:|---:|---:|---:|
| Tiny Aya | 15 | 42.4% | 29.4% | **-13.0 pp** [-15.5, -10.5] | 26.3% | 33.7% |
| Tiny Aya | 20 | 39.4% | 23.6% | **-15.8 pp** [-18.4, -13.3] | 26.7% | 29.3% |
| LFM 1.2B | 15 | 22.1% | 18.2% | **-3.9 pp** [-6.5, -1.3] | 8.5% | 8.2% |
| LFM 1.2B | 20 | 16.7% | 9.9% | **-6.8 pp** [-9.0, -4.6] | 7.3% | 5.8% |
| LFM 2.6B | 15 | 23.7% | 16.4% | **-7.3 pp** [-9.8, -4.9] | 26.5% | 25.1% |
| LFM 2.6B | 20 | 22.3% | 13.3% | **-9.0 pp** [-11.8, -6.3] | 22.6% | 20.3% |
| Qwen 1.5B | 15 | 21.8% | 15.8% | **-6.0 pp** [-8.6, -3.4] | 18.8% | 18.9% |
| Qwen 1.5B | 20 | 17.0% | 8.9% | **-8.0 pp** [-10.5, -5.6] | 17.5% | 19.3% |
| Gemma E2B | 15 | 45.7% | 41.7% | **-4.0 pp** [-6.2, -1.8] | 16.3% | 16.1% |
| Gemma E2B | 20 | 44.9% | 40.2% | **-4.7 pp** [-6.9, -2.5] | 14.5% | 15.0% |
| Gemma E4B | 15 | 47.0% | 40.6% | **-6.4 pp** [-8.9, -3.9] | 23.6% | 23.6% |
| Gemma E4B | 20 | 43.0% | 36.0% | **-7.0 pp** [-9.2, -4.7] | 22.9% | 20.7% |
| Qwen 3.5 2B | 15 | 36.0% | 29.8% | **-6.2 pp** [-8.6, -3.9] | 29.7% | 29.1% |
| Qwen 3.5 2B | 20 | 33.1% | 28.3% | **-4.8 pp** [-7.0, -2.6] | 29.1% | 28.6% |
| Qwen 3.5 4B | 15 | 61.7% | 58.6% | **-3.2 pp** [-5.4, -0.9] | 42.0% | 39.3% |
| Qwen 3.5 4B | 20 | 58.5% | 56.3% | **-2.1 pp** [-4.2, -0.1] | 40.1% | 38.8% |

### LongProc (7-Model Suite)

| Model | Exact trace | Mean correct prefix | Final answer | Full trace emitted | Mean output |
|---|---:|---:|---:|---:|---:|
| Qwen 1.5B | 0.0% | 1.2% | 4.0% | 96% | 2,027 |
| Qwen 3.5 2B | 0.0% | 1.2% | 28.0% | 72% | 1,921 |
| Qwen 3.5 4B | 16.0% | 40.6% | 68.0% | 100% | 1,929 |
| LFM 1.2B | 0.0% | 0.9% | 28.0% | 0% | 434 |
| LFM 2.6B | 0.0% | 0.2% | 4.0% | 16% | 1,086 |
| Gemma E2B | 0.0% | 9.4% | 16.0% | 80% | 1,987 |
| Gemma E4B | 8.0% | 38.0% | 76.0% | 96% | 1,996 |

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

### Stage 8 aggregate accuracy (40-item pilot)

| Model | Raw | Random masked | Untyped | Typed | Typed - untyped |
|---|---:|---:|---:|---:|---:|
| Qwen 1.5B | 90.0% | 85.0% | 80.0% | 97.5% | +17.5 pp [7.5, 30.0] |
| LFM 1.2B | 27.5% | 2.5% | 0.0% | 7.5% | +7.5 pp [0.0, 17.5] |
| LFM 2.6B | 92.5% | 52.5% | 27.5% | 97.5% | +70.0 pp [52.5, 85.0] |
| Gemma E2B | 100% | 100% | 92.5% | 100% | +7.5 pp [0.0, 17.5] |
| Gemma E4B | 100% | 100% | 92.5% | 100% | +7.5 pp [0.0, 17.5] |
| Tiny Aya | 87.5% | 82.5% | 97.5% | 97.5% | 0.0 pp |

Raw-value exposure was 85–100% in raw-condition outputs and 0% in every masked
condition. This describes controlled prompt exposure, not anonymity.

### Scaled Stage 8 entity canonicalization ($N=500$, 16,000 generations)

| Model | Raw | Random masked | Untyped | Typed | Typed − untyped (95% CI) | Exact p | Length token Δ |
|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen 1.5B | 94.8% | 82.0% | 81.0% | 92.4% | **+11.4 pp** [+8.0, +14.6] | 7.66e-12 | +0.0 |
| Qwen 3.5 2B | 48.6% | 61.0% | 96.6% | 98.6% | **+2.0 pp** [+0.6, +3.4] | 0.0129 | +0.0 |
| Qwen 3.5 4B | 100.0% | 99.8% | 99.6% | 100.0% | +0.4 pp [+0.0, +1.0] | 0.5000 | +0.0 |
| LFM 1.2B | 29.4% | 5.2% | 0.0% | 22.0% | **+22.0 pp** [+18.4, +25.6] | 1.54e-33 | +35.0 |
| LFM 2.6B | 94.6% | 56.6% | 18.2% | 97.0% | **+78.8 pp** [+75.0, +82.4] | 2.46e-115 | +35.0 |
| Gemma E2B | 100.0% | 100.0% | 85.8% | 98.8% | **+13.0 pp** [+10.0, +16.2] | 8.19e-18 | +0.0 |
| Gemma E4B | 100.0% | 99.6% | 86.4% | 99.8% | **+13.4 pp** [+10.4, +16.4] | 1.36e-20 | +0.0 |
| Tiny Aya | 82.4% | 77.8% | 91.2% | 97.6% | **+6.4 pp** [+4.0, +9.0] | 4.43e-07 | +36.0 |

In the strict token-matched subset (Qwen 1.5B, Qwen 3.5 2B, Qwen 3.5 4B, Gemma E2B, Gemma E4B; 2,500 pairs),
typed handles showed a **+8.0 percentage-point advantage** ($p = 4.74 \times 10^{-48}$). Across all 4,000 paired
comparisons, typed handles won 757 times vs 20 losses ($p = 5.34 \times 10^{-195}$). Output PII exposure was
92%–100% under raw prompts and **0.0% across all 16,000 generations under masked/typed representations**.

### Post-hoc validation studies

#### Stage 1 factorial ablation (LFM 2.5-2.6B)

A 1,600-generation factorial ablation crossing chat template / thinking mode
(`default` reasoning vs `prefill` closed thinking `<think>\n</think>\n`) with
generation output budget (80 vs 512 tokens) across 100 paired Stage 1 items at
5 and 20 sources:

| Sources | Condition | Arm | Content Acc | Strict Ans Acc | Relaxed Recall | Strict Cit Syntax | Truncation Rate | Mean Output Tokens |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 5 | Structured | `default_80` | 0.0% | 0.0% | 0.0% | 0.0% | 100.0% | 80.0 |
| 5 | Structured | `default_512` | 96.0% | 96.0% | 99.0% | 19.0% | 6.0% | 388.2 |
| 5 | Structured | `prefill_80` | 97.0% | 92.0% | 98.0% | 66.0% | 0.0% | 18.0 |
| 5 | Structured | `prefill_512` | 97.0% | 92.0% | 98.0% | 66.0% | 0.0% | 18.0 |
| 5 | UUID | `default_80` | 1.0% | 0.0% | 0.0% | 0.0% | 100.0% | 80.0 |
| 5 | UUID | `default_512` | 96.0% | 96.0% | 98.0% | 59.0% | 82.0% | 505.6 |
| 5 | UUID | `prefill_80` | 99.0% | 77.0% | 100.0% | 97.0% | 0.0% | 37.6 |
| 5 | UUID | `prefill_512` | 99.0% | 77.0% | 100.0% | 97.0% | 0.0% | 37.6 |
| 20 | Structured | `default_80` | 32.0% | 0.0% | 0.0% | 0.0% | 100.0% | 80.0 |
| 20 | Structured | `default_512` | 82.0% | 61.0% | 83.0% | 23.0% | 35.0% | 400.7 |
| 20 | Structured | `prefill_80` | 69.0% | 59.0% | 74.0% | 43.0% | 0.0% | 20.6 |
| 20 | Structured | `prefill_512` | 69.0% | 59.0% | 74.0% | 43.0% | 0.0% | 20.6 |
| 20 | UUID | `default_80` | 2.0% | 0.0% | 0.0% | 0.0% | 100.0% | 80.0 |
| 20 | UUID | `default_512` | 12.0% | 11.0% | 15.0% | 9.0% | 84.0% | 494.0 |
| 20 | UUID | `prefill_80` | 85.0% | 85.0% | 60.0% | 57.0% | 0.0% | 35.0 |
| 20 | UUID | `prefill_512` | 85.0% | 85.0% | 60.0% | 57.0% | 0.0% | 35.0 |

Outputs under `prefill_80` and `prefill_512` were byte-identical across all cells.

#### MuSiQue budget sensitivity (LFM 2.5-2.6B)

A 400-generation post-hoc study evaluating whether doubling the output token cap
from 256 to 512 tokens resolves the 15-source UUID binding penalty on the 100
held-out MuSiQue examples:

| Sources | Budget | Numeric Truncation | UUID Truncation | Numeric Recall | UUID Recall | Recall Delta (UUID - Num) | 95% Bootstrap CI |
|---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 15 | 256 tokens | 33.0% | 50.0% | 24.2% | 13.8% | **-10.42 pp** | [-16.25, -4.50] pp |
| 15 | 512 tokens | 25.0% | 37.0% | 26.3% | 15.8% | **-10.58 pp** | [-16.83, -4.50] pp |
| 20 | 256 tokens | 31.0% | 51.0% | 19.8% | 15.2% | **-4.67 pp** | [-10.08, +0.83] pp |
| 20 | 512 tokens | 23.0% | 39.0% | 21.4% | 17.4% | **-4.00 pp** | [-10.00, +1.83] pp |

Answer F1 differences remained centered near zero (-7.50 pp [-15.46, +0.55] at 256
tokens vs -4.50 pp [-13.16, +4.29] at 512 tokens for 15 sources). The 15-source
binding penalty was robust to doubling the budget. Residual truncation remained at
37%–39% under UUIDs.

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
substantial runtime. Processed results and generated figures are checked in, so
the reports and empirical charts can be reproduced without rerunning inference.
Raw generation logs are retained locally and hash-recorded in the findings and
provenance files, but are not tracked in Git.

The hidden-state experiments used two intentionally separate dependency
environments: Qwen/LFM used `transformers==4.57.6`, while Gemma 4 used
`transformers==5.20.2`. Exact package versions are recorded in
[`../MODEL_PROVENANCE.md`](../MODEL_PROVENANCE.md) and the historical constraints
files for [Qwen/LFM](../constraints/stage6-qwen-lfm.txt) and
[Gemma 4](../constraints/stage6-gemma4.txt). The broad `hf` project extra is
convenient for current runs, not a historical lockfile.

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
