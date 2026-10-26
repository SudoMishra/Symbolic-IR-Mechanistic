# Stage 5: explicit reasoning-budget findings

**Design:** 1440 two-pass generations across 3 model(s). The first pass receives the 2k–4k-token source prompt and a hard scratchpad cap; the second pass receives only that scratchpad and a fixed 128-token final-answer cap.

This manipulates visible scratchpad/output capacity. It is not a measurement of proprietary hidden reasoning tokens.

## Aggregate accuracy and token use

| Model | Budget | Numeric acc. | Compact acc. | UUID acc. | UUID no-reproduction acc. | Numeric reasoning tok. | UUID reasoning tok. | UUID cap-hit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
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
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | 64 | 66.7% | 33.3% | 12.5% | 4.2% | 59.0 | 64.0 | 100.0% |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | 128 | 75.0% | 75.0% | 37.5% | 50.0% | 93.6 | 128.0 | 100.0% |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | 256 | 83.3% | 75.0% | 75.0% | 79.2% | 126.2 | 232.2 | 62.5% |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | 512 | 75.0% | 83.3% | 75.0% | 87.5% | 130.9 | 284.2 | 4.2% |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | 1024 | 75.0% | 79.2% | 75.0% | 75.0% | 139.1 | 312.7 | 0.0% |

## Calibration by task

| Model | Task | Accuracy across all arms/budgets |
|---|---|---:|
| LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m | reasoning_arithmetic | 0.0% |
| LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m | reasoning_constraint | 11.7% |
| LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m | reasoning_entity_resolution | 12.5% |
| LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m | reasoning_temporal | 0.8% |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | reasoning_arithmetic | 10.0% |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | reasoning_constraint | 23.3% |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | reasoning_entity_resolution | 54.2% |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | reasoning_temporal | 35.8% |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | reasoning_arithmetic | 7.5% |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | reasoning_constraint | 83.3% |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | reasoning_entity_resolution | 90.0% |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | reasoning_temporal | 77.5% |

## Interpretation

The machine-readable result contains paired bootstrap intervals for UUID versus numeric and for UUID citation reproduction versus no reproduction at every source-count/budget cell.
Tasks or cells outside the target 30–70% accuracy band should be recalibrated before the full model matrix.
