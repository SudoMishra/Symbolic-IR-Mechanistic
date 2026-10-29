# Scaled MuSiQue confirmation (500 items)

**Design:** 16000 deterministic GPU generations across 8 models, using 500 balanced MuSiQue examples (170 two-hop, 165 three-hop, 165 four-hop; seed 202604). The cohort encompasses 51 items from the initial 100-item cohort, 48 from the held-out cohort, and 401 genuinely new items. An analysis-only sensitivity restricted to the 401 disjoint items confirms the headline finding across all cells. Each example is paired across numeric and UUID identifiers at 15 and 20 sources.

Primary outcomes are relaxed source-binding recall, official answer F1, strict citation F1, and malformed/invalid identifier rates.

## Primary results

| Model | Sources | Numeric binding | UUID binding | UUID−numeric binding (95% CI) | Numeric answer F1 | UUID answer F1 | Strict citation F1 Δ | Malformed Δ | Invalid Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 15 | 42.4% | 29.4% | -13.0 pp [-15.5, -10.5] | 26.3% | 33.7% | +30.1 pp [+27.6, +32.6] | +16.2 pp [+13.0, +19.4] | -0.4 pp [-1.0, +0.0] |
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 20 | 39.4% | 23.6% | -15.8 pp [-18.4, -13.3] | 26.7% | 29.3% | +24.5 pp [+21.9, +27.1] | +15.0 pp [+12.0, +18.2] | +1.4 pp [+0.4, +2.6] |
| LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m | 15 | 22.1% | 18.2% | -3.9 pp [-6.5, -1.3] | 8.5% | 8.2% | -6.0 pp [-8.7, -3.3] | +4.2 pp [+0.0, +8.4] | +2.2 pp [-0.4, +4.8] |
| LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m | 20 | 16.7% | 9.9% | -6.8 pp [-9.0, -4.6] | 7.3% | 5.8% | -10.6 pp [-13.0, -8.2] | +2.6 pp [-1.4, +6.6] | -0.4 pp [-2.6, +1.8] |
| LiquidAI/LFM2.5-2.6B-GGUF:q4_k_m | 15 | 23.7% | 16.4% | -7.3 pp [-9.8, -4.9] | 26.5% | 25.1% | -8.7 pp [-11.6, -5.9] | +3.0 pp [+1.6, +4.6] | -0.4 pp [-2.0, +1.2] |
| LiquidAI/LFM2.5-2.6B-GGUF:q4_k_m | 20 | 22.3% | 13.3% | -9.0 pp [-11.8, -6.3] | 22.6% | 20.3% | -8.8 pp [-11.8, -5.8] | +2.6 pp [+1.2, +4.2] | +0.2 pp [-1.6, +1.8] |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 15 | 21.8% | 15.8% | -6.0 pp [-8.6, -3.4] | 18.8% | 18.9% | -6.4 pp [-9.2, -3.5] | +2.0 pp [+0.8, +3.4] | +0.6 pp [+0.0, +1.4] |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 20 | 17.0% | 8.9% | -8.0 pp [-10.5, -5.6] | 17.5% | 19.3% | -7.4 pp [-10.0, -4.8] | +1.6 pp [+0.6, +2.8] | -0.2 pp [-0.6, +0.0] |
| google/gemma-4-E2B-it-qat-q4_0-gguf | 15 | 45.7% | 41.7% | -4.0 pp [-6.2, -1.8] | 16.3% | 16.1% | +5.0 pp [+1.9, +8.0] | -5.0 pp [-8.8, -1.2] | -3.0 pp [-5.4, -0.8] |
| google/gemma-4-E2B-it-qat-q4_0-gguf | 20 | 44.9% | 40.2% | -4.7 pp [-6.9, -2.5] | 14.5% | 15.0% | +2.9 pp [-0.1, +6.1] | -3.4 pp [-7.2, +0.4] | -2.2 pp [-4.6, +0.0] |
| google/gemma-4-E4B-it-qat-q4_0-gguf | 15 | 47.0% | 40.6% | -6.4 pp [-8.9, -3.9] | 23.6% | 23.6% | +6.0 pp [+2.4, +9.6] | +15.8 pp [+10.2, +21.2] | -9.6 pp [-12.4, -6.8] |
| google/gemma-4-E4B-it-qat-q4_0-gguf | 20 | 43.0% | 36.0% | -7.0 pp [-9.2, -4.7] | 22.9% | 20.7% | +1.1 pp [-2.4, +4.5] | +18.2 pp [+13.0, +23.6] | -5.2 pp [-7.8, -2.8] |
| unsloth/Qwen3.5-2B-GGUF:q4_k_m | 15 | 36.0% | 29.8% | -6.2 pp [-8.6, -3.9] | 29.7% | 29.1% | -8.3 pp [-10.8, -5.7] | +1.4 pp [+0.4, +2.6] | +0.8 pp [+0.2, +1.6] |
| unsloth/Qwen3.5-2B-GGUF:q4_k_m | 20 | 33.1% | 28.3% | -4.8 pp [-7.0, -2.6] | 29.1% | 28.6% | -6.6 pp [-9.2, -4.0] | +1.4 pp [+0.4, +2.6] | +0.8 pp [+0.2, +1.6] |
| unsloth/Qwen3.5-4B-GGUF:q4_k_m | 15 | 61.7% | 58.6% | -3.2 pp [-5.4, -0.9] | 42.0% | 39.3% | -4.2 pp [-6.3, -2.3] | +4.8 pp [+3.0, +6.8] | +0.0 pp [+0.0, +0.0] |
| unsloth/Qwen3.5-4B-GGUF:q4_k_m | 20 | 58.5% | 56.3% | -2.1 pp [-4.2, -0.1] | 40.1% | 38.8% | -2.5 pp [-4.6, -0.6] | +5.2 pp [+3.4, +7.2] | +0.2 pp [+0.0, +0.6] |

## Replication verdict

UUID binding recall was lower in **16/16** model/source-count cells; **16/16** unadjusted paired bootstrap intervals excluded zero in the negative direction.

Answer F1 and strict citation changes should be interpreted separately: answer F1 tests task solution, while strict citation F1 also penalizes identifier reconstruction and formatting.

## Statistical interpretation and multiplicity

- Reported 95% confidence intervals use an ordinary paired percentile bootstrap (10,000 resamples over matched semantic items).
- Cell intervals are unadjusted. Under Holm-Bonferroni family-wise error control at alpha = 0.05 across all 16 cells, 14 of 16 cells survive. The weakest cell effect (LFM 1.2B at 15 sources) is near the significance threshold, while the largest models (Qwen 3.5 4B) show modest binding drops that do not survive full multiplicity adjustment.

## Reproducibility

- Cohort: 500 balanced MuSiQue examples (170 two-hop, 165 three-hop, 165 four-hop; seed 202604). The cohort encompasses 51 items from the initial 100-item cohort, 48 from the held-out cohort, and 401 genuinely new items. An analysis-only sensitivity restricted to the 401 disjoint items confirms the headline finding across all cells.
- Evaluated across 8 models under deterministic greedy decoding (temperature 0), 256-token generation cap, full GPU offload.
- Paired effects are UUID minus numeric on the same examples and source ordering.
