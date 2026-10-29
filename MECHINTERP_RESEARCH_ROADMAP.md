# Mechanistic Interpretability Research Roadmap

**Working program:** Mechanisms of symbolic source–identifier binding in language models  
**Repository baseline:** completed Stages 0–9  
**Roadmap scope:** implementation and empirical work for Stages 10–18  
**Primary paper target:** NeurIPS / ICLR / ICML, with an NLP-focused framing suitable for EMNLP  
**Status:** research design; no new empirical claims are made in this document

---

## 1. Executive research thesis

The existing evidence supports a useful but incomplete observation: models can preserve source-fact geometry across identifier formats while developing format-specific citation states late in the network. Qwen2.5 and the small Gemma pilots causally follow a semantic source to a counterfactually reassigned identifier, whereas LFM is causally sensitive but tends to preserve or strengthen the old association. The next paper should not be framed as “compact identifiers work better.” It should test a mechanistic claim:

> **Source selection, source–identifier binding, and identifier serialization are partially separable computations. Their locations, causal pathways, and failure modes differ systematically across transformer and hybrid sequence-model architectures.**

The strongest paper would establish all four of the following:

1. **A behavioral phenomenon:** controlled identifier transformations change reference fidelity in a predictable way across tasks, contexts, and model families.
2. **A causal mechanism:** specific model components and pathways mediate source selection, binding, and serialization.
3. **An architectural contrast:** conventional attention models and hybrid recurrent/attention models implement or fail the computation differently.
4. **A generalization result:** the discovered mechanism predicts behavior on held-out templates, identifiers, source counts, tasks, and preferably a natural dataset.

The LFM result is therefore not a nuisance to remove. It is the highest-value falsification case in the project. If the inversion is real, it can distinguish “the model contains a source-to-label representation” from “the model uses that representation correctly during counterfactual rebinding.” Qwen3.5 2B and 4B add an especially informative comparison because their hybrid DeltaNet/full-attention structure can reveal which operations require explicit attention and which can be carried in recurrent state.

---

## 2. Current evidence and the exact gap

### 2.1 What is already established

The repository already contains:

- controlled behavioral experiments across citation, reasoning-budget, long-context, entity-binding, and privacy-oriented settings;
- Stage 6 hidden-state comparisons over 80 semantic examples, three identifier formats, and four models;
- Stage 7 direct source-ID swaps and residual-stream patching;
- Stage 8 non-citation entity canonicalization;
- exact checkpoint, tokenizer, execution, and result provenance;
- reusable span alignment, activation recording, patching, logit-likelihood, probe, similarity, and swap utilities.

The current Stage 7 result is 66 paired source-ID swaps and 1,056 residual interventions. Its main strengths are clean counterfactual construction, exact sequence likelihoods, paired analysis, and explicit architectural comparison. Its main weaknesses are small sample sizes, coarse residual interventions, sparse layer sampling, and heavy use of teacher forcing.

### 2.2 Claims that the current evidence does not yet support

The existing study does **not** yet establish:

- a head-, MLP-, state-, or edge-level circuit;
- that any discovered component is necessary, sufficient, minimal, or specific;
- that a residual patch changes free-running citation generation;
- that source selection, binding, and serialization occupy distinct causal subspaces;
- that the LFM inversion is stable rather than cohort-, tokenization-, or implementation-specific;
- that mechanisms found on synthetic reasoning prompts generalize to natural evidence citation;
- that the BF16 mechanistic model and the quantized behavioral model exhibit the same phenomenon;
- that the final-layer patch is more than a positive-control transplantation of an already formed output state;
- that normalized recovery ratios are stable when the direct swap effect is small;
- that a shared circuit exists across models merely because their representational geometry is similar.

### 2.3 Reviewer-critical threats to validity

| Threat | Why a reviewer will care | Required response |
|---|---|---|
| Stage 7 uses n=8/8/4/2 | Effects and transition layers may be cohort-specific | Independent, preregistered confirmatory cohorts with power analysis |
| Teacher-forced targets | Mechanism may not govern autoregressive generation | Repeat decisive interventions during cached generation |
| Final-layer recovery near 100% | Expected when transplanting the state immediately before the LM head | Treat as a positive control, not circuit localization |
| Whole-residual patching | Mixes attention, MLP, routing, recurrent state, and unrelated features | Component-, edge-, and subspace-level interventions |
| Sparse layer selection | Can miss narrow transitions or invite post hoc layer choice | Dense discovery scan, then frozen confirmatory windows |
| Multi-token identifiers | Total log-probability mixes first-token selection and continuation copying | Decompose first token, continuation, exact sequence, and free generation |
| Recovery fraction instability | Ratios explode or flip when the denominator is near zero | Report absolute effects first and threshold ratio reporting |
| Corruption may be off-manifold | Large effects can reflect activation distribution shift | Use matched counterfactual donors, interpolation, norm checks, and multiple corruptions |
| Cross-model module mismatch | “Layer 70%” does not imply homologous computation | Compare semantic stages and architecture-specific components |
| Quantized/BF16 mismatch | Behavioral and mechanistic conclusions may refer to different functions | Run a parity and phenomenon-retention study |
| Synthetic-task dependence | Circuit may exploit templates or source position | Held-out templates, natural data, order permutations, and adversarial controls |
| Attention visualization temptation | Attention mass alone is not causal evidence | Use attention only to generate hypotheses; confirm with interventions |

---

## 3. Research questions and preregistered hypotheses

The program should be driven by explicit hypotheses. Null results should remain publishable because they distinguish competing mechanistic accounts.

### H1 — Semantic normalization

After early lexical processing, different surface forms for the same identifier enter a partially shared relational representation, while exact identifier tokens remain format-specific near output.

**Predictions:** source-label relational geometry becomes more aligned across formats at intermediate layers; source-fact geometry remains stable; format decoding increases near output; cross-format intervention transfers source identity better than literal surface form.

### H2 — Three-stage factorization

The model performs at least three partially separable computations:

1. choose the relevant source;
2. retrieve or bind the identifier associated with that source;
3. serialize the identifier token sequence.

**Predictions:** distinct components/subspaces selectively affect source correctness, new-vs-old label preference, and token continuation. Intervening on serialization should change surface form without changing the selected semantic source.

### H3 — Late causal bottleneck

Correct counterfactual label information becomes causally concentrated in a limited late-network transition region rather than being uniformly distributed.

**Predictions:** dense layer × position patching reveals a stable transition band; a small component set explains most of the exact patch effect; ablating that set substantially reduces rebinding while preserving answer content.

### H4 — Identifier complexity primarily taxes serialization

Identifier length and token irregularity have a larger causal effect on continuation/reconstruction than on semantic source selection.

**Predictions:** UUID penalties grow over continuation tokens; first-token source-selection margins remain more stable; serialization components exhibit stronger format dependence than binding components.

### H5 — Architecture changes implementation, not merely depth

Transformer, multimodal-text-decoder, and hybrid recurrent/attention models use different causal pathways for the same source-binding behavior.

**Predictions:** component types, onset locations, and path structure differ after controlling for width, depth, and behavioral competence; normalized depth alone will not align transitions.

### H6 — LFM inversion reflects stale or positional binding

LFM’s negative counterfactual effect arises because its internal state preserves an earlier source-position/identifier association or uses a positional heuristic that is not correctly rewritten by the swap.

**Competing predictions:**

- **Stale-state account:** resetting or patching recurrent state after the swapped source repairs rebinding.
- **Position heuristic:** moving source positions changes the preferred identifier even when semantics and identifiers are fixed.
- **Serialization-bias account:** semantic source selection is correct, but token likelihood favors the old label only during decoding.
- **Metric/tokenization artifact:** first-token and free-generation results do not reproduce the total-log-probability inversion.
- **General capability failure:** inversion disappears on easier tasks or lower source counts.

### H7 — Hybrid-layer division of labor in Qwen3.5

Full-attention layers perform source lookup or cross-position routing, while DeltaNet/recurrent layers maintain or transform the selected binding through later computation.

**Predictions:** interventions at full-attention outputs affect source choice; recurrent-state interventions affect persistence and later retrieval; the 4B model exhibits a cleaner or more redundant division of labor than the 2B model.

### H8 — Typed handles reuse the citation-binding mechanism

Typed entity canonicalization and source citation share a binding operation but use different serializers.

**Predictions:** some components/subspaces transfer between Stage 7 citation tasks and Stage 8 entity tasks; serializer components remain task-specific; shared-component ablation harms both tasks more than matched control tasks.

### H9 — Mechanisms generalize by semantic role, not absolute position

Circuits identified using semantic position schemas generalize across variable context length, source count, source order, and identifier token length better than circuits defined by absolute token index.

### H10 — Causal representations are low-dimensional but not necessarily sparse in the neuron basis

Source identity, bound handle, and output format can be causally manipulated in low-rank subspaces even when single-neuron or single-head effects are weak.

---

## 4. Model panel and comparison logic

### 4.1 Core model panel

| Model | Scientific role | Primary framework | Required status |
|---|---|---|---|
| Qwen2.5 1.5B Instruct | Existing positive-control transformer and continuity with Stages 6–7 | TransformerLens + NNsight | Core |
| Qwen3.5 2B Instruct | Small hybrid successor; architecture contrast | NNsight + custom adapter + pyvene | Core |
| Qwen3.5 4B Instruct | Within-family scale comparison | NNsight + custom adapter + pyvene | Core |
| LFM2.5 1.2B Instruct | Mechanistic negative/inversion case | NNsight + architecture-specific state adapter | Core |
| Gemma 4 E2B IT | Independent model-family replication | NNsight + pyvene | Core if compute permits |
| Gemma 4 E4B IT | Scale/architecture replication with expensive offload | NNsight | Secondary confirmation |

Tiny Aya remains behavioral-only unless a hookable official checkpoint becomes available. A GGUF backend should not be treated as equivalent to a per-layer Transformers experiment.

### 4.2 Comparisons that answer different questions

- **Qwen2.5 1.5B vs Qwen3.5 2B:** architecture generation and hybridization, approximately size-matched.
- **Qwen3.5 2B vs 4B:** within-family scale and redundancy.
- **Qwen3.5 vs LFM:** two hybrid approaches with potentially different state mechanisms.
- **Qwen vs Gemma:** replication across conventional decoder families.
- **Within-model identifier formats:** representation and serialization effects without architecture confounding.

Do not collapse all models into one pooled mechanistic estimate. Use hierarchical summaries, but preserve model-specific estimands and conclusions.

---

## 5. Data program and experimental design

### 5.1 Dataset tiers

#### Tier A — Fully controlled minimal pairs

Purpose: causal identification and clean counterfactuals.

Task families:

- single-source attribute lookup;
- temporal ordering;
- entity resolution;
- two- and three-hop composition;
- key–value retrieval with distractors;
- source citation after a separately supplied answer;
- typed-handle selection;
- tool/schema argument filling with symbolic references.

Manipulated factors:

- source count: 5, 10, 15, 20, 40;
- context length: approximately 512, 2K, 4K, 8K tokens where supported;
- relevant-source position: early, middle, late;
- source order and label order independently randomized;
- identifier family: structured, random compact, semantic, hexadecimal, numeric, UUID;
- identifier token length and tokenizer fragmentation;
- one versus multiple relevant sources;
- one-token versus multi-token answer and citation targets;
- answer generation versus supplied-answer citation.

#### Tier B — Controlled natural-language templates

Purpose: prevent dependence on one prompt grammar.

- At least 8 independently authored templates per task family.
- Lexical paraphrases, syntactic reordering, instruction rewording, and output-schema variation.
- Hold out entire templates, not merely random examples.
- Include distractors sharing words, entities, dates, or relations with the query.

#### Tier C — Natural benchmark evidence

Purpose: external validity.

- Extend MuSiQue with mechanistically usable source and output spans.
- Add at least one natural citation/retrieval benchmark with source-level ground truth.
- Construct counterfactual identifier relabelings without changing passage content.
- Use only examples where the tested model has non-trivial base competence and both candidate labels are tokenizable within the context limit.

#### Tier D — Cross-domain symbolic binding

Purpose: show that the circuit is about binding rather than citation typography.

- synthetic entity canonicalization from Stage 8;
- database row handles;
- tool-result references;
- temporary variable names;
- document anchors or claim IDs.

### 5.2 Split discipline

Every mechanistic stage should use three non-overlapping splits:

| Split | Purpose | Suggested size per model |
|---|---|---:|
| Discovery | Dense scanning and hypothesis formation | 24–32 semantic examples |
| Validation | Select components and tune thresholds | 24–40 semantic examples |
| Confirmatory | Frozen intervention plan and final estimates | 80–100 semantic examples |

Examples must be split by semantic template and generator seed. Identifier seeds and source permutations must also differ across splits. Natural benchmark examples must not be used to choose the circuit and then be reported as external validation.

### 5.3 Minimum sample-size policy

Do not choose n solely from the current point estimate. Before the confirmatory run:

1. estimate the paired-effect distribution from the discovery split;
2. simulate confidence-interval width and sign stability under candidate n;
3. set n to achieve both 80–90% power for the smallest scientifically meaningful paired effect and a predeclared maximum CI width;
4. inflate for task/source-count strata and failed token alignments;
5. freeze n before examining confirmatory outcomes.

Default targets, subject to simulation:

- direct swap behavior: **100 examples/model**, balanced across four task/source-count cells;
- dense residual localization: **32 discovery + 40 held-out validation**;
- exact component/path confirmation: **40 validation + 80 confirmation**;
- expensive Gemma E4B work: at least **24 discovery + 48 confirmation**, with limitations stated explicitly;
- natural-data external validation: at least **100 usable examples/model**.

### 5.4 Counterfactual families

Use multiple counterfactuals because each supports a different causal interpretation:

1. **Identifier swap:** relevant source and distractor exchange labels; identifier set is fixed.
2. **Content swap:** source contents exchange positions while labels remain fixed.
3. **Question swap:** requested relation changes while source block is fixed.
4. **Source-order permutation:** content–label pairs move together.
5. **Label-order permutation:** labels change without source movement.
6. **Format translation:** same binding rendered in another identifier family.
7. **Answer-preserving corruption:** irrelevant wording changes while the correct binding stays fixed.
8. **Null donor:** matched example with the same output label but a different relevant source.
9. **Random donor:** unrelated activation with matched norm and position.
10. **Interpolated donor:** clean-to-counterfactual interpolation to test dose response and off-manifold behavior.

---

## 6. Measurement framework

### 6.1 Primary behavioral estimands

For old label \(y_o\), new label \(y_n\), clean prompt \(x\), and swapped prompt \(x'\):

\[
\Delta_{swap} = [\log P(y_n\mid x')-\log P(y_o\mid x')] -
                [\log P(y_n\mid x)-\log P(y_o\mid x)].
\]

Report:

- total sequence log-odds effect;
- mean per-token effect;
- first citation-token effect;
- continuation-only effect;
- exact generated citation accuracy;
- probability mass assigned to all valid source identifiers;
- answer correctness and source correctness separately;
- invalid/hallucinated identifier rate;
- old-existing, wrong-existing, and malformed-output errors.

### 6.2 Primary causal estimands

For intervention \(I\):

- **Absolute causal effect:** change in new-vs-old preference from clean baseline.
- **Mediation/recovery:** intervention effect divided by the direct counterfactual effect, only when the denominator exceeds a preregistered magnitude.
- **Necessity:** behavioral loss when the candidate component/path is ablated or replaced.
- **Sufficiency:** recovery when only the candidate circuit is retained or patched.
- **Specificity:** target-task effect minus effects on answer content, fluency, unrelated labels, and matched control tasks.
- **Faithfulness:** full-model performance reproduced by the retained circuit under a declared ablation baseline.
- **Completeness:** residual effect left outside the proposed circuit.
- **Minimality:** effect lost when individual members or coherent groups are removed.

Absolute effects are primary. Recovery ratios are secondary because near-zero or sign-changing direct effects make them unstable.

### 6.3 Representation estimands

- cosine similarity for aligned individual states;
- linear CKA and RSA for relational geometry;
- cross-validated linear probe accuracy/AUROC;
- minimum-description-length or sample-efficiency curves for probe complexity;
- cross-template and cross-format probe transfer;
- representation erasure effects;
- subspace dimensionality and principal-angle overlap;
- tuned/logit-lens token rank and calibrated probability trajectory.

Probe results are descriptive unless paired with erasure, interchange, or subspace intervention.

### 6.4 Statistical analysis

- Paired bootstrap intervals over semantic examples, never over individual tokens or interventions.
- Exact paired sign/McNemar tests for binary outcomes.
- Hierarchical regression with model, task, template, source count, identifier family, and example effects for synthesis.
- Multiple-comparison control within declared families, preferably Benjamini–Hochberg for discovery and fixed primary hypotheses for confirmation.
- Report effect distributions and positive-case counts, not only means.
- Use cluster-robust uncertainty when multiple formats or interventions share an example.
- Predeclare exclusions: token-alignment failure, context overflow, non-finite logits, unavailable module, or failed parity test.
- Report all failed or excluded runs in the manifest.

---

## 7. Tool and library architecture

### 7.1 Principle

No single framework should be forced across every architecture. The repository should provide one semantic experiment interface and thin architecture adapters, while established libraries perform tracing, intervention, circuit search, and subspace training.

### 7.2 Library responsibilities

| Library | Responsibility | Models | Do not use it for |
|---|---|---|---|
| Hugging Face Transformers + Accelerate | Canonical checkpoint loading, tokenization, chat templates, BF16 forward/generation, CPU offload | All | Circuit abstractions |
| [NNsight](https://nnsight.net/documentation/) | General tracing, activation editing, gradients, batching, generation-time intervention | Qwen3.5, LFM, Gemma; verification on Qwen2.5 | Assuming semantic component meanings automatically |
| [TransformerLens](https://transformerlensorg.github.io/TransformerLens/) | Activation cache, head/MLP decomposition, exact patching, path patching, EAP/EAP-IG | Qwen2.5 and explicitly verified supported models | Forcing unsupported hybrid architectures into a standard transformer representation |
| [pyvene](https://stanfordnlp.github.io/pyvene/) | DAS, low-rank and trainable interventions, interchange interventions, causal abstraction | All models with registered mappings | Basic model loading or tokenizer provenance |
| [PEAP](https://github.com/technion-cs-nlp/PEAP) methodology | Semantic position schemas and position-aware edge attribution | Primarily Qwen2.5; concepts reused elsewhere | A universal drop-in dependency |
| [SAE Lens](https://decoderesearch.github.io/SAELens/) | Targeted sparse autoencoder training and evaluation | Localized sites only | Model-wide first-pass discovery |
| [Circuit Tracer](https://www.anthropic.com/research/open-source-circuit-tracing) | Attribution-graph exploration on supported replacement models | Supported proxy checkpoints | Primary evidence on unsupported project models |
| Tuned Lens | Calibrated layerwise prediction trajectories | Optional supported models | Causal localization |
| CircuitsVis | Exploratory token/head visualization | Notebook and blog use | Statistical or causal evidence |
| einops + jaxtyping | Explicit tensor axes and runtime shape checks | All | Experiment orchestration |
| Zarr + Numcodecs | Chunked activation/intervention storage | Large scans | Small immutable metadata |
| safetensors | Portable tensor checkpoints for probes, subspaces, and SAEs | All | Append-only tabular results |
| Parquet + DuckDB | Queryable intervention summaries | Analysis | Raw generation text requiring exact provenance |
| statsmodels or PyMC | Hierarchical confirmatory models | Cross-model synthesis | Replacing paired raw summaries |

### 7.3 Discovery versus confirmation

| Phase | Preferred technique | Reason |
|---|---|---|
| Coarse discovery | EAP-IG, gradients, dense residual scans | Fast screening |
| Reliability check | Exact patching on a stratified subset | Detect attribution failure and nonlinear interactions |
| Component localization | Exact head/MLP/state patching | Causal component evidence |
| Path identification | Path patching or edge interventions | Sender–receiver mediation |
| Representation factorization | pyvene DAS/interchange + erasure | Tests causal abstractions |
| Feature interpretation | Targeted SAEs/transcoders | Human-readable features after localization |
| Final confirmation | Frozen exact interventions on held-out data | Publishable effect estimates |

Attribution methods are screening tools. Exact intervention is the confirmatory standard. This is consistent with known saturation and cancellation problems in attribution patching and AtP*.

### 7.4 Architecture adapter contract

Add a single semantic interface rather than more ad hoc module-name logic:

```python
class MechanisticModelAdapter(Protocol):
    def layer_count(self) -> int: ...
    def layer_kind(self, layer: int) -> str: ...
    def residual_pre(self, layer: int): ...
    def residual_post(self, layer: int): ...
    def attention_output(self, layer: int): ...
    def attention_head_output(self, layer: int): ...
    def mlp_output(self, layer: int): ...
    def recurrent_state(self, layer: int): ...
    def state_update_gate(self, layer: int): ...
    def final_norm(self): ...
    def lm_head(self): ...
    def supports(self, intervention_kind: str) -> bool: ...
```

Implementations should return module or trace handles plus axis metadata. Unsupported components must raise an explicit capability error instead of silently substituting a residual stream.

### 7.5 Environment strategy

The current model families require incompatible Transformers versions. Maintain separate, locked environments:

- `mech-qwen25-lfm`: existing verified Qwen2.5/LFM stack;
- `mech-gemma4`: Transformers version required by Gemma 4;
- `mech-qwen35`: version pinned to the official Qwen3.5 implementation;
- `mech-tlens`: TransformerLens and compatible Qwen2.5 dependencies;
- `mech-sae`: optional SAE Lens/Circuit Tracer environment.

Each environment must record Python, CUDA, Torch, Transformers, Accelerate, NNsight, TransformerLens, pyvene, and model revisions. Use lock files or exact constraints. Do not upgrade the existing Stage 6/7 environment in place.

---

## 8. Stage 10 — Infrastructure, parity, and measurement validation

**Goal:** prove that the new toolchain measures the same function before launching expensive experiments.

### Study 10.1 — Model/module census

For every core checkpoint:

- list every decoder layer and its architecture type;
- identify residual-pre, residual-post, attention/mixer, MLP, normalization, cache/state, and output-head tensors;
- record tensor shapes and axis meanings on a fixed prompt;
- identify tuple/dataclass outputs and in-place state behavior;
- record whether hooks run once per prompt or per generation step;
- produce a checked-in architecture manifest.

**Libraries:** Transformers, NNsight, einops, jaxtyping.  
**Artifact:** `results/architecture/<model_revision>/module_manifest.json`.  
**Gate:** all intended intervention sites are explicitly mapped or marked unsupported.

### Study 10.2 — No-op parity

Compare canonical Hugging Face execution with:

- NNsight trace without edits;
- NNsight identity edit;
- current Stage 7 hook runner;
- TransformerLens conversion for Qwen2.5;
- `use_cache=False` versus generation-compatible cache settings;
- candidate batch size 1 versus 2;
- CPU-offloaded versus non-offloaded execution where feasible.

**Metrics:** maximum/mean logit difference, target log-probability difference, greedy next-token identity, exact generated suffix.  
**Gate:** predeclared numerical tolerance and exact greedy-token equality on a representative suite. Any weight folding, centering, normalization rewriting, or dtype conversion in TransformerLens must be disabled or explicitly validated.

### Study 10.3 — Intervention unit tests

Required tests:

- donor equals recipient produces zero effect;
- clean-to-clean and swapped-to-swapped patches are identities;
- final-state patch reproduces donor logits within tolerance;
- unrelated position and question-endpoint controls remain small;
- batch and single-example patches agree;
- variable sequence length and padding do not shift positions;
- patching tuple outputs preserves non-primary fields;
- gradient-enabled traces do not retain stale graphs;
- cached generation patches the intended step only;
- offloaded tensors return to the correct device and dtype;
- recurrent states are cloned rather than mutated across examples.

### Study 10.4 — Behavioral precision parity

Run the direct source-ID swap on the same examples using:

- current BF16 Stage 7 code;
- new NNsight code;
- Qwen2.5 TransformerLens code;
- current GGUF quantized behavioral backend where exact scoring is available.

**Purpose:** separate framework disagreement, precision disagreement, and genuine quantization effects.  
**Gate:** sign and rank agreement for primary direct effects; any material mismatch becomes a reported precision study rather than being ignored.

### Study 10.5 — Storage and provenance migration

Keep append-only JSONL for request-level metadata. Add:

- Zarr arrays for large activation tensors;
- safetensors for trained subspaces/probes/SAEs;
- Parquet summaries for query and plotting;
- content hashes linking every tensor artifact to its request record;
- atomic completion markers and resumption keys;
- explicit units, axis names, semantic spans, model revision, tokenizer revision, prompt-template hash, library versions, dtype, cache mode, and intervention specification.

**Stage 10 exit criterion:** the same intervention can be reproduced through the new stack with verified logits, positions, and metadata on Qwen2.5, LFM, Gemma E2B, and both Qwen3.5 models.

---

## 9. Stage 11 — Scaled behavioral and direct-causal replication

**Goal:** establish a statistically defensible phenomenon before circuit discovery.

### Study 11.1 — Independent Stage 7 replication

Run 100 new semantic examples per core model, balanced across:

- temporal and entity-resolution tasks;
- 15 and 20 sources;
- structured, random-compact, and UUID identifiers;
- relevant-source position quartiles;
- identifier assignments and prompt templates.

Freeze the current direct-swap estimand and add first-token, continuation, and free-generation metrics.

**Primary tests:**

- Qwen2.5 positive counterfactual rebinding;
- LFM negative/inverted compact-ID effect;
- Gemma E2B positive rebinding;
- Qwen3.5 2B and 4B direction and magnitude;
- model × identifier-family interaction.

### Study 11.2 — LFM anomaly audit

Before interpreting the inversion, eliminate implementation explanations:

- manually inspect token IDs and candidate suffix alignment;
- score candidates independently rather than in a padded batch;
- compare right and left padding where supported;
- score first token at the exact same prefix;
- use both total and normalized likelihood;
- run free generation and rank all in-context labels;
- verify clean and swapped label sets are identical;
- repeat with new seeds, templates, task difficulty, and source counts;
- compare BF16 and GGUF behavior;
- test instruction phrasing and chat-template variants;
- include a trivial one-source and two-source competence control.

**Decision tree:**

- If inversion disappears after scoring correction, treat prior Stage 7 LFM as a measurement bug and document it.
- If it persists only in teacher forcing, classify it as a decoding/conditioning mismatch.
- If it persists in free generation and multiple tasks, proceed as a genuine mechanistic negative case.
- If it appears only at high source count, interpret it as capacity/interference failure rather than universal binding logic.

### Study 11.3 — Identifier-factorial behavior

Cross identifier properties rather than comparing only named formats:

- length: 1, 2, 4, 8, 16 tokenizer tokens;
- character family: digits, letters, mixed, punctuation-delimited;
- structural typing: untyped versus typed prefix;
- semantic content: arbitrary versus mnemonic;
- token frequency/familiarity;
- shared-prefix ambiguity;
- check-digit or compositional structure.

Use token-matched pairs wherever possible. Fit a hierarchical model predicting source selection, first-token choice, continuation accuracy, and exact generation.

### Study 11.4 — Scaling curves

Measure direct rebinding across source count and context length. Estimate where each model transitions from correct binding to heuristic or stale binding. Separate source count from raw token length through filler controls.

### Study 11.5 — Natural-data replication

Apply identifier swaps to held-out MuSiQue and one additional citation dataset. Use answer-correct examples for a conditional source-binding analysis, and report unconditional end-to-end accuracy separately.

**Stage 11 exit criterion:** stable, held-out direct effects for each core model, a resolved classification of the LFM anomaly, and frozen example pools for mechanistic discovery and confirmation.

---

## 10. Stage 12 — Dense layer × semantic-position localization

**Goal:** locate when and where source selection, binding, and serialization become causally transferable.

### Study 12.1 — Dense residual patching

Patch every layer, initially on the discovery split, at semantic positions:

- each source-label token and label endpoint;
- each source-content span and content endpoint;
- relation-bearing tokens in the question;
- question endpoint;
- answer tokens;
- delimiter immediately before citation;
- first citation-token prediction state;
- each continuation prediction state;
- post-citation closing tokens.

Create layer × semantic-position heatmaps for absolute causal effect. Do not average positions before checking for cancellation.

**Libraries:** NNsight for all models; TransformerLens for Qwen2.5; PEAP-style semantic schemas.  
**Key result:** transition bands defined by semantic computation, not normalized depth.

### Study 12.2 — First token versus continuation

For every identifier family, decompose intervention effects into:

- selection of the first distinguishing token;
- continuation given the correct prefix;
- closing syntax;
- recovery after an induced wrong prefix.

This is critical for deciding whether UUID difficulty is a binding problem or a long-sequence serialization problem.

### Study 12.3 — Position-aware attribution screening

On Qwen2.5:

- run EAP-IG over semantically labeled positions;
- preserve cross-position edges instead of aggregating all sequence positions;
- validate top positive, top negative, and random-ranked components by exact patching;
- quantify precision/recall of attribution screening against exact effects;
- check saturation and cancellation with multi-step integrated gradients and exact measurements.

Reuse PEAP’s position-schema idea even if the repository code requires adaptation. The output should be a candidate edge list, not a final circuit claim.

### Study 12.4 — Transition-window confirmation

Freeze model-specific transition windows from discovery and evaluate every layer in those windows on the validation split. Anticipated starting regions from Stage 7 are:

- Qwen2.5: layers 20–24;
- LFM: layers 6–13;
- Gemma E2B: layers 29–35;
- Gemma E4B: layers 33–42;
- Qwen3.5: determined de novo by layer type and dense scan.

**Stage 12 exit criterion:** each model has a held-out transition profile, and the source-selection versus serialization decomposition has at least one falsifiable component-level prediction.

---

## 11. Stage 13 — Component and path-level circuit discovery

**Goal:** replace “late residual state” with a concrete causal circuit.

### Study 13.1 — Attention/mixer versus MLP decomposition

Within each frozen transition window, patch or ablate separately:

- attention/mixer output;
- MLP output;
- residual input and output;
- full-attention versus recurrent/DeltaNet mixer output in hybrid models;
- recurrent state and gates where exposed;
- normalization inputs only as a diagnostic.

Measure direct, necessity, and specificity effects. Preserve answer content as a negative-control outcome.

### Study 13.2 — Head-level localization

For conventional attention layers:

- patch per-head `z` or head output, not attention probabilities alone;
- test query, key, value, and pattern interventions for selected heads;
- perform mean, resample, zero, and counterfactual ablations;
- include same-layer random heads and magnitude-matched controls;
- evaluate both discovery examples and held-out templates.

Use TransformerLens where verified; otherwise NNsight hooks with explicit head-axis validation.

### Study 13.3 — MLP and feature-channel localization

- Patch complete MLP outputs first.
- If an MLP is causal, screen neurons/channels or low-rank directions.
- Prefer low-rank subspace intervention over claiming single-neuron semantics.
- Test whether the MLP writes source identity, identifier format, or exact token logits into the residual stream.

### Study 13.4 — Path patching

Test explicit sender–receiver hypotheses:

1. source-label/source-content positions → query/relation position;
2. source position → answer/citation delimiter;
3. intermediate binding component → late serializer component;
4. full-attention layer → recurrent state in Qwen3.5;
5. recurrent state → late output/MLP;
6. shared binding component → task-specific serializer.

For each edge, freeze non-target paths appropriately and measure the direct effect. Compare node patching with edge/path patching to distinguish mediation from correlation.

### Study 13.5 — Causal scrubbing tests

Define an explicit computational graph:

```text
source facts
   -> relevant-source variable R
   -> bound-handle variable B
   -> surface-format variable F
   -> output token sequence Y
```

Construct resampling distributions that preserve or randomize one variable at a time. A proposed circuit passes only if its behavior matches the abstraction across resampled examples, not merely on one clean/corrupt pair.

### Study 13.6 — Faithfulness, completeness, and minimality

For the proposed circuit:

- retain only the circuit under several ablation baselines;
- ablate the circuit while retaining the rest of the model;
- compare against random circuits matched by node count and activation magnitude;
- remove nodes/edges greedily and by coherent functional group;
- report performance on the target behavior and unrelated language-model outputs;
- test multiple corruption baselines because faithfulness scores are baseline-sensitive.

**Stage 13 exit criterion:** at least one model has a compact, held-out, causally verified sender–receiver circuit with reported faithfulness, completeness, minimality, and specificity; the other models have architecture-aware component maps even if no shared circuit exists.

---

## 12. Stage 14 — Causal representation and subspace factorization

**Goal:** test whether source, binding, and format variables occupy separable causal subspaces.

### Study 14.1 — Cross-validated probes

At candidate sites, train probes for:

- relevant source identity;
- source position;
- bound identifier identity;
- old versus new assignment;
- identifier family;
- identifier length;
- task type;
- output token identity.

Controls:

- train/test split by template and identifier seed;
- label permutation;
- random Gaussian features matched in dimension;
- layerwise selectivity controls;
- probe capacity curves;
- cross-format and cross-task transfer.

Probes nominate sites; they do not establish use.

### Study 14.2 — Distributed Alignment Search with pyvene

Train low-rank rotated subspaces for hypothesized variables:

- \(R\): relevant source;
- \(B\): bound handle;
- \(F\): output format;
- \(T\): task or relation.

Perform interchange interventions:

- swap \(R\) while holding \(B,F,T\) fixed;
- swap \(B\) while holding \(R,F,T\) fixed;
- swap \(F\) while holding \(R,B,T\) fixed;
- swap task relation while preserving source set;
- compose interventions not encountered during training.

Evaluate selectivity: a binding-subspace swap should change the cited handle but not answer semantics; a format-subspace swap should change syntax/serialization but not semantic source.

### Study 14.3 — Erasure and necessity

Use LEACE or an equivalent closed-form linear concept erasure as a diagnostic:

- erase linearly decodable source position;
- erase bound-identifier information;
- erase format information;
- compare behavioral damage and remaining nonlinear decodability;
- use random subspaces of equal rank as controls.

Erasure claims must acknowledge that removal can alter unrelated features and that failed erasure does not prove absence of a nonlinear representation.

### Study 14.4 — Cross-model subspace comparison

- compare subspace dimensionality and principal angles;
- test whether a probe trained on one model transfers only after learned alignment;
- compare within-family Qwen3.5 2B/4B more strongly than unrelated architectures;
- avoid claiming neuron-level homology across models.

### Study 14.5 — Cross-task circuit reuse

Apply citation-derived binding interventions to Stage 8 typed-handle examples and vice versa. Include control tasks requiring ordinary next-token prediction but no binding. This tests H8 directly.

**Stage 14 exit criterion:** a low-dimensional causal abstraction passes held-out interchange tests and separates at least two of source selection, bound identity, and surface format.

---

## 13. Stage 15 — Architecture-specific studies

### 13.1 LFM inversion program

#### A. Determine what the model selected

Measure separately:

- probability of facts/answers associated with each source;
- probability of each in-context label;
- first citation token and continuation;
- source-position decoding;
- bound-label decoding;
- generated answer source and generated citation source.

This distinguishes correct semantic selection with wrong serialization from genuinely wrong source selection.

#### B. State chronology

Trace the recurrent/mixer state:

- immediately before and after each source label;
- immediately after source content;
- after the question;
- at the answer–citation boundary;
- at each generated citation token.

Patch states from clean/swapped donors at each boundary. Test whether a stale association is written early and carried forward.

#### C. Reset and truncation tests

Where the architecture permits:

- reset recurrent state after each source;
- reset only after the swapped relevant source;
- truncate or detach state at source boundaries;
- patch only the recurrent state, only the local mixer output, or only the MLP;
- compare with full residual patching.

#### D. Positional and recency hypotheses

- move the relevant source while preserving its label;
- move the label while preserving content position;
- duplicate a relevant fact under two labels;
- place old and new labels at matched distances from the question;
- reverse source order;
- insert irrelevant sources before versus after the relevant source.

#### E. Repair intervention

Find the smallest state/component intervention that changes the LFM effect from old-label preference to correct rebinding without changing answer accuracy. A successful repair would be a particularly strong causal result.

### 13.2 Qwen3.5 hybrid program

#### A. Layer-type atlas

Map every full-attention, DeltaNet/recurrent, local mixing, and MLP block. Plot direct and patched effects by layer type rather than only index.

#### B. Full-attention routing test

Patch/ablate full-attention heads connecting citation positions to source labels/content. Test whether source retrieval collapses while recurrent persistence remains intact.

#### C. Recurrent-state persistence test

Patch the state after the relevant source, after the question, and before citation. Test whether this changes late binding without altering early source selection.

#### D. Handoff edges

Use path patching between full-attention layers and subsequent DeltaNet/state layers. The target result is an explicit handoff from cross-position lookup to stateful maintenance.

#### E. 2B versus 4B scale

Compare:

- direct effect and error rate;
- transition width;
- circuit sparsity/redundancy;
- low-rank subspace dimensionality;
- robustness to source count and identifier length;
- recovery after ablation of the top component.

Do not interpret differences as pure scale if depth, layer schedule, tokenizer, or training differ; report those architectural covariates.

### 13.3 Gemma replication program

- Increase E2B to the full confirmatory cohort.
- Densely map E4B layers 33–42 before component decomposition.
- Test whether E2B/E4B share a transition mechanism or merely similar output behavior.
- Use E4B primarily as a scaling replication unless compute supports a complete circuit analysis.

**Stage 15 exit criterion:** a mechanistic explanation of the LFM result and a causal full-attention/recurrent division-of-labor test in Qwen3.5.

---

## 14. Stage 16 — Sparse features and interpretable units

**Goal:** obtain human-interpretable features only after causal sites are known.

### Study 16.1 — Targeted activation corpus

Collect activations at no more than 2–4 confirmed sites per model over a balanced corpus containing:

- all identifier formats;
- correct and incorrect binding cases;
- multiple task families;
- source positions and output positions;
- null examples without citation/binding;
- adversarial shared-prefix identifiers.

Avoid storing every layer and token. Use Zarr with chunking by site and semantic position.

### Study 16.2 — SAE training with SAE Lens

Train several widths/sparsities per site. Report:

- reconstruction error and variance explained;
- L0 or active-feature count;
- dead features;
- feature stability across seeds;
- downstream loss recovered after reconstruction;
- feature interpretability on held-out examples.

Select SAEs by a Pareto frontier rather than one arbitrary sparsity setting.

### Study 16.3 — Feature validation

For candidate source/binding/format features:

- inspect maximum-activating examples;
- test automated descriptions only as annotation support;
- measure specificity across task and format controls;
- ablate and activate features causally;
- patch feature coefficients across counterfactual examples;
- compare against random and frequency-matched features;
- verify effects survive SAE reconstruction error controls.

### Study 16.4 — Feature-level circuit

Connect validated features across sites using attribution/path methods, then verify a small number of edges exactly. If transcoders are available for the exact model, compare the graph with Circuit Tracer; otherwise do not present a proxy model’s graph as evidence for the target checkpoint.

**Stage 16 is optional for the first paper.** It becomes core only if feature interventions reveal a clearer mechanism than component/subspace analysis and can be completed without delaying confirmatory causal work.

---

## 15. Stage 17 — Autoregressive and robustness validation

**Goal:** show that the mechanism governs actual generation rather than only teacher-forced scoring.

### Study 17.1 — Generation-time intervention

Use NNsight or verified generation hooks to intervene:

- once during prompt ingestion;
- at the answer–citation boundary;
- only at the first citation token;
- at every citation continuation step;
- in the KV cache or recurrent state where relevant.

Record whether the intervention changes the generated semantic answer, citation, syntax, or length.

### Study 17.2 — Decoding robustness

Repeat decisive interventions under:

- greedy decoding;
- low-temperature sampling with fixed seeds;
- constrained decoding over valid identifiers;
- unconstrained decoding;
- varied maximum generation lengths.

The primary mechanistic conclusion should not depend on one decoding implementation.

### Study 17.3 — Template and distribution robustness

Test the frozen circuit on:

- unseen templates;
- unseen identifier seeds and formats;
- different source counts and positions;
- natural benchmark examples;
- task families not used in discovery;
- paraphrased instructions;
- distractor distributions with high lexical overlap.

### Study 17.4 — Specificity and side effects

Measure perplexity or next-token loss on matched non-binding text, answer accuracy, fluency, output validity, and unrelated source references. A useful mechanistic intervention should not globally damage the model.

**Stage 17 exit criterion:** the proposed circuit or subspace causally alters free-running binding behavior on held-out prompts with limited off-target degradation.

---

## 16. Stage 18 — Paper-level synthesis and external validation

### 16.1 Confirmatory freeze

Before the final run, freeze:

- model revisions and environments;
- datasets and split hashes;
- primary hypotheses and estimands;
- circuit nodes/edges/subspaces;
- intervention strengths and baselines;
- exclusion rules;
- statistical models;
- figure and table specifications.

Run final confirmation once. Exploratory changes afterward must be labeled as such.

### 16.2 External replication

Preferred options, in order:

1. a second natural citation/retrieval dataset;
2. a second independently implemented experiment runner;
3. an additional open model family with verified hooks;
4. a collaborator reproducing the frozen Qwen2.5 circuit from the public artifact.

### 16.3 Systems consequence

Connect mechanism to design without overstating safety:

- compact typed handles reduce certain binding and serialization burdens;
- validators guarantee reference syntax and existence, not semantic correctness;
- architecture-specific negative results imply that IR design should be benchmarked per model;
- a mechanistic repair or circuit-based diagnostic may predict which identifier scheme will work before a full deployment.

### 16.4 Reproducibility release

Release:

- exact configs and environment locks;
- data generators and split manifests;
- architecture adapters and parity tests;
- raw request-level records where licensing permits;
- intervention matrices and trained subspaces;
- plotting scripts and figure source data;
- model/checkpoint hashes;
- negative results and failed hypotheses;
- a minimal notebook reproducing one end-to-end causal result.

---

## 17. Priority plan

### P0 — Required for a credible top-conference submission

1. Stage 10 parity and architecture adapters.
2. Stage 11 direct-effect replication with n≈100/model.
3. Resolve the LFM anomaly.
4. Add Qwen3.5 2B and 4B.
5. Dense layer × semantic-position localization.
6. Attention/mixer-versus-MLP decomposition.
7. At least one exact component/path circuit on held-out examples.
8. First-token versus continuation analysis.
9. Autoregressive intervention validation.
10. Natural-data external validation.
11. Necessity, sufficiency, specificity, and circuit faithfulness tests.
12. Frozen confirmatory run with full provenance.

### P1 — Strongly increases novelty and acceptance probability

1. pyvene/DAS separation of source, binding, and format subspaces.
2. Qwen3.5 full-attention-to-recurrent-state handoff experiment.
3. Minimal causal repair of LFM inversion.
4. Cross-task reuse between citation and typed entity handles.
5. Position-aware circuit generalization across context lengths and source orders.
6. Hierarchical cross-model analysis.

### P2 — High-value extension, but not required for the first complete paper

1. Targeted SAEs at confirmed sites.
2. Feature-level causal circuits.
3. Circuit Tracer comparison on supported proxy models.
4. Gemma E4B full component circuit.
5. External collaborator replication.
6. Mechanism-guided identifier design or training intervention.

### Explicit non-priorities

- building a new general-purpose hook framework;
- model-wide SAE training before localization;
- attention heatmaps presented as explanations;
- exhaustive neuron enumeration;
- forcing every model into TransformerLens;
- reproducing old ACDC code when current exact patching/EAP tools suffice;
- expanding to many model families before the core causal claims replicate;
- optimizing the blog before the main empirical uncertainties are resolved.

---

## 18. Implementation work packages

### WP1 — Experiment schema

Add configuration fields for:

- discovery/validation/confirmation split;
- counterfactual family;
- semantic position schema;
- intervention granularity;
- architecture adapter;
- teacher-forced versus autoregressive mode;
- attribution screening versus exact confirmation;
- component and edge selections;
- corruption/ablation baseline;
- denominator threshold for recovery;
- artifact storage policy.

### WP2 — Architecture adapters

Implement and test adapters for Qwen2.5, LFM2.5, Gemma 4, and Qwen3.5. Keep adapter code separate from experimental logic. Every adapter must export its capabilities and module manifest.

### WP3 — NNsight intervention backend

Reproduce the existing Stage 7 residual patch, then add component, recurrent-state, gradient, and generation-time interventions. Preserve the old runner until parity is established.

### WP4 — TransformerLens backend

Add verified Qwen2.5 conversion, activation cache, EAP-IG, head/MLP patching, and path patching. Build logit-parity tests against Hugging Face.

### WP5 — pyvene backend

Register model/component mappings and implement DAS/interchange experiments. Store trained rotations and subspaces in safetensors with split and seed metadata.

### WP6 — Semantic position schemas

Generalize the current span utilities into named roles that survive template and token-length variation. Support one-to-many positions, endpoints, pooled spans, and generation-time positions.

### WP7 — Analysis and statistics

Create one long-form tidy record per example × intervention × target metric. Add hierarchical models, multiple-comparison bookkeeping, circuit metrics, effect heatmaps, and power simulation.

### WP8 — Storage

Introduce Zarr only for large arrays; retain JSONL manifests. Add checksum validation, resumability, and garbage-collection tooling for incomplete arrays without deleting raw records.

### WP9 — Sparse-feature extension

Install SAE Lens in a separate environment and begin only after Stage 13 identifies causal sites.

---

## 19. Recommended repository additions

```text
configs/mechinterp/
  stage10_parity/
  stage11_replication/
  stage12_dense_localization/
  stage13_circuits/
  stage14_subspaces/
  stage15_architecture/
  stage16_sae/
  stage17_generation/

src/symbolic_ir/mechinterp/
  adapters/
    base.py
    qwen25.py
    qwen35.py
    lfm25.py
    gemma4.py
  backends/
    native.py
    nnsight_backend.py
    transformer_lens_backend.py
    pyvene_backend.py
  schemas.py
  estimands.py
  circuit_metrics.py
  artifact_store.py

scripts/
  audit_model_architecture.py
  validate_mechinterp_parity.py
  run_stage11_replication.py
  run_stage12_localization.py
  run_stage13_circuits.py
  run_stage14_subspaces.py
  run_stage15_architecture.py
  run_stage17_generation.py

results/
  architecture/
  activations_zarr/
  circuits/
  subspaces/
  sae/
  processed/
```

Do not rename or overwrite existing Stage 6/7 artifacts. The successor stages should read them as immutable historical evidence.

---

## 20. Experiment registry

| ID | Experiment | Hypothesis | Method/library | Primary outcome | Priority |
|---|---|---|---|---|---|
| E10.1 | Module census | Measurement validity | Transformers + NNsight | Verified component map | P0 |
| E10.2 | No-op/logit parity | Framework does not change function | HF/NNsight/TL | Logit and generation agreement | P0 |
| E10.3 | Intervention tests | Patches target intended states | Native + NNsight | Identity/positive/negative controls | P0 |
| E10.4 | BF16/GGUF parity | Phenomenon survives precision change | HF + llama.cpp | Direct-effect agreement | P0 |
| E11.1 | Large Stage 7 replication | Direct rebinding is stable | Native/NNsight | Swap log-odds | P0 |
| E11.2 | LFM audit | Inversion is genuine | NNsight + free generation | Stable negative/positive classification | P0 |
| E11.3 | Identifier factorial | Complexity taxes serialization | Behavioral + hierarchical model | First-token/continuation effects | P0 |
| E11.4 | Context/source scaling | Binding has capacity threshold | Behavioral | Scaling curves | P1 |
| E11.5 | Natural replication | Effect generalizes | MuSiQue + external data | Held-out direct effect | P0 |
| E12.1 | Dense residual map | Late causal bottleneck | NNsight/TL | Layer × role heatmap | P0 |
| E12.2 | First/continuation split | Selection differs from copying | Exact likelihood | Token-stage decomposition | P0 |
| E12.3 | Position-aware EAP-IG | Efficient discovery is reliable | TL + PEAP ideas | Exact-patching precision | P1 |
| E13.1 | Component decomposition | Mixer/MLP roles differ | NNsight/TL | Component causal effects | P0 |
| E13.2 | Head localization | Specific heads route source info | TransformerLens | Held-out head effects | P0 for Qwen |
| E13.3 | MLP/subspace localization | Binding is low-rank | TL/NNsight/pyvene | Causal low-rank direction | P1 |
| E13.4 | Path patching | Binding flows through proposed edges | TransformerLens/NNsight | Direct path effects | P0 |
| E13.5 | Causal scrubbing | Circuit implements stated abstraction | Resampling interventions | Abstraction-consistent behavior | P1 |
| E13.6 | Circuit metrics | Circuit is faithful and specific | auto-circuit concepts/custom | Faithfulness/completeness | P0 |
| E14.1 | Probe atlas | Variables are decodable | sklearn | Cross-template transfer | Supporting |
| E14.2 | DAS factorization | R/B/F occupy separable subspaces | pyvene | Selective interchange | P1 |
| E14.3 | Concept erasure | Subspaces are used | LEACE/custom | Selective behavioral loss | P1 |
| E14.4 | Cross-model alignment | Representations differ systematically | CKA/principal angles | Family/scale pattern | P2 |
| E14.5 | Citation/entity reuse | Binding circuit generalizes | Cross-task intervention | Transfer effect | P1 |
| E15.1 | LFM state chronology | Stale state causes inversion | NNsight adapter | State-specific mediation | P0 |
| E15.2 | LFM repair | Inversion is causally correctable | State/component edit | Correct rebinding restored | P1 |
| E15.3 | Qwen3.5 layer atlas | Layer types divide labor | NNsight | Effects by layer type | P0 |
| E15.4 | Qwen3.5 handoff | Attention lookup feeds recurrent state | Path patching | Handoff mediation | P1 |
| E15.5 | Qwen3.5 scale | 4B has cleaner/redundant circuit | 2B/4B comparison | Circuit robustness/sparsity | P1 |
| E16.1 | Targeted SAE | Causal site contains sparse features | SAE Lens | Reconstruction/feature quality | P2 |
| E16.2 | Feature intervention | Feature meaning is causal | SAE Lens + NNsight | Specific causal effect | P2 |
| E17.1 | Generation intervention | Circuit governs free decoding | NNsight | Generated binding changes | P0 |
| E17.2 | Decoding robustness | Effect is not decoding-specific | HF generation | Robustness across settings | P1 |
| E17.3 | Distribution robustness | Circuit generalizes semantically | Frozen circuit | Held-out performance | P0 |

---

## 21. Stop/go rules

### After Stage 11

- **Go to circuit discovery** for a model only if it shows a stable, non-trivial direct counterfactual effect or a stable inversion worth explaining.
- **Do not localize a circuit** for a floor model that cannot perform the base task; first reduce task difficulty or treat it as a capability boundary.
- If Qwen3.5 2B/4B fail the base behavior, retain them as architectural negative cases but do not force the handoff hypothesis.

### After Stage 12

- Continue to component localization only when a transition region replicates on validation data.
- If effects are diffuse, prioritize subspace and causal-scrubbing approaches over exhaustive head searches.
- If exact patching disagrees strongly with attribution screening, report the disagreement and use exact results for confirmation.

### After Stage 13

- Claim a circuit only if it has held-out causal effects, faithfulness/completeness analysis, and controls.
- If no compact circuit exists, a distributed low-rank mechanism is still a valid result; move to Stage 14.
- Do not begin SAEs merely because component localization is difficult.

### Before paper submission

- No headline claim should rely only on n<40, one prompt template, one identifier family, teacher forcing, or a final-layer positive control.
- Every major figure must trace to immutable source records and a scripted build.
- Every model-specific conclusion must state whether it is confirmatory, exploratory, or diagnostic.

---

## 22. Minimum viable paper and ideal paper

### Minimum viable strong paper

1. Large direct-effect replication on Qwen2.5, LFM, Qwen3.5 2B/4B, and Gemma E2B.
2. Dense position-aware localization.
3. One causally verified Qwen circuit with component and path evidence.
4. A mechanistic explanation of the LFM inversion.
5. First-token/continuation decomposition.
6. Free-generation validation.
7. Natural-data and held-out-template generalization.
8. Clear library/tooling and reproducibility release.

### Ideal paper

The minimum paper plus:

- a Qwen3.5 attention-to-recurrent-state handoff circuit;
- DAS separation of source, binding, and format subspaces;
- causal reuse across citation and typed entity handles;
- a minimal LFM repair intervention;
- targeted SAE features that explain a confirmed path;
- an external reproduction.

---

## 23. Likely paper figures

1. **Task and causal abstraction:** source selection → bound handle → serialization.
2. **Behavioral replication:** direct swap effects with uncertainty across models and formats.
3. **Token-stage decomposition:** first citation token versus continuation.
4. **Dense causal maps:** layer × semantic position for each architecture.
5. **Component decomposition:** attention/mixer, MLP, and recurrent-state contributions.
6. **Circuit/path diagram:** exact sender–receiver effects for Qwen2.5.
7. **LFM anomaly:** state chronology and repair intervention.
8. **Qwen3.5 hybrid mechanism:** full-attention-to-recurrent handoff, 2B versus 4B.
9. **Causal subspaces:** selective source/binding/format interchange.
10. **Generalization:** frozen-circuit effects on natural data and autoregressive generation.

Appendices should contain parity tests, all intervention baselines, per-model architecture manifests, excluded examples, power analysis, sensitivity analyses, and negative results.

---

## 24. Literature and method anchors

The implementation should reuse, adapt, or explicitly compare against these lines of work:

- Circuits and mechanistic analysis: [Distill Circuits thread](https://distill.pub/2020/circuits/).
- Causal mediation/activation patching: [ROME](https://arxiv.org/abs/2202.05262), [Interpretability in the Wild / IOI](https://arxiv.org/abs/2211.00593).
- Hypothesis testing by resampling: [Causal Scrubbing](https://www.alignmentforum.org/posts/JvZhhzycHu2Yd57RN/causal-scrubbing-a-method-for-rigorously-testing).
- Automated circuit discovery: [ACDC](https://arxiv.org/abs/2304.14997) and [auto-circuit](https://arxiv.org/abs/2407.08734).
- Efficient localization and known attribution failure modes: [AtP*](https://arxiv.org/abs/2403.00745) and TransformerLens [attribution patching](https://transformerlensorg.github.io/TransformerLens/generated/code/transformer_lens.tools.analysis.attribution_patching.html).
- Layerwise prediction: [Tuned Lens](https://arxiv.org/abs/2303.08112).
- Causal abstraction and distributed interventions: [pyvene](https://arxiv.org/abs/2403.07809).
- Linear concept erasure: [LEACE](https://arxiv.org/abs/2306.03819).
- Position-aware circuits: [PEAP](https://peap-circuits.github.io/).
- Sparse feature decomposition: [Scaling and evaluating sparse autoencoders](https://arxiv.org/abs/2406.04093) and [SAE Lens](https://github.com/decoderesearch/SAELens).
- Replacement-model attribution graphs: [Circuit Tracer](https://www.anthropic.com/research/open-source-circuit-tracing).

These methods should be cited for their appropriate role. None eliminates the need for exact, held-out, task-specific causal validation.

---

## 25. Final decision standard

The paper should be considered ready only when the evidence supports a statement of this form:

> Across preregistered held-out examples and multiple identifier formats, we causally separate semantic source selection from handle binding and token serialization. In a conventional transformer we identify a compact, faithful pathway that performs counterfactual rebinding; in hybrid architectures we show a different division of labor, including either state-mediated persistence or a reproducible failure mode. These mechanisms predict and causally alter autoregressive behavior on unseen templates and natural examples.

If the studies instead show diffuse, architecture-specific, or non-factorized mechanisms, that is also a meaningful result. The roadmap is designed so that failure of the elegant three-stage account yields a rigorous negative conclusion rather than an inconclusive collection of visualizations.
