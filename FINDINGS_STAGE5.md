# Stage 5: explicit reasoning-budget findings

**Design:** 2400 two-pass generations across 5 model(s). The first pass receives the 2k–4k-token source prompt and a hard scratchpad cap; the second pass receives only that scratchpad and a fixed 128-token final-answer cap.

This manipulates visible scratchpad/output capacity. It is not a measurement of proprietary hidden reasoning tokens.

## Aggregate accuracy and token use

| Model | Budget | Numeric acc. | Compact acc. | UUID acc. | UUID no-reproduction acc. | Numeric reasoning tok. | UUID reasoning tok. | UUID cap-hit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 64 | 16.7% | 16.7% | 8.3% | 4.2% | 59.8 | 61.6 | 91.7% |
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 128 | 45.8% | 25.0% | 12.5% | 16.7% | 108.7 | 110.0 | 70.8% |
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 256 | 50.0% | 16.7% | 25.0% | 37.5% | 158.8 | 173.7 | 25.0% |
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 512 | 50.0% | 25.0% | 33.3% | 41.7% | 159.7 | 218.2 | 12.5% |
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 1024 | 50.0% | 29.2% | 37.5% | 33.3% | 146.6 | 310.8 | 12.5% |
| LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m | 64 | 8.3% | 4.2% | 0.0% | 20.8% | 49.2 | 54.8 | 54.2% |
| LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m | 128 | 4.2% | 4.2% | 0.0% | 16.7% | 69.7 | 80.3 | 20.8% |
| LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m | 256 | 4.2% | 0.0% | 0.0% | 16.7% | 91.8 | 88.5 | 8.3% |
| LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m | 512 | 4.2% | 4.2% | 0.0% | 20.8% | 105.6 | 121.9 | 4.2% |
| LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m | 1024 | 8.3% | 0.0% | 0.0% | 8.3% | 135.0 | 103.4 | 0.0% |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 64 | 0.0% | 12.5% | 0.0% | 0.0% | 49.0 | 40.8 | 58.3% |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 128 | 41.7% | 41.7% | 20.8% | 20.8% | 100.0 | 73.9 | 41.7% |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 256 | 50.0% | 50.0% | 33.3% | 16.7% | 146.2 | 115.0 | 12.5% |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 512 | 54.2% | 45.8% | 45.8% | 20.8% | 237.0 | 186.5 | 16.7% |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 1024 | 45.8% | 58.3% | 33.3% | 25.0% | 271.8 | 229.5 | 12.5% |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 64 | 37.5% | 25.0% | 12.5% | 4.2% | 59.4 | 64.0 | 100.0% |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 128 | 50.0% | 29.2% | 37.5% | 29.2% | 109.0 | 128.0 | 100.0% |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 256 | 58.3% | 58.3% | 70.8% | 45.8% | 144.8 | 236.0 | 70.8% |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 512 | 79.2% | 70.8% | 62.5% | 79.2% | 189.8 | 364.7 | 37.5% |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 1024 | 70.8% | 75.0% | 66.7% | 95.8% | 252.1 | 476.7 | 8.3% |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | 64 | 66.7% | 33.3% | 12.5% | 4.2% | 59.0 | 64.0 | 100.0% |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | 128 | 75.0% | 75.0% | 37.5% | 50.0% | 93.6 | 128.0 | 100.0% |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | 256 | 83.3% | 75.0% | 75.0% | 79.2% | 126.2 | 232.2 | 62.5% |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | 512 | 75.0% | 83.3% | 75.0% | 87.5% | 130.9 | 284.2 | 4.2% |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | 1024 | 75.0% | 79.2% | 75.0% | 75.0% | 139.1 | 312.7 | 0.0% |

## Calibration by task

| Model | Task | Accuracy across all arms/budgets |
|---|---|---:|
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | reasoning_arithmetic | 1.7% |
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | reasoning_constraint | 20.0% |
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | reasoning_entity_resolution | 65.8% |
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | reasoning_temporal | 27.5% |
| LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m | reasoning_arithmetic | 0.0% |
| LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m | reasoning_constraint | 11.7% |
| LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m | reasoning_entity_resolution | 12.5% |
| LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m | reasoning_temporal | 0.8% |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | reasoning_arithmetic | 10.0% |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | reasoning_constraint | 23.3% |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | reasoning_entity_resolution | 54.2% |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | reasoning_temporal | 35.8% |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | reasoning_arithmetic | 25.0% |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | reasoning_constraint | 70.8% |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | reasoning_entity_resolution | 43.3% |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | reasoning_temporal | 72.5% |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | reasoning_arithmetic | 7.5% |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | reasoning_constraint | 83.3% |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | reasoning_entity_resolution | 90.0% |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | reasoning_temporal | 77.5% |

## Interpretation

The machine-readable result contains paired bootstrap intervals for UUID versus numeric and for UUID citation reproduction versus no reproduction at every source-count/budget cell.
Tasks or cells outside the target 30–70% accuracy band should be recalibrated before the full model matrix.
