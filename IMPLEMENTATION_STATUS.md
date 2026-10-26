# Roadmap implementation status

This file distinguishes implemented tooling from completed empirical runs and work that remains.

## Implemented and verified

- Stage 0 infrastructure, including a 20-example end-to-end smoke run.
- Stage 1–5 datasets, controls, matrices, logging, evaluation, resumption, and analysis.
- Stage 6 paired surface-form experiment configuration and representation-similarity utilities.
- Stage 7 paired source-ID swaps, long-context residual-stream capture/patching,
  exact citation-sequence likelihoods, resumable manifests, and paired-bootstrap analysis.
- Stage 8 synthetic entity data, canonicalization conditions, binding evaluation, and leakage measurement.
- Stage 9 request-scoped typed IR, trusted-schema canonicalizer, strict symbolic
  output validator, redacted audit events, deterministic rehydrator, adversarial
  evaluation, and systems guidance.

## Completed real-model evidence

- Qwen2.5-1.5B: 400-generation Stage 1, 280-generation family pilot, and 100-generation numeric control.
- LiquidAI LFM2.5-1.2B: 400-generation Stage 1 and 100-generation numeric control.
- Gemma 4 E2B and E4B: 400-generation Stage 1 plus 100-generation numeric control for each version.
- Unified paired-bootstrap and exact-test analysis across 2,000 matched Stage-1/control generations. See `FINDINGS_CROSS_MODEL.md`.
- MuSiQue Stage 2–4 replication: 7,500 deterministic CUDA generations across Qwen2.5 1.5B, LFM2.5 1.2B, Gemma 4 E2B/E4B, and Tiny Aya Global. The shared 100-example cohort contains 34 two-hop, 33 three-hop, and 33 four-hop questions with 15/20 passages and 2,022–3,697 raw prompt tokens across native tokenizers. See `FINDINGS_MUSIQUE_STAGES_2_4.md`.
- Independent held-out MuSiQue confirmation: 2,000 deterministic CUDA generations on a disjoint balanced 100-example cohort. UUID relaxed binding recall was lower in all 10 model/source-count cells and significantly lower in six. See `FINDINGS_MUSIQUE_CONFIRMATORY.md`.
- Stage 5 explicit-budget study: 2,400 completed two-pass generations across Qwen2.5 1.5B, LFM2.5 1.2B, Gemma 4 E2B/E4B, and Tiny Aya Global. The visible scratchpad cap is varied over 64/128/256/512/1,024 tokens while the final decoder is fixed at 128 tokens. See `FINDINGS_STAGE5.md`.
- Independent Stage 5 confirmation: 3,200 additional deterministic CUDA two-pass generations on seed 202606, using 20 examples per retained task/source-count cell versus 3 in the pilot. The strict pilot-only 30–70% calibration rule retained Qwen temporal/entity-resolution, Gemma E2B entity-resolution, and Tiny Aya entity-resolution. All 160 semantic examples have complete four-arm × five-budget blocks. The broad monotonic UUID × budget interaction did not replicate, while model-specific Qwen UUID penalties, Gemma E2B's 64-token UUID failure, Gemma's high-budget no-reproduction recovery, and a robust total-output-token cost remained. See `FINDINGS_STAGE5_CONFIRMATORY.md`.
- Stage 6 cross-model hidden-state replication: 960 forward passes (80 semantic examples × three identifier formats × four models) through official BF16 Qwen2.5-1.5B-Instruct, LFM2.5-1.2B-Instruct, Gemma 4 E2B-it, and Gemma 4 E4B-it text checkpoints. Every model passed the representation gate: source-fact geometry stayed largely invariant, source-label relational geometry converged after different lexical embeddings, and citation states became format-specific late. UUID likelihood costs varied in sign and location, rejecting a universal literal-copying account. See `FINDINGS_STAGE6_CROSS_MODEL.md` and the model-specific Stage 6 reports.
- Stage 7 causal intervention study: 66 paired source-ID swaps and 1,056 residual-stream interventions across Qwen, LFM, Gemma E2B, and Gemma E4B. Qwen (n=8) and the smaller Gemma pilots (n=4/n=2) followed the semantic source to its new identifier; LFM (n=8) was causally sensitive but retained or strengthened the old association, with a significant compact-ID inversion. Final-layer citation-state patches transferred approximately 100% of each model's actual swap response, while the onset of transferable reconstruction differed sharply by architecture. See `FINDINGS_STAGE7_CROSS_MODEL.md` and the four model-specific Stage 7 reports.
- Stage 8 synthetic entity-canonicalization study: 800 deterministic CUDA generations across Qwen, LFM, Gemma E2B/E4B, and Tiny Aya (40 account-resolution examples × four entity representations × five models). Source identifiers were held fixed and citations disabled. Qwen showed a significant, exactly token-matched typed-over-untyped gain of 17.5 points; Tiny Aya showed a significant 15-point typed-over-random gain with near-matched length. The pooled typed-over-untyped gain was 8.0 points, but Gemma was ceiling-limited and LFM floor-limited, so the effect is not claimed as universal. See `FINDINGS_STAGE8_CROSS_MODEL.md`.

## Completed systems evidence

- Stage 9 operational boundary evaluation: 500 synthetic requests containing 10,000 records, 500 exact valid round trips, and 5,000 adversarial outputs. All configured raw values were absent from model payloads and audits; all ten invalid-output classes were rejected and refused rehydration; all 499 cross-request rehydration attempts were blocked. Canonical state used 52.26% fewer serialized characters. The intentionally wrong existing handle passed structural validation in all 500 cases, establishing the boundary between reference integrity and semantic correctness. See `FINDINGS_STAGE9.md`.

## Deliberately not claimed complete

- Component/head-level Stage 7 circuit localization and a larger independent Gemma replication.
- Broader Stage 8 task-family replication beyond synthetic account resolution.
- Integration with an external production identity, retrieval, database, or tool system; none was supplied.
- Production security certification, persistent encrypted vault storage, authorization enforcement, and real traffic evaluation.

## Required next gate

All roadmap stages and checkpoints are complete at their stated research scope. Stage 9 turns the empirical result into an executable reference boundary and explicitly demonstrates that deterministic validation catches representation-integrity failures but not a semantically wrong existing handle. The next research extensions are independent external-system validation, broader Stage 8 task families, and component-level patching in model-specific transition regions (Qwen 20–24, LFM 6–13, Gemma E2B 29–35, Gemma E4B 33–42) with a larger independent Gemma cohort. Tiny Aya remains unavailable for per-layer work because its official Transformers checkpoint is gated; the local GGUF cannot expose residual states.
