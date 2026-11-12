---
title: Decision Models Research Portfolio
aliases:
  - Structured Decision Models Roadmap
  - System One Models Research
created: 2026-11-12
updated: 2026-11-12
status: planning
area:
  - decision-models
  - mechanistic-interpretability
  - model-serving
tags:
  - research/roadmap
  - research/decision-models
  - research/mechanistic-interpretability
  - research/model-serving
  - portfolio
---

# Decision Models Research Portfolio

> [!abstract] North star
> Understand how structured decision models turn unstructured state into calibrated, typed judgments; determine when those judgments are coherent and trustworthy; identify what decision post-training changes internally; and learn how to train and serve these models efficiently.

## Dashboard

**Current phase:** Literature review and shared evaluation harness  
**Current focus:** [[#Project 1 — Decision Symmetry|Decision Symmetry]]  
**Next milestone:** Run a small schema-invariance pilot across one open decision model and its base model.  
**Primary public artifact:** [[#Flagship blog — Inside Decision Models|Inside Decision Models]]

### Immediate next actions

- [ ] Create a clean repository or package for decision-model experiments.
- [ ] Define a provider-independent `DecisionRequest` and `DecisionResponse` schema.
- [ ] Add adapters for Transformers, vLLM, d3-mini, and joey-1.
- [ ] Construct 100 hand-verifiable Decision Symmetry examples.
- [ ] Implement option-order, label, paraphrase, and negation transformations.
- [ ] Run a one-model pilot before expanding the benchmark.
- [ ] Write the opening two sections of [[#Flagship blog — Inside Decision Models|Inside Decision Models]].

## Portfolio map

| Priority | Project | Type | Status | Expected artifact |
|---:|---|---|---|---|
| 1 | [[#Project 1 — Decision Symmetry|Decision Symmetry]] | Behavioral + calibration | 🟡 Planned | Blog + benchmark/paper |
| 2 | [[#Project 2 — Anatomy of a Decision Model|Anatomy of a Decision Model]] | Mechanistic | 🟡 Planned | Research paper |
| 3 | [[#Project 3 — Knowing When Not to Decide|Knowing When Not to Decide]] | Behavioral + systems | 🟡 Planned | Research paper |
| 4 | [[#Project 4 — Multiple-question consistency|Multiple-question consistency]] | Behavioral + structured prediction | 🟡 Planned | Blog/paper |
| 5 | [[#Project 5 — Serving-induced decision drift|Serving-induced decision drift]] | ML systems | 🟡 Planned | Systems blog/paper |
| 6 | [[#Project 6 — Training a decision model|Training a decision model]] | Training + data | ⚪ Backlog | Open recipe/model |
| 7 | [[#Project 7 — One read or many?|One read or many?]] | Architecture + systems | ⚪ Backlog | Comparative study |
| 8 | [[#Project 8 — Decision models as verifiers|Decision models as verifiers]] | Evaluation | ⚪ Backlog | Focused study |
| 9 | [[#Project 9 — Multimodal evidence arbitration|Multimodal evidence arbitration]] | Multimodal | ⚪ Backlog | Focused study |
| 10 | [[#Flagship blog — Inside Decision Models|Inside Decision Models]] | Technical synthesis | 🟡 Planned | Flagship blog |

> [!important] Scope control
> “Knowing When Not to Decide” and “When is one forward pass insufficient?” are one project. Decision Symmetry and multiple-question consistency share infrastructure, but test different phenomena: invariance of one judgment versus coherence among several judgments.

## Research identity

This portfolio studies a new class of models that map a state and typed questions directly to probabilities over predefined options. The unifying questions are:

1. **Invariance:** Does an equivalent schema produce an equivalent decision?
2. **Coherence:** Do related probabilities satisfy logical and probabilistic constraints?
3. **Calibration:** Does reported confidence correspond to empirical correctness?
4. **Mechanism:** What changes when a generative backbone becomes a decision model?
5. **Boundary:** Which tasks can be solved in one read, and which require deliberation?
6. **Systems:** Which serving primitives make decision inference fast without changing its result?

### Model families of interest

- TypeSafe Jev / System One models
- OpenAI Decisions API
- vLLM-SR Decision 3.0: d3-edge, d3-lite, d3-nano, d3-mini, d3-flash, d3-ultra
- Base Labs: joey-1, elephant-1, mammoth-1
- Cloudflare Clef joint-schema models
- Liquid d1-style first-token decision models
- Ordinary causal LMs used through label-token readout
- Encoder and cross-encoder classification baselines

---

# Shared experimental infrastructure

## Canonical request schema

```python
DecisionRequest(
    state: str | dict,
    questions: dict[str, Question],
    media: list[Media] | None,
)

Question = ChoiceQuestion | BooleanQuestion | ScoreQuestion

DecisionResponse(
    probabilities: dict[str, dict[str, float]],
    choices: dict[str, str | bool | float],
    confidence: dict[str, float],
    raw_logits: dict[str, list[float]] | None,
    latency_ms: float,
    usage: dict,
)
```

## Provider adapters

- [ ] Hugging Face Transformers reference adapter
- [ ] vLLM `/v1/decisions` adapter
- [ ] vLLM `/v1/systemone` adapter
- [ ] d3 native adapter
- [ ] joey-1 native adapter
- [ ] OpenAI Decisions API adapter
- [ ] Jev adapter, if access is available
- [ ] TEI sequence-classification baseline
- [ ] SGLang experimental first-token adapter
- [ ] TensorRT-LLM experimental classifier adapter

## Common metrics

### Predictive quality

- Accuracy
- Macro/micro F1
- Negative log likelihood
- Brier score
- Expected calibration error
- Class-conditional calibration
- Area under the risk–coverage curve

### Invariance and coherence

- Top-1 flip rate
- Jensen–Shannon divergence
- Total variation distance
- Odds-ratio drift
- Complement violation
- Implication violation
- Monotonicity violation
- Constraint-graph violation count and magnitude

### Systems

- Time to first and final decision
- Requests or questions per second
- State tokens processed per second
- GPU memory
- Cache hit rate
- Cost per thousand states
- Cost per million questions
- Probability drift across runtimes and precisions

## Reproducibility rules

- [ ] Store the exact model revision and tokenizer revision.
- [ ] Store prompt formatter and option-code mapping.
- [ ] Record runtime version, CUDA version, GPU, dtype, and quantization.
- [ ] Save raw logits when the runtime exposes them.
- [ ] Save the full probability vector, not only the selected option.
- [ ] Separate training, calibration, IID test, schema-shift, and domain-shift sets.
- [ ] Use paired tests for schema transformations.
- [ ] Include a Transformers reference run for runtime comparisons.
- [ ] Report confidence intervals over examples and transformations.

---

# Project 1 — Decision Symmetry

**Working title:** *Do Structured Decision Models Obey Their Own Probabilities?*  
**Priority:** P0  
**Status:** Planned  
**Best initial artifact:** Empirical blog that grows into a benchmark paper

## Central question

Do logically and semantically equivalent decision requests produce equivalent probability distributions?

## Hypotheses

- **H1:** Option order changes probabilities even when option semantics remain fixed.
- **H2:** Option IDs and answer-code tokens introduce stable priors independent of content.
- **H3:** Adding irrelevant or duplicate choices changes the relative odds of existing choices.
- **H4:** Negated boolean questions produce larger inconsistencies than paraphrases.
- **H5:** Decision-specific post-training improves top-1 invariance more than probability invariance.
- **H6:** Calibration degrades under schema changes even when accuracy stays constant.

## Transformations

- [ ] Option permutation
- [ ] Option-ID permutation
- [ ] Criteria paraphrase
- [ ] Question paraphrase
- [ ] Boolean negation
- [ ] JSON versus natural-language state
- [ ] Percentage versus fraction
- [ ] Positive versus negative framing
- [ ] Irrelevant alternative
- [ ] Duplicate option
- [ ] Option split
- [ ] Option merge
- [ ] Description-length manipulation
- [ ] Semantically empty label names
- [ ] UUID versus compact option identifiers

## Evaluation matrix

| Dimension | Initial values |
|---|---|
| Models | d3-mini, joey-1, Qwen3.5 base label-read baseline |
| Domains | Routing, document judgment, factual classification, synthetic logic |
| Options | 2, 3, 5, 10, 20 |
| Transformations | Order, ID, paraphrase, negation, irrelevant alternative |
| Repetitions | Deterministic reference plus repeated serving runs |

## Minimum viable pilot

- 100 canonical examples
- 5 transformations per example
- 3 models
- 1,500 decisions total
- Paired top-1 flip and probability-divergence analysis

## Strong result threshold

A result becomes paper-worthy if at least one of the following holds:

- equivalent schemas cause substantial probability shifts across most models;
- accuracy remains stable while calibration changes strongly;
- decision post-training improves one type of invariance while worsening another;
- an intervention such as permutation augmentation or consistency regularization materially fixes the problem;
- the failure predicts downstream routing or abstention errors.

## Tasks

- [ ] Define canonical schema representation.
- [ ] Implement transformation library.
- [ ] Design manual validity checks for transformed examples.
- [ ] Run the pilot.
- [ ] Plot flip rate by transformation and model.
- [ ] Plot probability simplex trajectories.
- [ ] Decide whether to expand into DECIDE-SYM.
- [ ] Write a short result note.

---

# Project 2 — Anatomy of a Decision Model

**Working title:** *From Language Model to Decision Model: What Does Decision Post-Training Change?*  
**Priority:** P0/P1  
**Status:** Planned  
**Dependency:** A stable behavioral task suite from Project 1

## Central question

Does decision post-training create new representations, reorganize existing representations, or mostly attach a better readout and calibration layer?

## Comparisons

- Qwen3.5 backbone versus joey-1
- Qwen3.5 backbone versus d3 counterpart, where matching checkpoints permit
- Base label-token readout versus trained classification head
- Frozen-backbone head training versus full fine-tuning

## Mechanistic experiments

- [ ] Layerwise linear probes for the final decision
- [ ] State–option compatibility probes
- [ ] Representational similarity across checkpoints
- [ ] Base-to-decision activation patching
- [ ] Decision-to-base activation patching
- [ ] Readout/head swaps
- [ ] Option-code direction analysis
- [ ] Positional and label-prior analysis
- [ ] Logit-lens-style layerwise decision trajectories
- [ ] Causal ablation of layers or components changed most by post-training
- [ ] Calibration decomposition: ranking versus temperature

## Candidate conclusions

1. **Readout-only account:** The backbone already represents the decision; post-training exposes it.
2. **Representation account:** Fine-tuning creates earlier and more invariant state–option features.
3. **Geometry account:** The information exists in both models, but fine-tuning makes it linearly accessible.
4. **Calibration account:** Most gains come from better scaling rather than different rankings.
5. **Hybrid account:** Different task families rely on different changes.

## Controls

- Random head with matched dimensionality
- Same-data linear probe on the base model
- Label and position permutation
- Norm-matched activation replacement
- Random-layer patching
- Equivalent generative prompting baseline
- Calibration performed on the same held-out set

## Tasks

- [ ] Identify genuinely comparable base/decision checkpoint pairs.
- [ ] Confirm identical tokenization and inspect architecture differences.
- [ ] Reproduce official inference for each decision checkpoint.
- [ ] Build activation-capture hooks.
- [ ] Run probes before causal interventions.
- [ ] Pre-register intervention predictions from probe results.
- [ ] Run patching and head-swap experiments.
- [ ] Test whether the mechanism predicts schema invariance.

---

# Project 3 — Knowing When Not to Decide

**Working title:** *Selective Escalation for System One Models*  
**Priority:** P1  
**Status:** Planned

## Central question

Where does fast, one-pass judgment break down, and does the decision model know when a slower reasoning model is required?

## Task ladder

1. Direct lexical classification
2. Single-span document lookup
3. One-hop implication
4. Multi-hop composition
5. Arithmetic comparison
6. Conflicting-evidence resolution
7. Counterfactual reasoning
8. Long-document aggregation
9. Cross-modal comparison

## Experimental conditions

- Decision model only
- Generative model, direct answer
- Generative model with reasoning
- Decision model followed by generative escalation
- Oracle escalation based on correctness
- Learned escalation based on internal features

## Questions

- [ ] Does low confidence identify difficult examples?
- [ ] Which examples are confidently wrong?
- [ ] Does entropy outperform maximum probability?
- [ ] Does schema instability predict failure better than confidence?
- [ ] Do internal features improve routing?
- [ ] What threshold minimizes cost for a target risk?
- [ ] Does the threshold transfer across domains?
- [ ] Can a small decision model reliably choose between standard and reasoning models?

## Core outputs

- Risk–coverage curves
- Accuracy versus latency/cost frontier
- Failure taxonomy
- System One capability boundary plot
- Selective escalation policy

## Tasks

- [ ] Build depth-controlled task generator.
- [ ] Define comparable direct and deliberative baselines.
- [ ] Measure decision-model confidence and correctness.
- [ ] Fit a calibration-only escalation baseline.
- [ ] Add schema-instability and internal-feature predictors.
- [ ] Evaluate domain transfer.

---

# Project 4 — Multiple-question consistency

**Working title:** *One State, Many Decisions: Are Structured Decision Outputs Jointly Coherent?*  
**Priority:** P1  
**Status:** Planned

## Central question

When several typed questions refer to one shared state, do the returned marginals satisfy known logical and probabilistic relationships?

## Example schema

```yaml
state:
  message: "I was charged twice. Please refund the duplicate charge."

questions:
  refund_requested:
    type: boolean
  billing_related:
    type: boolean
  route:
    type: choice
    options: [billing, support, sales]
  urgency:
    type: score
    levels: [low, medium, high]
  human_review:
    type: boolean
```

## Constraint graph

```text
refund_requested ⇒ billing_related
billing_related ⇒ route ≠ sales
urgency = high ⇒ P(human_review) should not decrease
route = billing ⇒ P(billing_related) should be high
```

## Experimental variables

- Questions asked separately versus together
- Question ordering
- 1, 2, 4, 8, 16, 32, 64 questions
- Explicit versus implicit dependencies
- Repeated equivalent questions
- Independent reads versus joint-schema head
- Raw output versus constrained probability projection

## Metrics

- Marginal accuracy
- Joint exact match
- Constraint violations
- Violation magnitude
- Calibration before and after projection
- Latency per question
- Probability drift caused by adding unrelated questions

## Tasks

- [ ] Build a constraint-graph representation.
- [ ] Generate synthetic states with exact labels.
- [ ] Add realistic workflow schemas.
- [ ] Implement logical consistency checker.
- [ ] Implement constrained post-processing baseline.
- [ ] Compare per-question and joint-head architectures.

---

# Project 5 — Serving-induced decision drift

**Working title:** *Does the Inference Engine Change the Decision?*  
**Priority:** P1/P2  
**Status:** Planned

## Central question

Can runtime implementation, batching, caching, numeric precision, or quantization alter probability estimates enough to change application behavior?

## Runtimes

- Transformers reference
- vLLM
- SGLang
- TensorRT-LLM
- TEI for encoder/classifier baselines

## Factors

- BF16, FP16, FP8, INT8, 4-bit
- Batch size and batch composition
- Prefix-cache hit versus miss
- Question packing
- State length
- Number of options
- Number of questions
- Tensor parallelism
- GPU generation
- Batch-invariant execution when supported

## Measurements

- Top-1 flips relative to reference
- Probability-vector divergence
- Brier and calibration drift
- Run-to-run repeatability
- Latency and throughput
- GPU memory
- Cache savings

## Important systems hypotheses

- **H1:** Small numeric changes disproportionately affect decisions near a threshold.
- **H2:** Quantization preserves accuracy better than calibration.
- **H3:** Batch-invariant execution improves repeatability at measurable throughput cost.
- **H4:** Joint-schema heads amortize long states better than per-question reads.
- **H5:** The fastest runtime depends on state length and question count, not just model size.

## Tasks

- [ ] Establish a bitwise or high-precision Transformers reference.
- [ ] Run identical requests across runtimes.
- [ ] Sweep decisions near 0.5 and production thresholds.
- [ ] Measure calibration after quantization.
- [ ] Build latency crossover plots.
- [ ] Document unsupported runtime/model combinations explicitly.

---

# Project 6 — Training a decision model

**Working title:** *What Actually Makes a Good Decision Model?*  
**Priority:** P2  
**Status:** Backlog

## Goal

Produce an open, reproducible recipe that turns a small generative backbone into a calibrated structured decision model.

## Training ladder

- [ ] Next-token label SFT
- [ ] Option and label permutation augmentation
- [ ] Frozen-backbone classification head
- [ ] LoRA decision fine-tuning
- [ ] Full decision fine-tuning
- [ ] Temperature/vector calibration
- [ ] Symmetry consistency regularization
- [ ] Abstention/selective prediction
- [ ] RLCD-like reinforcement learning

## Candidate objectives

### Supervised proper-scoring objective

```text
L = cross_entropy(correct_option)
```

### Consistency-regularized objective

```text
L = L_correct
  + λ_symmetry × divergence(p_original, unpermute(p_transformed))
  + λ_constraint × constraint_violation
```

### RLCD-like reward

```text
R = reward_correct
  - λ_brier × brier_error
  - λ_overconf × confident_error
  - λ_symmetry × schema_instability
  - λ_constraint × logical_violation
  - λ_abstain × unnecessary_abstention
```

> [!warning] Terminology
> TypeSafe’s exact “Reinforcement Learning for Calibrated Decisions” method is proprietary. Any open implementation should be described as an RLCD-like or calibrated-decision RL recipe unless the original algorithm becomes public.

## Data sources

- Classification datasets converted to state/question/options
- Multiple-choice reasoning datasets
- Tool and model routing examples
- Support/workflow routing
- Document and policy judgment
- Pairwise preference data
- Verifier and reward-model data
- Synthetic state machines
- Logically constrained multi-question records
- Multimodal classification and comparison data

## Required augmentations

- [ ] Random option order
- [ ] Random answer codes
- [ ] Criteria paraphrases
- [ ] Question paraphrases
- [ ] Negation pairs
- [ ] Hard negatives
- [ ] Irrelevant alternatives
- [ ] Option split/merge
- [ ] Missing-information and abstention cases
- [ ] Domain-held-out examples

## Split discipline

| Split | Purpose |
|---|---|
| Train | Learn task and schema |
| Validation | Tune optimization |
| Calibration | Fit temperature/thresholds only |
| IID test | Standard evaluation |
| Schema-shift test | New wording, labels, and option structure |
| Domain-shift test | New semantic domains |
| Private symmetry test | Detect augmentation overfitting |

---

# Project 7 — One read or many?

**Working title:** *Architectures for Structured Decisions*  
**Priority:** P2  
**Status:** Backlog

## Architecture taxonomy

1. **Next-token label reading** — standard causal LM, one first-token read per question.
2. **Answer-code classification** — d3-style classification head, usually one read per question.
3. **Joint schema head** — score all options for all questions in one pooling read.
4. **Decision-tuned generative model** — ordinary generation architecture trained to answer with the first token.
5. **Encoder/cross-encoder classifier** — pooled encoder representation with classification or ranking head.
6. **Hosted proprietary model** — architecture unavailable; behavior accessible through API.

## Benchmark grid

| Variable | Values |
|---|---|
| State length | 128, 512, 2K, 8K, 16K tokens |
| Questions | 1, 2, 4, 8, 16, 32, 64 |
| Options | 2, 5, 10, 26+ |
| Precision | BF16, FP16, FP8/INT8 where supported |
| Modalities | Text; text + image; text + video where available |

## Questions

- When does one joint read become faster than prefix-cached per-question reads?
- Does a joint head improve consistency or create cross-question interference?
- Which architecture calibrates best under schema shift?
- Does bidirectional/full attention help state–option matching?
- Which design scales best with many options versus many questions?

---

# Project 8 — Decision models as verifiers

**Working title:** *Fast Judgment, Shallow Judgment?*  
**Priority:** P2  
**Status:** Backlog

## Test cases

- Correct answer with invalid reasoning
- Wrong answer with persuasive reasoning
- Correct but unnecessarily verbose answer
- Incorrect answer copying reference phrases
- One subtle error in a long solution
- Right result obtained by invalid method
- Unsupported claim mixed with correct facts

## Outputs

- Correctness probability
- Error-presence probability
- Error type
- Severity score
- Escalation probability
- First-error span, where supported

## Baselines

- Generative LLM judge
- Outcome reward model
- Process reward model
- Encoder classifier
- Execution-based verifier
- Simple lexical/style baselines

---

# Project 9 — Multimodal evidence arbitration

**Working title:** *Which Modality Does a Decision Model Trust?*  
**Priority:** P3  
**Status:** Backlog

## Controlled evidence conditions

- Text correct, image misleading
- Image correct, text misleading
- Both correct
- Both incorrect
- One modality absent
- Low-resolution or occluded image
- Duplicate evidence
- Conflicting images
- Evidence order manipulation

## Main analysis

Track how the full probability vector changes as evidence is added, removed, degraded, or contradicted. Distinguish accuracy from evidence sensitivity and calibration.

---

# Flagship blog — Inside Decision Models

**Working title:** *Inside Decision Models: Architectures, Training, Calibration and High-Performance Serving*  
**Status:** Planned  
**Format:** Long technical article with diagrams, code, benchmarks, and a small trained model

## Thesis

Decision models are not merely chat models forced to emit JSON. They replace open-ended decoding with typed probabilistic judgment, creating different training objectives, evaluation requirements, failure modes, and serving opportunities.

## Proposed outline

### 1. What is a decision model?

- State, question, criteria, and probability interface
- System One judgment versus generative response
- Difference from classifiers, rerankers, reward models, and LLM judges
- Typed output versus factual reliability
- Jev, OpenAI Decisions, d3, Joey, Clef, and Liquid d1 ecosystem

### 2. Architecture taxonomy

- Next-token label reading
- Answer-code readout
- Sequence-classification head
- Joint schema head
- Encoder/cross-encoder model
- Multimodal variants
- Proprietary hosted models

### 3. Probability semantics

- Option-normalized probability
- Full-vocabulary label mass
- Confidence versus calibrated correctness
- Temperature scaling
- Abstention and refusal
- Why probabilities from different architectures need not mean the same thing

### 4. Creating decision datasets

- Converting classification and MCQ datasets
- Tool, model, and workflow routing
- Document judgments
- Judge/verifier data
- Synthetic state machines and constraint graphs
- Option randomization and counterfactual augmentation
- Calibration and shift splits
- Avoiding benchmark contamination and schema overfitting

### 5. Training recipes

- Label-token SFT
- Classification heads
- Frozen versus trainable backbone
- LoRA versus full fine-tuning
- Proper-scoring objectives
- Pairwise/listwise objectives
- Consistency regularization
- Calibration stages
- Abstention training
- RLCD claims versus reproducible RLCD-like training

### 6. Optimization primitives

- No long autoregressive decode
- One-token or no-token output
- Selective option logits
- Pooled final-state readout
- Shared-state prefill reuse
- Prefix/KV caching
- Continuous batching
- Question packing
- Joint schema heads
- Multimodal encoder reuse
- Quantization
- Fused softmax/calibration

### 7. What does *not* help much?

- Speculative decoding
- Token streaming
- Long decode optimizations
- Sampling algorithms intended for creative generation

### 8. Serving frameworks

#### vLLM

- Native `/v1/decisions` and `/v1/systemone` surfaces
- Next-token, classification, and joint-schema read strategies
- Prefix caching for compatible per-question reads
- Raw logits and label-mass diagnostics
- Batch-invariant execution trade-off

#### SGLang

- First-token label-logprob implementation
- Radix/shared-prefix reuse
- Custom endpoint or wrapper requirements
- Verify native decision-schema support before claiming parity

#### TensorRT-LLM

- Generation-logit access
- Encoder/classification outputs
- Quantization and kernel opportunities
- Custom packaging needed for a complete Decisions API surface

#### TEI

- Natural fit for encoder classifiers and rerankers
- `/predict` and `/rerank`
- Efficient batching
- Not automatically compatible with causal answer-code checkpoints

#### Transformers

- Correctness reference
- Easiest training and mechanistic access
- Not the production-throughput baseline

### 9. Hands-on build

- Start from a 0.8B–2B backbone
- Construct typed-decision data
- Train label-token baseline
- Train a decision head
- Calibrate on a held-out split
- Add symmetry regularization
- Serve through one production runtime
- Compare against the base model

### 10. Open research problems

- Decision symmetry
- Logical consistency
- Calibration under shift
- One-pass capability boundaries
- Serving-induced probability drift
- Multimodal evidence arbitration
- Mechanistic effects of decision post-training

## Blog production checklist

- [ ] Confirm every architecture claim against code or primary documentation.
- [ ] Draw architecture taxonomy diagram.
- [ ] Draw training pipeline diagram.
- [ ] Draw runtime optimization diagram.
- [ ] Train at least one small decision model.
- [ ] Include one reproducible dataset-building script.
- [ ] Include one serving benchmark.
- [ ] Include one failure case from Decision Symmetry.
- [ ] Clearly label proprietary claims and unknowns.
- [ ] Publish code, configs, and exact checkpoint revisions.

---

# Serving optimization notebook

## Primitive-by-architecture matrix

| Primitive | Next-token read | D3-style classifier | Joint schema head | Encoder classifier |
|---|---:|---:|---:|---:|
| Autoregressive decode | One token | None | None | None |
| Prefix/KV reuse | Often useful | Architecture-dependent | State read once | Not KV-based |
| Question batching | Yes | Yes | Native joint read | Yes |
| Raw option logits | Label-token logits | Classification logits | Schema-head logits | Class logits |
| Continuous batching | Yes | Yes | Yes | Yes |
| Speculative decoding | Little value | No value | No value | No value |
| Quantization | Useful | Useful; verify calibration | Useful; verify calibration | Useful |
| Multimodal encoder reuse | Model-dependent | Often possible | Natural opportunity | Model-dependent |

## Benchmark questions

- At what number of questions does a joint head beat prefix-cached independent reads?
- Does a longer shared state make prefix caching more valuable?
- Does full/bidirectional attention disable useful cache primitives?
- How much throughput is lost for batch-invariant probability outputs?
- Does FP8 preserve ranking but damage calibration?
- Can calibration be repaired after quantization with a new temperature?
- Should option softmax run on GPU or CPU?
- Is it faster to score all vocabulary logits or gather only option codes?
- How does serving cost scale with questions versus options?

---

# Reading list

## Decision model ecosystem

- [ ] [OpenAI Decisions API](https://developers.openai.com/api/docs/guides/decisions)
- [ ] [vLLM Structured Decisions](https://docs.vllm.ai/en/latest/serving/online_serving/decisions/)
- [ ] [vLLM Structured Decision Models](https://docs.vllm.ai/en/latest/serving/online_serving/structured_decisions/)
- [ ] [vLLM Semantic Router documentation](https://vllm-sr.ai/docs/next/model-runtime/choose-a-model/)
- [ ] [d3-mini model/runtime documentation](https://app.vllm-sr.ai/docs)
- [ ] [joey-1 model card](https://huggingface.co/baselabs/joey-1)
- [ ] [TypeSafe: Introducing System One Models and Jev](https://typesafe.ai/blog/introducing-system-one-models-and-jev)
- [ ] [Artificial Analysis Decision Index](https://artificialanalysis.ai/evaluations/artificial-analysis-decision-index)
- [ ] [Jev Decision Index dataset](https://huggingface.co/datasets/multimodalart/decision-index-leaderboard)

## Calibration and selective prediction

- [ ] [QA-Calibration of Language Model Confidence Scores — ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/cd96cb9a239c37b39dbf34f3f5a4c56f-Abstract-Conference.html)
- [ ] [Trust or Escalate — ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/08dabd5345b37fffcbe335bd578b15a0-Abstract-Conference.html)
- [ ] [Learning to Route LLMs with Confidence Tokens — ICML 2025](https://proceedings.mlr.press/v267/chuang25b.html)
- [ ] [MetaFaith — EMNLP 2025](https://aclanthology.org/2025.emnlp-main.1505/)

## Routing and judgment

- [ ] [RouteLLM — ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/5503a7c69d48a2f86fc00b3dc09de686-Abstract-Conference.html)
- [ ] [BEST-Route — ICML 2025](https://proceedings.mlr.press/v267/ding25d.html)
- [ ] [Improving LLM-as-a-Judge with the Judgment Distribution — EMNLP Findings 2025](https://aclanthology.org/2025.findings-emnlp.1259/)
- [ ] [Judging the Judges: Position Bias](https://aclanthology.org/2025.ijcnlp-long.18/)

## Serving frameworks

- [ ] [TEI quick tour](https://huggingface.co/docs/text-embeddings-inference/quick_tour)
- [ ] [TEI supported models](https://huggingface.co/docs/text-embeddings-inference/supported_models)
- [ ] [TensorRT-LLM documentation](https://nvidia.github.io/TensorRT-LLM/)
- [ ] [SGLang documentation](https://docs.sglang.ai/)

---

# Decision log

| Date | Decision | Reason | Revisit when |
|---|---|---|---|
| 2026-11-12 | Begin with Decision Symmetry | No training required; generates shared infrastructure | Pilot reveals negligible effect |
| 2026-11-12 | Merge one-pass limits with selective escalation | Same hypothesis and evaluation ladder | A distinct architectural mechanism emerges |
| 2026-11-12 | Keep joint consistency separate from symmetry | One tests invariance; the other tests constraint satisfaction | Shared benchmark becomes too fragmented |
| 2026-11-12 | Treat exact RLCD as unknown | Public descriptions do not specify a reproducible algorithm | TypeSafe publishes technical details |

---

# Experiment note template

Copy this section into a separate note for each experiment.

```markdown
---
title: EXP — Short experiment name
date: YYYY-MM-DD
project: "[[Decision Models Research Portfolio]]"
status: planned
tags:
  - experiment/decision-models
---

# EXP — Short experiment name

## Question

## Prediction

## Independent variables

## Dependent variables

## Models and revisions

## Dataset and split

## Runtime configuration

## Controls

## Stopping rule

## Results

## Interpretation

## Alternative explanations

## Follow-ups

## Artifact paths
```

# Paper note template

```markdown
---
title: "Paper — Title"
authors: []
year:
venue:
url:
tags:
  - paper/decision-models
---

# Paper — Title

## One-sentence claim

## Problem

## Method

## Evidence

## What is genuinely new?

## Weaknesses

## Assumptions

## Reproducible components

## Connection to my projects

## Experiment inspired by this paper
```

# Weekly review template

```markdown
## Week of YYYY-MM-DD

### Completed
- [ ]

### Evidence produced
-

### Decisions made
-

### Blockers
-

### Next three actions
1.
2.
3.

### Scope check
- Am I testing a concrete hypothesis?
- Will the result be informative if negative?
- Am I collecting full probability vectors?
- Is the experiment reusable by another project?
```

---

# Definition of done

## Blog-quality project

- [ ] One clearly stated phenomenon
- [ ] At least two model families
- [ ] Controlled counterfactuals
- [ ] Full probability analysis
- [ ] Reproducible code and data
- [ ] At least one surprising or decision-relevant result
- [ ] Clear limitations and alternative explanations

## Workshop/paper-quality project

- [ ] Strong baselines
- [ ] Multiple model sizes or families
- [ ] Held-out domain or schema shift
- [ ] Statistical uncertainty
- [ ] Mechanistic or causal evidence where claimed
- [ ] Ablation of the proposed explanation or method
- [ ] Public benchmark or reusable artifact
- [ ] Negative results reported

---

# Parking lot

- Decision models for active learning and label acquisition
- Continual calibration under changing class priors
- Personalized decision thresholds
- Cost-sensitive and asymmetric decisions
- Decision explanations without generating rationalizations
- Adversarial option descriptions
- Multilingual schema transfer
- Fairness and subgroup calibration
- Private or sensitive state processing
- Decision-model ensembles
- Distilling reasoning models into decision models
- Decision models for reward modeling
- Decision models as RAG rerankers
- Span extraction plus typed decisions
- Decision-specific quantization-aware training
- Online recalibration without backbone updates

---

# Progress log

## 2026-11-12

- Created portfolio roadmap.
- Prioritized Decision Symmetry as the first executable study.
- Defined five core projects and a flagship systems/training blog.
- Identified shared infrastructure and reusable evaluation metrics.

