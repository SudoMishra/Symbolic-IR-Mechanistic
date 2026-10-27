---
title: "The Hidden Cost of UUIDs: Building a Symbolic IR for LLM Systems"
description: "What 18,020 behavioral records, 23,620 model calls, 960 hidden-state passes, 1,056 causal interventions, and 5,000 adversarial tests taught us about UUIDs in LLM interfaces."
author: "Sudo Mishra (Symbolic IR Project)"
date: "October 2026"
repository: "https://github.com/SudoMishra/Symbolic-IR-Mechanistic"
---

# The Hidden Cost of UUIDs: Building a Symbolic IR for LLM Systems

**Author:** Sudo Mishra (Symbolic IR Project)  
**Date:** October 2026  
**Repository:** [github.com/SudoMishra/Symbolic-IR-Mechanistic](https://github.com/SudoMishra/Symbolic-IR-Mechanistic)

Modern LLM applications routinely place machine-generated identifiers directly inside prompts: document UUIDs, database primary keys, account numbers, transaction hashes, tool-call IDs, and workflow handles. Because these strings already exist in backend databases, engineers treat the LLM context window as a transparent transport pipe.

That assumption is expensive and fundamentally flawed. An autoregressive language model is not a relational database index. It is a probabilistic token predictor with finite attention capacity and tokenization constraints. Passing high-entropy, opaque strings forces the model to encode, track, and reproduce meaningless characters—often degrading attribution accuracy and inflating latency.

This engineering report synthesizes a comprehensive empirical investigation: **18,020 behavioral records / 23,620 model calls** (the difference comes from 5,600 two-pass records), **960 paired hidden-state passes**, **1,056 causal interventions**, and **5,000 adversarial tests** of a deterministic symbolic boundary.

The central thesis is not the naive claim that “short aliases make models smarter.” The defensible, systems-grounded rule is:

> **Keep a literal value in model context when its characters are part of the problem. Otherwise, expose a compact request-scoped symbolic handle, validate the model’s symbolic output, and rehydrate it in trusted software.**

![Figure 1 — Representation boundary between software and model: Trusted software replaces transport keys with request-scoped handles; literal values never enter model context.](assets/01_raw_vs_symbolic.svg)

> **Figure 1 — Representation boundary between software and model.** This figure shows a representation boundary, not a new reasoning algorithm. The application begins with literal database identifiers and potentially sensitive values. Before constructing the prompt, trusted software replaces those values with request-scoped handles such as `<SOURCE_1>` and records the reversible mapping in a protected vault. The model sees the same semantic facts but not the backend identifiers. Its symbolic response is validated before trusted software uses the vault to restore the original values. Canonicalization controls representation and exposure; it does not prove that the model selected the correct record or had permission to act on it.

---

## PART I: THE SETUP & THE METRIC TRAP

### Opaque Literals in Context

To see the problem clearly, consider what happens when a standard retrieval-augmented generation (RAG) system feeds retrieved documents to a model:

```text
=== RAW APPLICATION PAYLOAD (High-Entropy Backend Literals) ===
Source 8ce71ad9-71f2-4a03-b7f2-26f64e0db302:
Account ACCT-GB-4490-9812 belongs to Maya Chen. Contact: maya.chen@internal.corp.

Source b3a02e31-4f09-4d31-b90f-8a884315c28a:
Account ACCT-US-8177-2044 belongs to Luis Ortiz. Contact: luis.ortiz@internal.corp.

Question: Which account belongs to Maya Chen? Cite the source document UUID.
```

Under the native tokenizers used in these experiments, UUID identifiers averaged roughly **25 to 35 tokens**. A representative segmentation looks like this:

```text
["8", "ce", "71", "ad", "9-", "71", "f", "2-", "4a", "03-", "b", "7f", "2-", "26", "f", "64", "e0", "db", "30", "2"]
```

Now compare this with an **Intermediate Representation (IR)** using request-scoped symbolic handles:

```text
=== SYMBOLIC MODEL VIEW (Typed Request-Scoped Handles) ===
<SOURCE_1>:
<ACCOUNT_1> belongs to Maya Chen. Contact: <EMAIL_1>.

<SOURCE_2>:
<ACCOUNT_2> belongs to Luis Ortiz. Contact: <EMAIL_2>.

Question: Which account belongs to Maya Chen? Return the account and supporting source handle.
```

Across the tested tokenizers, `<SOURCE_1>` averaged roughly **5.5 to 6 tokens**. Across 20 retrieved passages, UUIDs add hundreds of tokens of high-entropy noise to prefill, consume KV-cache memory, risk literal copying errors at the output head, and needlessly expose internal database identifiers and personal data to the model.

### The Core Engineering Questions

We set out to answer three concrete questions:
1. **The Transport Question:** How much do opaque identifiers inflate input tokens, output tokens, and end-to-end generation latency?
2. **The Attribution Question:** Does identifier surface form actively degrade the model’s ability to bind facts to sources, even when task content and source order are held identical?
3. **The System Boundary Question:** Can a lightweight, deterministic software layer manage the mapping outside model context, validate symbolic responses, and guarantee representation integrity?

### Experimental Design: Paired by Construction

To measure representation effects without confounding them with content difficulty, our harness enforced strict controls:

- **Canonical Semantic Units:** Prompts were never authored as isolated strings. Each example was generated as a canonical object (question, passages, gold answer, gold source keys) and rendered into target identifier families (*numeric* `[1]`, *structured* `[S1]`, *random compact* `[XQ7M]`, *long hex*, *UUID*, and *typed entity handles*) only at inference time.
- **Identical Sequence Order:** Within every paired comparison, passage order, question phrasing, and distractor sets were identical.
- **Native Tokenizer Accounting:** Input and output lengths were logged using each model's native tokenizer, rather than character approximations.
- **Pinned Model Revisions & Deterministic Decoding:** All behavioral runs used temperature 0 decoding against pinned local GGUF models across five small/edge model families (1.2B to 4B parameters):
  - Qwen2.5-1.5B-Instruct (Q4_K_M)
  - LiquidAI LFM2.5-1.2B-Instruct (Q4_K_M)
  - Google Gemma 4 E2B Instruct (Q4_0)
  - Google Gemma 4 E4B Instruct (Q4_0)
  - Cohere Tiny Aya Global (Q4_K_M)
- **Scale:** The dataset comprises **18,020 behavioral records / 23,620 model calls** across behavioral stages (including an initial 20-record end-to-end smoke test), 960 BF16 hidden-state passes, 1,056 causal interventions, and 5,000 adversarial test cases.

![Figure 2 — Experimental evidence program across five testing regimes: Keeping behavioral generations, stress tests, mechanistic measurements, generalization, and deterministic software tests separate.](assets/02_evidence_funnel.svg)

> **Figure 2 — Experimental evidence program across five testing regimes.** This figure summarizes the evidence program and keeps different kinds of observations separate. The behavioral stages measure what models generate under controlled identifier formats. The stress tests ask whether additional scratchpad budget or verbose reasoning repairs the problem. The mechanistic stages inspect internal representations and intervene on them, without counting those forward passes as behavioral generations. The entity-resolution stage tests whether the idea generalizes beyond citations. Finally, the system stage evaluates deterministic software rather than model intelligence. The stages therefore strengthen different parts of the argument and should not be combined into one inflated sample count.

### The Citation Metric Trap

Our initial tests revealed an immediate trap in citation evaluation. When we tested Qwen2.5-1.5B on 20-source prompts, its **strict citation accuracy** was **7% for structured labels `[S1]` versus 34% for UUIDs**. 

On the surface, it looked like UUIDs performed five times better. But inspecting the raw outputs revealed the mismatch: Qwen selected the correct structured source in **66%** of cases, but often emitted `S7` instead of `[S7]`. Because strict evaluation requires exact character matching of the enclosing brackets, the evaluator marked those citations wrong. With UUIDs, the model selected the right source less often, but copied the prompt's formatting wrapper more reliably when it did.

To prevent surface syntax from masquerading as reasoning failure, we decomposed citation evaluation into a multi-stage pipeline:

```text
Solve problem → Select evidence → Bind to handle → Reconstruct literal → Format syntax
```

Throughout this work, we report separate metrics:
- **Answer Exact Match / F1:** Does the model produce the correct answer string?
- **Relaxed Source Binding:** Does the emitted identifier map back to the gold source in the mapping vault, tolerating surface formatting variations (e.g., omitted brackets)?
- **Strict Citation:** Requires exact identifier reconstruction AND exact syntax wrapper matching.
- **Surface-Only Failure:** The model selected the correct source, but violated the requested wrapper or casing.

> **Takeaway for evaluators:** Never publish a single citation metric. If you do not decouple semantic evidence selection from surface wrapper formatting, you are measuring bracket retention, not model factuality.

### Grounding in Related Work

This investigation connects three previously disparate threads in ML systems:
1. **Binding IDs in Transformers:** Feng & Steinhardt (2023) demonstrated that transformers track entities across long contexts by binding them to identifier tokens. Our work tests how identifier entropy and tokenization boundaries interact with that binding mechanism in production retrieval.
2. **Citation Evaluation:** The ALCE benchmark (Gao et al., 2023) established standard citation recall and precision metrics for RAG. Our metric decomposition directly addresses ALCE’s vulnerability to surface formatting discrepancies.
3. **Symbolic Trust Boundaries & Untrusted Views:** The CaMeL framework (Debenedetti et al., 2025) and the Dual-LLM pattern (Willison, 2023) propose isolating untrusted data and privileged tools. Our reference architecture applies the same separation principle: a request-scoped mapping vault reduces literal exposure and rejects malformed symbolic outputs. It does not make retrieved content trustworthy or neutralize prompt injection.

---

## PART II: THE BEHAVIORAL EVIDENCE (SYNTHETIC TO MULTI-HOP)

### Controlled Baseline: Qwen 5 vs. 20 Sources

Our baseline experiment compared structured labels `[S1]` against full UUIDs across 100 paired questions at 5 sources, and another 100 at 20 sources:

| Sources | Identifier Type | Answer Accuracy | Strict Citation | Relaxed Source Binding | Mean Input Tokens | Mean Latency |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|
| **5** | Structured `[S1]` | **100%** | 68% | **96%** | 234.6 | **1.74 s** |
| **5** | UUID | 98% | 29% | 63% | 385.5 | 4.36 s |
| **20** | Structured `[S1]` | 90% | 7% | **66%** | 639.3 | **5.27 s** |
| **20** | UUID | **92%** | **34%** | 37% | 1,237.4 | 11.96 s |

The results illustrate the core phenomenon:
1. **Answer accuracy is invariant:** At 20 sources, answer correctness was 90% vs. 92%—well within statistical parity. The model found the required fact regardless of identifier format.
2. **Relaxed binding degrades severely:** Relaxed source binding collapsed from **66% down to 37%** under UUIDs. The model knew the answer, but lost track of which document provided it.
3. **The Transport Tax is massive:** At 20 sources, UUIDs added **93.5% more input tokens** (1,237.4 vs. 639.3) and increased generation latency from **5.3 seconds to 12.0 seconds** on the local CPU runtime.

Across all four initial models at 20 sources, UUIDs imposed a **70% to 94% input token tax** and a **77% to 129% latency overhead**.

The binding result was not universal. Gemma E2B reversed the Qwen/LFM pattern in this synthetic baseline: UUID binding exceeded structured-label binding by **37 points at five sources** and **25 points at twenty sources**, with both paired intervals excluding zero. Gemma E4B was at ceiling for both formats. That counter-result is why the later held-out MuSiQue study reports each model and source-count cell separately rather than claiming a universal accuracy advantage.

### Skeptical Follow-Up: Does This Survive Real Multi-Hop Retrieval?

Synthetic single-hop citation prompts isolate variables cleanly, but real-world engineering workloads involve noisy, multi-hop retrieval. Does the UUID binding penalty persist when questions require reasoning across multiple passages?

To test this, we evaluated the models on **MuSiQue**, a challenging multi-hop benchmark. We filtered 100 balanced questions (34 two-hop, 33 three-hop, and 33 four-hop examples) screened so that every prompt fell within 2,000 to 3,700 tokens across all native tokenizers. We tested across 15 and 20 retrieval passages.

Across the initial 7,500 generations (MuSiQue Stages 2–4), UUID relaxed source binding recall was lower in all 10 model/source-count cells. 

To ensure this was not an artifact of example selection, we drew a **completely disjoint, held-out cohort of 100 balanced MuSiQue questions** and ran **2,000 independent confirmatory generations** across all five model families:

![Figure 3 — Every held-out estimate favored numeric labels; six were conclusive: UUID minus numeric relaxed source-binding recall across 10 model/source-count cells in held-out MuSiQue (2,000 generations).](assets/03_musique_confirmation.svg)

> **Figure 3 — Held-out MuSiQue binding effects.** Each row compares the same held-out questions under UUID and numeric source labels. A value of −10 percentage points means that UUIDs reduced relaxed source-binding recall by ten points relative to numeric labels. The dot is the observed paired difference, and the horizontal line shows its 95% bootstrap interval. All ten point estimates fall to the left of zero, so every observed comparison favored numeric labels. Six intervals remain entirely below zero, providing clearer evidence of a difference; four cross zero and should be treated as directionally consistent but statistically inconclusive. Answer F1 did not show the same pattern, so the result concerns attribution rather than general question answering.

| Model Family | Sources | UUID − Numeric Binding Recall (pp) | Paired 95% Bootstrap CI | Excludes Zero? |
|:---|:---:|:---:|:---:|:---:|
| **Tiny Aya** | 15 | **-11.4** | [-17.1, -6.1] | **Yes** |
| **Tiny Aya** | 20 | **-14.8** | [-20.2, -9.7] | **Yes** |
| **LFM 1.2B** | 15 | **-7.5** | [-13.4, -1.6] | **Yes** |
| **LFM 1.2B** | 20 | **-6.1** | [-12.1, -0.5] | **Yes** |
| **Qwen 1.5B** | 15 | **-6.8** | [-12.3, -1.2] | **Yes** |
| **Qwen 1.5B** | 20 | -0.8 | [-5.1, +3.2] | No |
| **Gemma E2B** | 15 | -3.1 | [-8.3, +2.4] | No |
| **Gemma E2B** | 20 | -4.8 | [-10.1, +0.1] | No |
| **Gemma E4B** | 15 | **-5.8** | [-10.9, -0.9] | **Yes** |
| **Gemma E4B** | 20 | -3.4 | [-9.1, +2.3] | No |

### The Critical Findings from Held-Out MuSiQue:
1. **Directional Consistency:** In **10 out of 10 cells**, the estimated point effect of UUIDs on relaxed source binding was negative. In 6 of 10 cells, the 95% confidence interval strictly excluded zero.
2. **Answer F1 Remains Flat:** As in the synthetic task, Answer F1 differences between UUID and numeric conditions were small and centered near zero (all 95% intervals spanned zero).
3. **The Buried Engineering Insight (Dual Labels):** Many teams attempt a shortcut: keeping the raw UUID in the prompt but appending a short alias next to it (e.g., `Source 8ce71... [S1]`). In MuSiQue Stage 4, **dual labels failed to reliably recover alias-only performance**. The result is consistent with additional representation burden, but Stage 4 does not identify an attention-head mechanism. You cannot remove the UUID tax by adding more text.

---

## PART III: ABLATIONS & MECHANISTIC DEEP DIVE

Having observed consistent binding penalties and transport costs, we designed targeted ablations to test competing hypotheses.

### Ablation 1: Is It Just Token Length, or Syntax Formatting?

Could the difference between `[S1]` and UUIDs simply be that UUIDs are longer?

We ran a controlled token-matched pilot comparing `[1]` with `[S1]` across four models. Both representations averaged exactly **3.55 tokens per identifier** and identical prompt lengths (639 tokens). 

On Qwen, numeric labels `[1]` beat structured labels `[S1]` by **67 percentage points on strict citation formatting**, yet the relaxed binding difference was only **8 points** (with a confidence interval spanning zero). Most of the "gain" came from the tokenizer/prior bias: the model reliably retained brackets around standalone digits `[1]`, but frequently stripped brackets from `[S1]`.

Next, we tested the **no-reproduction control**: leaving UUIDs in the prompt for reading, but removing the requirement to cite them in the output. When citation reproduction was removed:
- LiquidAI LFM answer F1 improved by **+3.5 points**.
- Gemma E4B answer F1 improved by **+5.1 points**.

In those two cells, requiring UUID reproduction was associated with lower answer F1. The control does not isolate whether the difference came from literal emission itself, the stricter output instruction, or their interaction.

### Ablation 2: Can Chain-of-Thought / Reasoning Budgets Overcome It?

A seductive theoretical hypothesis is that opaque identifiers consume *internal bookkeeping capacity*. If true, giving the model more reasoning tokens (a larger scratchpad) should allow it to "think through" the bookkeeping, causing the UUID penalty to shrink monotonically as budget increases.

We tested this hypothesis across **5,600 two-pass generations (11,200 model calls)**: 2,400 pilot generations across five models and 3,200 separately seeded confirmatory generations in the retained cells. Pass 1 received the multi-source prompt and a visible scratchpad cap of 64, 128, 256, 512, or 1,024 tokens. Pass 2 received only that generated scratchpad and had a fixed 128-token budget to emit the final answer.

The confirmatory experiment evaluated cells meeting a pre-declared calibration threshold:

![Figure 4 — More scratchpad did not consistently repair UUID performance: UUID minus numeric final-answer accuracy across visible scratchpad budgets (64 to 1,024 tokens) across 5,600 two-pass generations (11,200 model calls).](assets/04_reasoning_budget.svg)

> **Figure 4 — Reasoning-budget experiment.** The experiment used two passes. Pass 1 received the original multi-source problem and a scratchpad limit ranging from 64 to 1,024 tokens. Pass 2 saw only that scratchpad and produced the final answer. Each point reports final-answer accuracy under UUID identifiers minus accuracy under numeric labels. Values below zero favor numeric labels; values above zero favor UUIDs. Qwen remained mostly below zero, Gemma E2B changed direction sharply, and Tiny Aya moved toward parity at larger budgets. Because the effects do not move consistently toward zero as the budget grows—and most intervals are broad—the data reject a universal monotonic recovery story. They do not prove why Gemma E2B changes direction.

**The Result: The Monotonic Hypothesis Failed.**
- Every confirmatory slope estimate and every low-to-high interaction interval included zero. Additional reasoning budget did not smoothly erase the UUID penalty.
- Qwen maintained significant UUID deficits at 128 tokens (-20.0 pp) and 1,024 tokens (-21.2 pp).
- **The Gemma E2B anomaly remains an inference:** At 64 tokens, Gemma E2B showed a -35.0 pp UUID deficit. At 256 tokens, UUIDs beat numeric by +50.0 pp (+30.0, +70.0 CI). The traces are consistent with an output-length confound: UUID scratchpads were longer, and the UUID condition hit the cap on every 64- and 128-token pilot run. That may have preserved more information for Pass 2, but the experiment does not establish this mechanism. When UUID reproduction was removed at 512 and 1,024 tokens, Gemma E2B reached **95% and 100% accuracy**.
- **What Did Replicate:** UUIDs increased total generated output in **14 of 15 confirmatory cells**. The transport and generation cost is universal; the cognitive scratchpad interaction is not.

> **Sidebar: Why long traces are not reasoning (the LongProc reality check)**
>
> To ensure we did not equate verbose generation with correct reasoning, we benchmarked our four models on **LongProc**, a public benchmark requiring deterministic belief-state tracking over 1,024–2,048 token reference traces.
> 
> The results offer a stark warning:
> - **Qwen2.5-1.5B** generated an average of **2,027 output tokens** and hit the hard 2,048 token cap on **84% of runs**, yet achieved a mean correct-prefix accuracy of only **1.2%**. It looped verbosely without maintaining state.
> - **Gemma 4 E4B** achieved **76% final-answer accuracy**, but produced an exact state trace only **8% of the time**.
> 
> ![Figure 5 — Long generation does not establish procedural correctness: Comparing mean correct-trace prefix before first error, final-answer accuracy, and exact full-trace accuracy across 25 LongProc belief-state instances.](assets/05_longproc.svg)
> 
> **Figure 5 — LongProc trace quality.** LongProc supplies a deterministic reference sequence of state updates, allowing the generated procedure to be checked step by step. The blue bar measures how much of that reference trace the model completes before its first error. The green bar measures only whether the final answer is correct, while the orange bar requires the complete generated trace to match. These metrics can diverge: Gemma E4B answered 76% of examples correctly but produced the exact full trace only 8% of the time. Qwen generated about 2,027 tokens on average yet achieved only a 1.2% correct-prefix score. The result is not that long outputs are always bad; it is that output length and final-answer accuracy do not establish procedural correctness.
> 
> An application that evaluates only the final answer or celebrates long Chain-of-Thought traces is blind to procedural failure.

### Ablation 3: Inside the Transformer — Stable Facts, Late Realization

If the model knows the answer but misattributes the source, what is happening inside the network?

In Stage 6, we extracted residual-stream hidden states from **960 paired forward passes** across official BF16 checkpoints of Qwen2.5-1.5B, LFM2.5-1.2B, Gemma 4 E2B, and Gemma 4 E4B on 80 semantic examples rendered under structured, random compact, and UUID formats.

![Figure 6 — Fact-token geometry stays stable; identifier geometry is model- and depth-dependent: Structured-vs-UUID linear CKA similarity across normalized model depth across 960 paired hidden-state passes (80 examples).](assets/06_stage6_geometry.svg)

> **Figure 6 — Representation geometry across layers.** Linear CKA compares the geometry of hidden representations across the same 80 examples under two prompt formats: structured source labels and UUIDs. A value near one means that the relationships among examples are represented similarly in both conditions; it does not mean that individual vectors or model outputs are identical. The teal curves remain above roughly 0.94 because the passage facts are unchanged and surrounding UUIDs do not substantially reorganize their representation. Identifier-label states begin less aligned and often become more similar in middle layers, but the pattern varies by architecture and Gemma E2B diverges sharply at the final layer. This is correlational evidence about representation geometry, not proof of a particular causal circuit.

Using Linear Centered Kernel Alignment (CKA) across normalized model depth, three patterns emerged:
1. **Source-Fact Geometry is Format-Invariant:** The per-model minimum CKA for source-content tokens ranged from **0.941 to 0.979**. Because fact tokens share identical text across conditions, high correlation is expected; the important finding is that surrounding high-entropy UUIDs do not distort the semantic representation of the passage text.
2. **Source Labels Converge:** Source-label representations start far apart at the lexical embedding layer, but converge significantly in mid-network layers as the model binds them to their respective passages. (Note: in LFM, label CKA fluctuates between 0.67 and 0.89, while in Gemma E2B, label representations collapse to ~0.37 at the final layer).
3. **Late Surface Divergence:** Representations at the position immediately preceding citation emission diverge, becoming highly format-specific near the output heads.

### Causal Interventions: Source-ID Swaps & Activation Patching

CKA is purely correlational. To prove causality, Stage 7 performed **66 counterfactual source-ID swaps** and **1,056 residual-stream activation patches**.

For each example, we swapped the identifier assigned to the relevant source with a distractor identifier while holding all passage text, questions, and distractor sets constant. A positive log-probability delta indicates the model successfully followed the source fact to its reassigned identifier.

![Figure 7 — After an ID swap, models do not all rebind to the relevant source: Mean change in log P(newly correct ID) minus log P(previous ID) after prompt-level ID swaps (66 counterfactual swaps and 1,056 activation interventions).](assets/07_stage7_swaps.svg)

> **Figure 7 — Counterfactual source-ID swaps.** This intervention changes only which identifier is attached to the relevant passage. The facts, question, distractors, and set of available identifiers remain unchanged. The plotted effect asks whether the prompt swap moves the model’s probability from the formerly correct identifier toward the identifier now attached to the relevant source. Positive values indicate successful rebinding; negative values indicate persistence of the old association. Qwen is positive across formats, whereas LFM is negative for the compact formats. The Gemma estimates are positive but come from very small pilot cohorts and should not be treated as stable population estimates. Because full UUIDs contain more tokens, total sequence log-probability magnitudes are not directly comparable across identifier formats.

The causal interventions produced a critical revelation: **Shared representational geometry does not imply a shared causal circuit.**
- **Qwen and Gemma pilots** showed positive direct swap effects: the models assigned more probability to the newly correct identifier after the swap. The intervention does not identify a specific attention-head mechanism.
- **LiquidAI LFM** was causally sensitive but reacted in reverse: under compact IDs, swapping the source ID caused LFM to strongly reinforce its *prior* lexical association.
- **Activation Patching & Onset Layers:** Patching the residual stream at the final layer transferred ~100% of the counterfactual swap effect in all models (an expected property, as the final residual directly projects to logits). The real distinction lies in the **onset layer** where the binding decision becomes locked:
  - In **Qwen**, transferable citation states emerge early at **layer 24** (74–108% transfer).
  - In **Gemma E2B**, onset occurs at **layer 29**.
  - In **Gemma E4B**, sampled **layer 32** barely transferred UUID behavior.

---

## PART IV: SYSTEMS PAYOFF & PRODUCTION ARCHITECTURE

### Generalizing Beyond Citations: Typed Entity Resolution

Does canonicalization help outside citation formatting? In Stage 8, we evaluated synthetic account resolution across **800 model generations** with citations completely disabled. Prompts contained 15 or 20 customer records rendered in four conditions: raw PII, arbitrary random masking, untyped canonical handles, and typed handles (`<ACCOUNT_1>`, `<EMAIL_2>`).

![Figure 8 — Canonicalization eliminates raw-value exposure; accuracy effects vary by model: Panel A: Account-resolution accuracy (%) by model and representation; Panel B: Outputs containing raw PII (%) across 800 model generations.](assets/08_stage8_entities.svg)

> **Figure 8 — Typed entity canonicalization.** Each model resolved synthetic customer accounts from prompts containing the same records under four representations. “Raw” includes literal names, emails, and account numbers. “Random” replaces them with arbitrary masks. “Untyped” uses consistent but semantically neutral handles, while “typed” uses handles such as `<ACCOUNT_1>` and `<EMAIL_2>`. Typed handles improved Qwen by 17.5 percentage points relative to untyped handles and helped Tiny Aya relative to random masking. Gemma was near ceiling across conditions, while LFM performed poorly whenever values were masked. Separately, every masked representation reduced raw-value output exposure to zero in this dataset. Thus canonicalization reliably controlled literal exposure, but its task-accuracy effect depended on the model.

- **Qwen2.5-1.5B** achieved **97.5% task accuracy** with typed handles versus **80.0%** with untyped handles—a **+17.5 percentage-point gain at identical prompt lengths**.
- **Tiny Aya** gained **+15.0 percentage points** with typed handles over arbitrary masking (though typed vs. untyped remained parity at 97.5%).
- **Gemma E2B/E4B** were ceiling-limited (~95%+ across all conditions), while LFM suffered when masked (falling to 0–7.5%).
- **Exposure Reduction:** Masked conditions completely eliminated raw names, emails, and account numbers from outputs (0% vs. 85–100% in raw prompts).

Headline finding: *Typed handles can improve non-citation entity binding, but gains are architecture-dependent.*

---

### The Reference Architecture: Symbolic IR & Mapping Vault

The empirical findings culminate in Stage 9: a reference implementation of a **Request-Scoped Symbolic IR** boundary.

Instead of passing raw backend IDs to the model, trusted software interposes a canonicalizer and mapping vault:

```text
Trusted Application Context (DB UUIDs, PII, Tool IDs)
         │
         ▼
┌─────────────────────────────────┐
│  Request-Scoped Canonicalizer   │ ────► Protected Mapping Vault
└─────────────────────────────────┘       (Never enters model context)
         │
         ▼
Model-Facing Typed IR (<SOURCE_1>, <ACCOUNT_2>)
         │
         ▼
┌─────────────────────────────────┐
│       LLM JSON Generation       │
└─────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│   Deterministic IR Validator    │
└─────────────────────────────────┘
  ├── 1. Strict JSON Syntax
  ├── 2. Raw-Value Leakage Check
  ├── 3. Handle Syntax Check
  ├── 4. Request Registry Membership
  ├── 5. Type Consistency
  └── 6. Tool Argument Schema
         │
         ▼ (Accepted Only)
Deterministic Same-Request Rehydration
         │
         ▼
Application Authorization & Business Rules
```

![Figure 9 — A symbolic handle is a reference, not a capability: The request-scoped Symbolic IR boundary validates structural representation before rehydration; semantic correctness and authorization require independent application checks.](assets/09_trust_boundary.svg)

> **Figure 9 — Symbolic IR trust boundary.** The canonicalizer creates typed request-scoped handles and stores their literal values in a protected vault. The model receives only the symbolic representation. Its response is treated as untrusted: a deterministic validator checks the JSON shape, raw-value leakage, handle syntax, request membership, type consistency, and allowed action schema. Only an accepted response may be rehydrated. This boundary successfully accepted 500 valid round trips, rejected 5,000 malformed or unauthorized symbolic payloads, and blocked 499 cross-request replay attempts. However, all 500 deliberately wrong-but-registered handles passed structural validation. A valid handle proves only that the reference is well formed and belongs to the request; ownership, semantic correctness, freshness, and authorization still require separate checks.

### Production Implementation Pattern

Below is a runnable example using the tested reference implementation in this repository:

```python
from symbolic_ir.ir import (
    CanonicalizationPolicy,
    ValidationPolicy,
    canonicalize_request,
    rehydrate_response,
    validate_symbolic_output,
)

exchange = canonicalize_request(
    request_id="request-42",
    instruction="Return the account for Maya Chen.",
    state={"customer": {"name": "Maya Chen", "account": "ACCT-GB-4490-9812"}},
    policy=CanonicalizationPolicy({"account": "ACCOUNT"}),
)

# Send only exchange.model_ir.to_model_payload() to the model.
model_output = '{"answer":"<ACCOUNT_1>","references":[],"actions":[]}'
result = validate_symbolic_output(
    model_output,
    vault=exchange.vault,
    policy=ValidationPolicy(answer_types=("ACCOUNT",), reference_types=()),
)
if not result.accepted:
    raise ValueError(result.issues)

resolved = rehydrate_response(result, vault=exchange.vault)
assert resolved.answer == "ACCT-GB-4490-9812"
```

The library also validates strict response shape, leakage, request-local registry membership, handle types, and authorized tool arguments before rehydration.

### Operational Stress Test: 5,000 Adversarial Test Cases

To verify the deterministic boundary, we subjected the reference implementation to an adversarial regression suite of **500 synthetic requests** and **5,000 adversarial payloads** across 10 failure classes:
- **100% Structural Enforcement:** All 500 valid responses were accepted and rehydrated without loss. All 5,000 malformed, leaked, mistyped, unauthorized tool, and unregistered-handle outputs were rejected.
- **Cross-Request Isolation:** All 499 attempted cross-request handle replay attacks were blocked.
- **Payload Efficiency:** The canonical model view reduced serialized prompt characters by **52.26%**. Median validation overhead was **0.037 ms**. Stage 9 did not record tokenizer counts, so no token-reduction figure is claimed here.

### The Critical Semantic Limit

In 500 deliberately crafted test cases, we fed the validator a response containing a **well-formed handle registered to the current request, but pointing to the wrong account**.

**Every single one (500 / 500) passed structural validation and rehydrated to the wrong account.**

This is not a bug in the validator; it is a fundamental principle of software security:

```text
Malformed or unregistered handle  → deterministic validation can reject
Valid but semantically wrong handle → authorization, business rules, or review
```

A symbolic handle is a **reference**, not a capability token, permission proof, or guarantee of model correctness. Post-rehydration code must still check permissions, account ownership, and idempotency.

---

### The Practical Decision Matrix for ML Engineers

When should an engineering team implement Symbolic IR?

| Scenario | Recommendation | Why? |
|---|:---:|---|
| **RAG Retrieval Passages** | **Alias It** | Document UUIDs are arbitrary transport pointers. Aliasing saves 70–94% tokens and eliminates bracket-parsing failures. |
| **Tool / Agent Object IDs** | **Alias It** | Database keys, session tokens, and transaction IDs should never be emitted directly by the LLM. |
| **Privacy / PII Redaction** | **Alias It** | Scrub account numbers and emails before prompting; rehydrate locally after generation. |
| **Code Refactoring & Diffs** | **Keep Literal** | Variable names, function signatures, and line content carry syntax meaning. |
| **URL Path & Domain Analysis** | **Keep Literal** | Subdomains, query parameters, and paths contain semantic tokens needed for categorization. |
| **Quoted Legal / Source Text** | **Keep Literal** | Verbatim quotes require preserving exact surface morphology. |

> **Rule of Thumb:** If the string is a **pointer or address**, alias it to a request-scoped handle. If the string is the **payload or subject of analysis**, keep it raw.

---

## Limitations & Open Questions

1. **Model Parameter Scale:** Our behavioral and mechanistic tests ran on local models between 1.2B and 4B parameters. While the transport cost (tokens, latency, KV-cache) applies equally to 70B+ and proprietary models (GPT-4o, Claude 3.5 Sonnet), frontier models possess much higher attention capacity and may exhibit higher baseline UUID binding fidelity. Testing the held-out MuSiQue cohort on frontier APIs remains an open research priority.
2. **Context Length Regimes:** The measured input prompts ranged from roughly 230 to 4,000 tokens, using 4K–8K context windows. In 100K+ contexts, identifier token bloat can accumulate into substantial KV-cache use, but attention dilution at that scale requires dedicated measurement.
3. **State Management in Distributed Systems:** Maintaining a `MappingVault` requires request-scoped state. In serverless or distributed streaming agent loops, vaults must be tied to ephemeral cache stores (e.g., Redis with short TTLs) and managed across conversational turns.

---

## Summary & Conclusion

Placing machine-generated UUIDs into LLM prompts is an antipattern born of convenience. Autoregressive models pay a heavy penalty in token consumption, generation latency, and citation binding recall when forced to juggle high-entropy strings.

By introducing a clean, deterministic **Symbolic IR** boundary—canonicalizing transport keys into compact typed handles and keeping the mapping vault in trusted software—engineering teams can cut prompt tokens by up to 50%, eliminate literal PII exposure, and establish a verifiable trust boundary between probabilistic models and production applications.

---

### Reproducibility & Artifacts

Empirical Figures 3–8 are generated from checked-in processed result artifacts; Figures 1, 2, and 9 are deterministic code-generated schematics. Local raw logs are hash-recorded for provenance but are not tracked in Git.
- **Figure Generator:** [`blog/scripts/build_figures.py`](scripts/build_figures.py)
- **Technical Appendix & Evidence Ledger:** [`blog/appendix.md`](appendix.md)
- **Machine-Readable Evidence Manifest:** [`blog/evidence_manifest.csv`](evidence_manifest.csv)
- **Test Suite:** Run `.venv/bin/python scripts/run_tests.py` to verify the deterministic test suite.
