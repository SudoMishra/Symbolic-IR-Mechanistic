# Held-out MuSiQue confirmatory replication

**Design:** 2400 deterministic GPU generations across 6 models, using 100 MuSiQue dev examples disjoint from the original 100-example cohort. Each example is paired across numeric and UUID identifiers at 15 and 20 sources.

Primary outcomes are relaxed source-binding recall, official answer F1, strict citation F1, and malformed/invalid identifier rates.

## Primary results

| Model | Sources | Numeric binding | UUID binding | UUID−numeric binding (95% CI) | Numeric answer F1 | UUID answer F1 | Strict citation F1 Δ | Malformed Δ | Invalid Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 15 | 40.4% | 29.0% | -11.4 pp [-17.1, -6.1] | 30.2% | 34.8% | +26.5 pp [+20.9, +32.2] | +26.0 pp [+18.0, +35.0] | +3.0 pp [+0.0, +7.0] |
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 20 | 37.5% | 22.8% | -14.8 pp [-20.2, -9.7] | 24.8% | 25.6% | +22.0 pp [+16.9, +27.1] | +13.0 pp [+7.0, +20.0] | +0.0 pp [-3.0, +3.0] |
| LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m | 15 | 21.3% | 13.8% | -7.5 pp [-13.4, -1.6] | 7.5% | 7.0% | -10.7 pp [-16.7, -4.8] | +14.0 pp [+6.0, +22.0] | +1.0 pp [-2.0, +5.0] |
| LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m | 20 | 17.5% | 11.4% | -6.1 pp [-12.1, -0.5] | 5.9% | 5.7% | -8.2 pp [-13.2, -3.0] | +15.0 pp [+8.0, +23.0] | +6.0 pp [+1.0, +12.0] |
| LiquidAI/LFM2.5-2.6B-GGUF:q4_k_m | 15 | 24.2% | 13.8% | -10.4 pp [-16.3, -4.5] | 22.9% | 15.4% | -13.1 pp [-20.1, -6.1] | +2.0 pp [+0.0, +5.0] | +1.0 pp [+0.0, +3.0] |
| LiquidAI/LFM2.5-2.6B-GGUF:q4_k_m | 20 | 19.8% | 15.2% | -4.7 pp [-10.2, +0.8] | 17.4% | 17.3% | -4.0 pp [-10.2, +2.0] | +3.0 pp [-1.0, +7.0] | +1.0 pp [+0.0, +3.0] |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 15 | 18.8% | 12.0% | -6.8 pp [-12.3, -1.2] | 17.4% | 17.0% | -10.4 pp [-16.5, -4.1] | +3.0 pp [+0.0, +7.0] | +0.0 pp [+0.0, +0.0] |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 20 | 9.7% | 8.8% | -0.8 pp [-5.1, +3.2] | 15.1% | 17.1% | -1.5 pp [-6.6, +3.6] | +1.0 pp [+0.0, +3.0] | +0.0 pp [+0.0, +0.0] |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 15 | 39.1% | 36.0% | -3.1 pp [-8.3, +2.4] | 13.8% | 14.5% | -1.0 pp [-7.5, +5.5] | +1.0 pp [-8.0, +9.0] | +1.0 pp [-3.0, +5.0] |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 20 | 38.5% | 33.7% | -4.8 pp [-10.1, +0.1] | 9.5% | 13.1% | +5.7 pp [-0.7, +12.2] | -9.0 pp [-18.0, -1.0] | -6.0 pp [-11.0, -2.0] |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | 15 | 45.0% | 39.2% | -5.8 pp [-10.9, -0.9] | 21.3% | 21.5% | +3.1 pp [-5.2, +11.5] | +16.0 pp [+4.0, +28.0] | -9.0 pp [-15.0, -3.0] |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | 20 | 42.2% | 38.8% | -3.4 pp [-9.1, +2.3] | 20.3% | 22.8% | +1.7 pp [-6.8, +10.4] | +21.0 pp [+10.0, +32.0] | -12.0 pp [-19.0, -5.0] |

## Replication verdict

UUID binding recall was lower in **12/12** model/source-count cells; **7/12** paired bootstrap intervals excluded zero in the negative direction.

Answer F1 and strict citation changes should be interpreted separately: answer F1 tests task solution, while strict citation F1 also penalizes identifier reconstruction and formatting.

## Reproducibility

- Cohort seed: 202603; 34 two-hop, 33 three-hop, and 33 four-hop questions.
- Prompts were jointly screened with all five native GGUF tokenizers and kept within 2,000–3,700 tokens.
- Temperature 0, 256-token generation cap, full CUDA offload, Q4 quantization.
- Paired effects are UUID minus numeric on the same examples and source ordering; intervals use 10,000 bootstrap samples.
