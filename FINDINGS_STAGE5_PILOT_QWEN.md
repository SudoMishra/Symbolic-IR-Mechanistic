# Stage 5: explicit reasoning-budget findings

**Design:** 480 two-pass generations across 1 model(s). The first pass receives the 2k–4k-token source prompt and a hard scratchpad cap; the second pass receives only that scratchpad and a fixed 128-token final-answer cap.

This manipulates visible scratchpad/output capacity. It is not a measurement of proprietary hidden reasoning tokens.

## Aggregate accuracy and token use

| Model | Budget | Numeric acc. | Compact acc. | UUID acc. | UUID no-reproduction acc. | Numeric reasoning tok. | UUID reasoning tok. | UUID cap-hit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 64 | 0.0% | 12.5% | 0.0% | 0.0% | 49.0 | 40.8 | 58.3% |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 128 | 41.7% | 41.7% | 20.8% | 20.8% | 100.0 | 73.9 | 41.7% |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 256 | 50.0% | 50.0% | 33.3% | 16.7% | 146.2 | 115.0 | 12.5% |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 512 | 54.2% | 45.8% | 45.8% | 20.8% | 237.0 | 186.5 | 16.7% |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 1024 | 45.8% | 58.3% | 33.3% | 25.0% | 271.8 | 229.5 | 12.5% |

## Calibration by task

| Model | Task | Accuracy across all arms/budgets |
|---|---|---:|
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | reasoning_arithmetic | 10.0% |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | reasoning_constraint | 23.3% |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | reasoning_entity_resolution | 54.2% |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | reasoning_temporal | 35.8% |

## Interpretation

The machine-readable result contains paired bootstrap intervals for UUID versus numeric and for UUID citation reproduction versus no reproduction at every source-count/budget cell.
Tasks or cells outside the target 30–70% accuracy band should be recalibrated before the full model matrix.
