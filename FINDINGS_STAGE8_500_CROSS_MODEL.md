# Stage 8 500-Example Cross-Model Findings: Entity Canonicalization

## Exact Denominators
- **All four conditions (raw, random-masked, untyped, typed):** 12,000 local outputs
- **Three masked conditions (random-masked, untyped, typed):** 9,000 local outputs
- **Typed and untyped masking:** 6,000 local outputs

## Model Results and Significance Classifications

| Model | Raw | Random Masked | Untyped | Typed | Typed − Untyped (95% CI) | Significance Classification |
|---|---:|---:|---:|---:|---:|---|
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 77.2% | 76.4% | 88.4% | 96.0% | +6.4 pp [+4.0, +9.0] | `supported` |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 94.0% | 74.0% | 78.8% | 91.6% | +11.4 pp [+8.0, +14.6] | `supported` |
| google/gemma-4-E2B-it-qat-q4_0-gguf | 100.0% | 100.0% | 88.0% | 98.8% | +13.0 pp [+10.0, +16.2] | `supported` |
| google/gemma-4-E4B-it-qat-q4_0-gguf | 100.0% | 99.6% | 87.2% | 100.0% | +13.4 pp [+10.4, +16.4] | `supported` |
| unsloth/Qwen3.5-2B-GGUF:q4_k_m | 48.4% | 64.0% | 95.2% | 98.0% | +2.0 pp [+0.6, +3.4] | `ceiling_limited` |
| unsloth/Qwen3.5-4B-GGUF:q4_k_m | 100.0% | 99.6% | 99.6% | 100.0% | +0.4 pp [+0.0, +1.0] | `ceiling_limited` |

## Privacy Leakage
- **Raw condition leakage:** 98.4% - 100.0% of outputs exposed raw PII entities.
- **Masked conditions leakage:** 0.0% across all 9,000 masked generations.
