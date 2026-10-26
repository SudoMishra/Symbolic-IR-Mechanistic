# Stage 8 cross-model findings: entity canonicalization

## Design

Five local models received the same 40 synthetic account-resolution examples under raw, random-masked, untyped canonical, and typed canonical entity representations (800 generations total). Prompts contain 15 or 20 records and approximately 2.2K–3.5K native tokens. Source labels are fixed to `[S1]` across all conditions, citations are disabled, and only entity surface form changes.

## Accuracy

| Model | Raw | Random masked | Untyped | Typed | Typed−untyped (95% CI) | Exact p | Token delta |
|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen 1.5B | 90.0% | 85.0% | 80.0% | 97.5% | +17.5 pp [+7.5, +30.0] | 0.0156 | +0.0 |
| LFM 1.2B | 27.5% | 2.5% | 0.0% | 7.5% | +7.5 pp [+0.0, +17.5] | 0.25 | +35.0 |
| Gemma E2B | 100.0% | 100.0% | 92.5% | 100.0% | +7.5 pp [+0.0, +17.5] | 0.25 | +0.0 |
| Gemma E4B | 100.0% | 100.0% | 92.5% | 100.0% | +7.5 pp [+0.0, +17.5] | 0.25 | +0.0 |
| Tiny Aya | 87.5% | 82.5% | 97.5% | 97.5% | +0.0 pp [+0.0, +0.0] | 1 | +36.0 |

Across all 200 model/example pairs, typed handles improve over untyped by +8.0 points (0 typed losses, 16 typed wins; exact p=3.05e-05). This pooled result is descriptive because model families are heterogeneous.

The strict token-matched subset—Qwen 1.5B, Gemma E2B, Gemma E4B—contains 120 pairs and shows +10.8 points (0/13 discordant losses/wins; exact p=0.000244).

## Privacy exposure and error type

| Model | Raw: any raw PII in output | Masked conditions: any raw PII | Typed wrong-existing entity | Typed hallucinated entity |
|---|---:|---:|---:|---:|
| Qwen 1.5B | 97.5% | 0.0% | 2.5% | 0.0% |
| LFM 1.2B | 85.0% | 0.0% | 82.5% | 10.0% |
| Gemma E2B | 100.0% | 0.0% | 0.0% | 0.0% |
| Gemma E4B | 100.0% | 0.0% | 0.0% | 0.0% |
| Tiny Aya | 100.0% | 0.0% | 0.0% | 2.5% |

## Findings

1. **Checkpoint 8 is passed, but not universally.** Qwen shows a significant +17.5-point typed-over-untyped gain with exactly matched input length. This is the requested non-citation generalization of canonical symbolic structure.
2. **Typed structure also beats arbitrary masking on Tiny Aya.** The gain is +15.0 points (exact p=0.0312) with -1.6 input tokens, a near-length-matched comparison.
3. **Capability and calibration matter.** Both Gemma models are at ceiling for raw, random-masked, and typed conditions, leaving only three untyped errors. LFM is near floor after masking and therefore does not provide a reliable positive accuracy comparison.
4. **Typed handles reduce binding mistakes rather than formatting alone.** Qwen's typed wins are all paired corrections with no paired regressions; the evaluator normalizes optional angle brackets before scoring.
5. **Masking eliminates raw-value exposure in this controlled setup.** No masked output contains any of the synthetic raw names, emails, or account numbers. This occurs because raw values are removed before model inference; it is exposure reduction, not a complete privacy guarantee.

## Checkpoint 8

**Decision: generalization gate passed.** Typed canonicalization improves a non-citation entity-binding task under an exact token-count control on Qwen and a near-token-matched arbitrary-alias control on Tiny Aya. The effect is architecture-dependent rather than universal.

The next roadmap step is Stage 9: synthesize the behavioral, causal, efficiency, and privacy results into an LLM-facing intermediate-representation design with deterministic validation and rehydration.
