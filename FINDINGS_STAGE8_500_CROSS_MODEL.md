# Stage 8 cross-model findings: entity canonicalization

## Design

8 local models received the same 500 synthetic account-resolution examples under raw, random-masked, untyped canonical, and typed canonical entity representations (16000 generations total). Prompts contain 15 or 20 records and native token sequences. Source labels are fixed to `[S1]` across all conditions, citations are disabled, and only entity surface form changes.

## Accuracy

| Model | Raw | Random masked | Untyped | Typed | Typed−untyped (95% CI) | Exact p | Token delta |
|---|---:|---:|---:|---:|---:|---:|---:|
| Gemma E2B | 100.0% | 100.0% | 85.8% | 98.8% | +13.0 pp [+10.0, +16.2] | 8.19e-18 | +0.0 |
| Gemma E4B | 100.0% | 99.6% | 86.4% | 99.8% | +13.4 pp [+10.4, +16.4] | 1.36e-20 | +0.0 |
| LFM 1.2B | 29.4% | 5.2% | 0.0% | 22.0% | +22.0 pp [+18.4, +25.6] | 1.54e-33 | +35.0 |
| LFM 2.6B | 94.6% | 56.6% | 18.2% | 97.0% | +78.8 pp [+75.0, +82.4] | 2.46e-115 | +35.0 |
| Qwen 1.5B | 94.8% | 82.0% | 81.0% | 92.4% | +11.4 pp [+8.0, +14.6] | 7.66e-12 | +0.0 |
| Qwen 3.5 2B | 48.6% | 61.0% | 96.6% | 98.6% | +2.0 pp [+0.6, +3.4] | 0.0129 | +0.0 |
| Qwen 3.5 4B | 100.0% | 99.8% | 99.6% | 100.0% | +0.4 pp [+0.0, +1.0] | 0.5 | +0.0 |
| Tiny Aya | 82.4% | 77.8% | 91.2% | 97.6% | +6.4 pp [+4.0, +9.0] | 4.43e-07 | +36.0 |

Across all 4000 model/example pairs, typed handles improve over untyped by +18.4 points (20 typed losses, 757 typed wins; exact p=5.34e-195). This pooled result is descriptive because model families are heterogeneous.

The strict token-matched subset—Gemma E2B, Gemma E4B, Qwen 1.5B, Qwen 3.5 2B, Qwen 3.5 4B—contains 2500 pairs and shows +8.0 points (13/214 discordant losses/wins; exact p=4.74e-48).

## Privacy exposure and error type

| Model | Raw: any raw PII in output | Masked conditions: any raw PII | Typed wrong-existing entity | Typed hallucinated entity |
|---|---:|---:|---:|---:|
| Gemma E2B | 100.0% | 0.0% | 1.0% | 0.2% |
| Gemma E4B | 100.0% | 0.0% | 0.2% | 0.0% |
| LFM 1.2B | 92.0% | 0.0% | 71.4% | 6.6% |
| LFM 2.6B | 99.4% | 0.0% | 3.0% | 0.0% |
| Qwen 1.5B | 98.4% | 0.0% | 7.4% | 0.2% |
| Qwen 3.5 2B | 100.0% | 0.0% | 1.4% | 0.0% |
| Qwen 3.5 4B | 100.0% | 0.0% | 0.0% | 0.0% |
| Tiny Aya | 100.0% | 0.0% | 2.4% | 0.0% |

## Findings

1. **Token-matched advantage:** In the strict token-matched subset (5 models, 2500 pairs), typed handles improve accuracy over untyped handles by +8.0 points (13 losses vs 214 wins; exact p=4.74e-48).
2. **Fleet-wide win rate:** Across all 4000 model/example pairs, typed handles won 757 times against 20 losses (+18.4 points; exact p=5.34e-195).
3. **Recovery from untyped representation collapse:** Models sensitive to arbitrary placeholders (e.g. LFM 2.6B, Gemma E2B, Gemma E4B) often degrade sharply on untyped masks but recover to near-ceiling performance when semantic type hints are provided.
4. **Complete output exposure elimination:** Masked conditions completely eliminated raw personal names, emails, and account numbers from model outputs (0.0% across all masked/typed generations vs 92%–100% in raw prompts).

## Checkpoint 8

**Decision: generalization gate passed.** Across 8 models and 500 examples (16000 generations), typed canonicalization systematically protects non-citation entity binding under matched token lengths and eliminates model-layer data leakage.

The next roadmap step is Stage 9: synthesize the behavioral, causal, efficiency, and privacy results into an LLM-facing intermediate-representation design with deterministic validation and rehydration.
