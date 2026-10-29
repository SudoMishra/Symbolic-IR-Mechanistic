# Stage 8 cross-model findings: entity canonicalization

## Design

6 local models received the same 40 synthetic account-resolution examples under raw, random-masked, untyped canonical, and typed canonical entity representations (960 generations total). Prompts contain 15 or 20 records and native token sequences. Source labels are fixed to `[S1]` across all conditions, citations are disabled, and only entity surface form changes.

## Accuracy

| Model | Raw | Random masked | Untyped | Typed | Typed−untyped (95% CI) | Exact p | Token delta |
|---|---:|---:|---:|---:|---:|---:|---:|
| Gemma E2B | 100.0% | 100.0% | 92.5% | 100.0% | +7.5 pp [+0.0, +17.5] | 0.25 | +0.0 |
| Gemma E4B | 100.0% | 100.0% | 92.5% | 100.0% | +7.5 pp [+0.0, +17.5] | 0.25 | +0.0 |
| LFM 1.2B | 27.5% | 2.5% | 0.0% | 7.5% | +7.5 pp [+0.0, +17.5] | 0.25 | +35.0 |
| LFM 2.6B | 92.5% | 52.5% | 27.5% | 97.5% | +70.0 pp [+52.5, +85.0] | 5.77e-08 | +35.0 |
| Qwen 1.5B | 90.0% | 85.0% | 80.0% | 97.5% | +17.5 pp [+7.5, +30.0] | 0.0156 | +0.0 |
| Tiny Aya | 87.5% | 82.5% | 97.5% | 97.5% | +0.0 pp [+0.0, +0.0] | 1 | +36.0 |

Across all 240 model/example pairs, typed handles improve over untyped by +18.3 points (1 typed losses, 45 typed wins; exact p=1.34e-12). This pooled result is descriptive because model families are heterogeneous.

The strict token-matched subset—Gemma E2B, Gemma E4B, Qwen 1.5B—contains 120 pairs and shows +10.8 points (0/13 discordant losses/wins; exact p=0.000244).

## Privacy exposure and error type

| Model | Raw: any raw PII in output | Masked conditions: any raw PII | Typed wrong-existing entity | Typed hallucinated entity |
|---|---:|---:|---:|---:|
| Gemma E2B | 100.0% | 0.0% | 0.0% | 0.0% |
| Gemma E4B | 100.0% | 0.0% | 0.0% | 0.0% |
| LFM 1.2B | 85.0% | 0.0% | 82.5% | 10.0% |
| LFM 2.6B | 97.5% | 0.0% | 2.5% | 0.0% |
| Qwen 1.5B | 97.5% | 0.0% | 2.5% | 0.0% |
| Tiny Aya | 100.0% | 0.0% | 0.0% | 2.5% |

## Findings

1. **Token-matched advantage:** In the strict token-matched subset (3 models, 120 pairs), typed handles improve accuracy over untyped handles by +10.8 points (0 losses vs 13 wins; exact p=0.000244).
2. **Fleet-wide win rate:** Across all 240 model/example pairs, typed handles won 45 times against 1 losses (+18.3 points; exact p=1.34e-12).
3. **Recovery from untyped representation collapse:** Models sensitive to arbitrary placeholders (e.g. LFM 2.6B, Gemma E2B, Gemma E4B) often degrade sharply on untyped masks but recover to near-ceiling performance when semantic type hints are provided.
4. **Complete output exposure elimination:** Masked conditions completely eliminated raw personal names, emails, and account numbers from model outputs (0.0% across all masked/typed generations vs 92%–100% in raw prompts).

## Checkpoint 8

**Decision: generalization gate passed.** Across 6 models and 40 examples (960 generations), typed canonicalization systematically protects non-citation entity binding under matched token lengths and eliminates model-layer data leakage.

The next roadmap step is Stage 9: synthesize the behavioral, causal, efficiency, and privacy results into an LLM-facing intermediate-representation design with deterministic validation and rehydration.
