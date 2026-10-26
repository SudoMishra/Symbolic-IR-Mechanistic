# Stage 5 confirmatory reasoning-budget experiment

**Design:** independent seed 202606; 3200 completed two-pass generations; 160 complete semantic examples; 10,000-replicate stratified paired bootstrap.

Pilot information was used only to retain model–task pairs with aggregate answer accuracy in the predeclared 30–70% interval. All new examples differ from the pilot seed.

The budget is an explicit visible scratchpad cap, not a hidden chain-of-thought or proprietary reasoning-token budget.

## Retained cells and confirmatory calibration

| Model | Task | Examples | Confirmatory accuracy across arms/budgets |
|---|---|---:|---:|
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | reasoning_entity_resolution | 40 | 64.0% |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | reasoning_entity_resolution | 40 | 53.5% |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | reasoning_temporal | 40 | 44.0% |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | reasoning_entity_resolution | 40 | 46.1% |

## Pilot-to-confirmation comparison

The same interaction estimators are recomputed on only the pilot cells selected for confirmation. Effects are percentage points with stratified paired-bootstrap 95% intervals.

| Model | Pilot slope per doubling | Confirmatory slope per doubling | Pilot low-to-high | Confirmatory low-to-high |
|---|---:|---:|---:|---:|
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | +0.8 [-2.5, +5.8] | -1.6 [-4.5, +1.2] | +8.3 [-8.3, +25.0] | +0.0 [-10.0, +10.0] |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | -6.7 [-13.3, +1.7] | +5.2 [-1.0, +11.0] | -33.3 [-58.3, -8.3] | +7.5 [-12.5, +27.5] |
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | +10.0 [+3.3, +18.3] | -0.3 [-5.5, +4.8] | +41.7 [+16.7, +66.7] | +3.7 [-13.7, +20.0] |

## Accuracy by budget

Effects are percentage points with paired-bootstrap 95% intervals.

| Model | Budget | Numeric | Compact | UUID | UUID no reproduction | UUID − numeric (pp, 95% CI) | No reproduction − UUID (pp, 95% CI) |
|---|---:|---:|---:|---:|---:|---:|---:|
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 64 | 15.0% | 15.0% | 25.0% | 30.0% | +10.0 [-2.5, +25.0] | +5.0 [-7.5, +20.0] |
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 128 | 70.0% | 62.5% | 52.5% | 47.5% | -17.5 [-37.5, +5.0] | -5.0 [-25.0, +12.5] |
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 256 | 97.5% | 70.0% | 85.0% | 65.0% | -12.5 [-25.0, +0.0] | -20.0 [-32.5, -7.5] |
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 512 | 87.5% | 72.5% | 87.5% | 70.0% | +0.0 [-15.0, +12.5] | -17.5 [-32.5, -2.5] |
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 1024 | 90.0% | 72.5% | 90.0% | 75.0% | +0.0 [-12.5, +12.5] | -15.0 [-30.0, +0.0] |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 64 | 12.5% | 6.2% | 7.5% | 8.8% | -5.0 [-13.8, +3.8] | +1.2 [-6.2, +10.0] |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 128 | 65.0% | 61.3% | 45.0% | 41.2% | -20.0 [-33.8, -6.2] | -3.8 [-15.0, +7.5] |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 256 | 65.0% | 60.0% | 55.0% | 51.2% | -10.0 [-22.5, +2.5] | -3.8 [-15.0, +7.5] |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 512 | 61.3% | 68.8% | 57.5% | 52.5% | -3.8 [-17.5, +10.0] | -5.0 [-15.0, +6.2] |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 1024 | 77.5% | 65.0% | 56.2% | 57.5% | -21.2 [-31.2, -11.2] | +1.2 [-7.5, +10.0] |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 64 | 35.0% | 15.0% | 0.0% | 2.5% | -35.0 [-50.0, -20.0] | +2.5 [+0.0, +7.5] |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 128 | 30.0% | 22.5% | 65.0% | 85.0% | +35.0 [+15.0, +52.5] | +20.0 [+0.0, +37.5] |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 256 | 32.5% | 32.5% | 82.5% | 70.0% | +50.0 [+30.0, +70.0] | -12.5 [-30.0, +5.0] |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 512 | 37.5% | 27.5% | 50.0% | 95.0% | +12.5 [-10.0, +35.0] | +45.0 [+27.5, +62.5] |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 1024 | 47.5% | 42.5% | 50.0% | 100.0% | +2.5 [-17.5, +22.5] | +50.0 [+35.0, +65.0] |

## Identifier-complexity × budget interaction

A positive low-to-high estimate means UUID accuracy recovers relative to numeric as budget increases. The slope is the UUID-minus-numeric change, in percentage points, for each budget doubling.

| Model | Low-to-high interaction (pp, 95% CI) | Slope per doubling (pp, 95% CI) | 20-source minus 15-source UUID penalty (pp, 95% CI) |
|---|---:|---:|---:|
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | +3.7 [-13.7, +20.0] | -0.3 [-5.5, +4.8] | +4.0 [-13.0, +22.0] |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | +0.0 [-10.0, +10.0] | -1.6 [-4.5, +1.2] | -9.0 [-24.5, +6.0] |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | +7.5 [-12.5, +27.5] | +5.2 [-1.0, +11.0] | +0.0 [-24.0, +25.0] |

## Token use

| Model | Budget | UUID − numeric reasoning tokens (95% CI) | UUID − numeric total output tokens (95% CI) |
|---|---:|---:|---:|
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 64 | -6.5 [-10.7, -2.7] | +36.7 [+24.1, +49.5] |
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 128 | -13.2 [-22.7, -4.9] | +43.3 [+32.5, +53.6] |
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 256 | -11.6 [-36.3, +12.3] | +47.8 [+21.6, +73.7] |
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 512 | +17.9 [-14.6, +51.8] | +79.9 [+49.2, +112.1] |
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 1024 | +36.7 [-8.9, +93.4] | +100.6 [+54.4, +157.6] |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 64 | -8.5 [-12.4, -5.2] | +33.5 [+24.9, +41.5] |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 128 | -12.4 [-20.1, -5.3] | +33.0 [+22.1, +43.4] |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 256 | -33.3 [-48.8, -17.8] | +16.7 [+0.1, +33.0] |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 512 | +0.1 [-34.3, +34.3] | +48.0 [+12.9, +83.6] |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 1024 | -8.7 [-90.5, +75.1] | +39.6 [-42.0, +121.7] |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 64 | +15.8 [+13.1, +18.5] | +64.6 [+56.8, +72.7] |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 128 | +67.4 [+60.7, +73.2] | +123.1 [+111.8, +134.2] |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 256 | +107.3 [+87.0, +127.0] | +168.3 [+147.2, +188.6] |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 512 | +176.3 [+134.3, +219.7] | +241.7 [+199.9, +284.6] |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 1024 | +233.9 [+172.2, +301.9] | +299.1 [+239.0, +363.7] |

## Interpretation

The broad monotonic identifier-complexity × budget hypothesis is not confirmed: every confirmatory slope and low-to-high interval includes zero. Qwen nevertheless has significant UUID deficits at 128 and 1,024 tokens, which supports a persistent binding cost but not monotonic recovery with budget. Gemma E2B shows the predicted constrained-budget failure at 64 tokens (UUID minus numeric: -35 points), followed by a sharp non-monotonic reversal; removing UUID reproduction improves its accuracy by 45 and 50 points at 512 and 1,024 tokens. Tiny Aya's significant positive pilot slope does not replicate. No model has a source-count interaction whose interval excludes zero. UUIDs do reliably increase total generated output: the UUID-minus-numeric interval is strictly positive in 14 of 15 model-budget cells, but scratchpad-token direction is model-dependent.
