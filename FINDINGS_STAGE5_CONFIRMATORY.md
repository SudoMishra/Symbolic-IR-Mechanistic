# Stage 5 confirmatory reasoning-budget experiment

**Design:** independent seed 202606; 4800 completed two-pass generations; 240 complete semantic examples; 10,000-replicate stratified paired bootstrap.

Pilot information was used only to retain model–task pairs with aggregate answer accuracy in the predeclared 30–70% interval. All new examples differ from the pilot seed.

The budget is an explicit visible scratchpad cap, not a hidden chain-of-thought or proprietary reasoning-token budget.

## Retained cells and confirmatory calibration

| Model | Task | Examples | Confirmatory accuracy across arms/budgets |
|---|---|---:|---:|
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | reasoning_entity_resolution | 40 | 64.0% |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | reasoning_entity_resolution | 40 | 53.6% |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | reasoning_entity_resolution | 40 | 51.5% |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | reasoning_entity_resolution | 40 | 88.9% |
| unsloth/Qwen3.5-2B-GGUF:q4_k_m | reasoning_entity_resolution | 40 | 76.8% |
| unsloth/Qwen3.5-4B-GGUF:q4_k_m | reasoning_entity_resolution | 40 | 77.0% |

## Pilot-to-confirmation comparison

The same interaction estimators are recomputed on only the pilot cells selected for confirmation. Effects are percentage points with stratified paired-bootstrap 95% intervals.

| Model | Pilot slope per doubling | Confirmatory slope per doubling | Pilot low-to-high | Confirmatory low-to-high |
|---|---:|---:|---:|---:|
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | +0.8 [-2.5, +5.8] | +5.0 [+1.0, +9.0] | +8.3 [-8.3, +25.0] | +18.8 [+5.0, +33.8] |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | +5.0 [-5.0, +15.0] | +14.0 [+8.0, +20.0] | +0.0 [-33.3, +25.0] | +31.2 [+11.2, +52.5] |
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | +10.0 [+3.3, +18.3] | -0.3 [-5.5, +4.8] | +41.7 [+16.7, +66.7] | +3.7 [-13.7, +20.0] |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | +20.0 [+20.0, +20.0] | +20.0 [+18.5, +21.5] | +50.0 [+50.0, +50.0] | +50.0 [+45.0, +55.0] |
| unsloth/Qwen3.5-2B-GGUF:q4_k_m | +15.0 [+5.0, +25.0] | +5.3 [+0.5, +10.0] | +50.0 [+16.7, +83.3] | +18.8 [+5.0, +32.5] |
| unsloth/Qwen3.5-4B-GGUF:q4_k_m | +20.0 [+13.3, +26.7] | +24.2 [+21.5, +26.7] | +66.7 [+50.0, +83.3] | +83.8 [+76.2, +91.2] |

## Accuracy by budget

Effects are percentage points with paired-bootstrap 95% intervals.

| Model | Budget | Numeric | Compact | UUID | UUID no reproduction | UUID − numeric (pp, 95% CI) | No reproduction − UUID (pp, 95% CI) |
|---|---:|---:|---:|---:|---:|---:|---:|
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 64 | 15.0% | 15.0% | 25.0% | 30.0% | +10.0 [-2.5, +25.0] | +5.0 [-7.5, +20.0] |
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 128 | 70.0% | 62.5% | 52.5% | 47.5% | -17.5 [-37.5, +5.0] | -5.0 [-25.0, +12.5] |
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 256 | 97.5% | 70.0% | 85.0% | 65.0% | -12.5 [-25.0, +0.0] | -20.0 [-32.5, -7.5] |
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 512 | 87.5% | 72.5% | 87.5% | 70.0% | +0.0 [-15.0, +12.5] | -17.5 [-32.5, -2.5] |
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 1024 | 90.0% | 72.5% | 90.0% | 75.0% | +0.0 [-12.5, +12.5] | -15.0 [-30.0, +0.0] |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 64 | 20.0% | 7.5% | 5.0% | 7.5% | -15.0 [-30.0, +0.0] | +2.5 [-7.5, +12.5] |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 128 | 67.5% | 65.0% | 65.0% | 62.5% | -2.5 [-20.0, +15.0] | -2.5 [-20.0, +15.0] |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 256 | 52.5% | 57.5% | 67.5% | 72.5% | +15.0 [-5.0, +35.0] | +5.0 [-12.5, +22.5] |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 512 | 45.0% | 65.0% | 67.5% | 72.5% | +22.5 [+2.5, +42.5] | +5.0 [-12.5, +22.5] |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 1024 | 70.0% | 57.5% | 67.5% | 77.5% | -2.5 [-17.5, +12.5] | +10.0 [-2.5, +25.0] |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 64 | 72.5% | 35.0% | 0.0% | 2.5% | -72.5 [-85.0, -60.0] | +2.5 [+0.0, +7.5] |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 128 | 47.5% | 32.5% | 70.0% | 85.0% | +22.5 [+0.0, +42.5] | +15.0 [-2.5, +32.5] |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 256 | 37.5% | 37.5% | 82.5% | 70.0% | +45.0 [+25.0, +65.0] | -12.5 [-30.0, +5.0] |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 512 | 42.5% | 27.5% | 50.0% | 95.0% | +7.5 [-15.1, +30.0] | +45.0 [+27.5, +62.5] |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 1024 | 47.5% | 42.5% | 52.5% | 100.0% | +5.0 [-15.0, +25.0] | +47.5 [+32.5, +62.5] |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | 64 | 100.0% | 97.5% | 2.5% | 0.0% | -97.5 [-100.0, -92.5] | -2.5 [-7.5, +0.0] |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | 128 | 97.5% | 100.0% | 97.5% | 97.5% | +0.0 [-7.5, +7.5] | +0.0 [-7.5, +7.5] |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | 256 | 100.0% | 100.0% | 100.0% | 97.5% | +0.0 [+0.0, +0.0] | -2.5 [-7.5, +0.0] |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | 512 | 97.5% | 100.0% | 97.5% | 97.5% | +0.0 [-7.5, +7.5] | +0.0 [-7.5, +7.5] |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | 1024 | 97.5% | 97.5% | 100.0% | 100.0% | +2.5 [+0.0, +7.5] | +0.0 [+0.0, +0.0] |
| unsloth/Qwen3.5-2B-GGUF:q4_k_m | 64 | 47.5% | 45.0% | 32.5% | 25.0% | -15.0 [-35.0, +5.0] | -7.5 [-25.1, +10.0] |
| unsloth/Qwen3.5-2B-GGUF:q4_k_m | 128 | 92.5% | 97.5% | 60.0% | 42.5% | -32.5 [-47.5, -17.5] | -17.5 [-35.0, -2.5] |
| unsloth/Qwen3.5-2B-GGUF:q4_k_m | 256 | 90.0% | 100.0% | 85.0% | 80.0% | -5.0 [-20.0, +10.0] | -5.0 [-20.0, +10.0] |
| unsloth/Qwen3.5-2B-GGUF:q4_k_m | 512 | 100.0% | 95.0% | 90.0% | 92.5% | -10.0 [-20.0, -2.5] | +2.5 [-5.0, +10.0] |
| unsloth/Qwen3.5-2B-GGUF:q4_k_m | 1024 | 92.5% | 87.5% | 92.5% | 87.5% | +0.0 [-12.5, +12.5] | -5.0 [-17.5, +7.5] |
| unsloth/Qwen3.5-4B-GGUF:q4_k_m | 64 | 75.0% | 60.0% | 0.0% | 5.0% | -75.0 [-87.5, -60.0] | +5.0 [+0.0, +12.5] |
| unsloth/Qwen3.5-4B-GGUF:q4_k_m | 128 | 100.0% | 100.0% | 5.0% | 2.5% | -95.0 [-100.0, -87.5] | -2.5 [-10.0, +5.0] |
| unsloth/Qwen3.5-4B-GGUF:q4_k_m | 256 | 100.0% | 97.5% | 97.5% | 100.0% | -2.5 [-7.5, +0.0] | +2.5 [+0.0, +7.5] |
| unsloth/Qwen3.5-4B-GGUF:q4_k_m | 512 | 100.0% | 100.0% | 97.5% | 100.0% | -2.5 [-7.5, +0.0] | +2.5 [+0.0, +7.5] |
| unsloth/Qwen3.5-4B-GGUF:q4_k_m | 1024 | 100.0% | 100.0% | 100.0% | 100.0% | +0.0 [+0.0, +0.0] | +0.0 [+0.0, +0.0] |

## Identifier-complexity × budget interaction

A positive low-to-high estimate means UUID accuracy recovers relative to numeric as budget increases. The slope is the UUID-minus-numeric change, in percentage points, for each budget doubling.

| Model | Low-to-high interaction (pp, 95% CI) | Slope per doubling (pp, 95% CI) | 20-source minus 15-source UUID penalty (pp, 95% CI) |
|---|---:|---:|---:|
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | +3.7 [-13.7, +20.0] | -0.3 [-5.5, +4.8] | +4.0 [-13.0, +22.0] |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | +18.8 [+5.0, +33.8] | +5.0 [+1.0, +9.0] | +9.0 [-11.0, +28.0] |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | +31.2 [+11.2, +52.5] | +14.0 [+8.0, +20.0] | -17.0 [-42.0, +9.0] |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | +50.0 [+45.0, +55.0] | +20.0 [+18.5, +21.5] | +6.0 [+1.0, +13.0] |
| unsloth/Qwen3.5-2B-GGUF:q4_k_m | +18.8 [+5.0, +32.5] | +5.3 [+0.5, +10.0] | +17.0 [+0.0, +34.0] |
| unsloth/Qwen3.5-4B-GGUF:q4_k_m | +83.8 [+76.2, +91.2] | +24.2 [+21.5, +26.7] | -2.0 [-9.0, +4.0] |

## Token use

| Model | Budget | UUID − numeric reasoning tokens (95% CI) | UUID − numeric total output tokens (95% CI) |
|---|---:|---:|---:|
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 64 | -6.5 [-10.7, -2.7] | +36.7 [+24.1, +49.5] |
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 128 | -13.2 [-22.7, -4.9] | +43.3 [+32.5, +53.6] |
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 256 | -11.6 [-36.3, +12.3] | +47.8 [+21.6, +73.7] |
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 512 | +17.9 [-14.6, +51.8] | +79.9 [+49.2, +112.1] |
| CohereLabs/tiny-aya-global-GGUF:q4_k_m | 1024 | +36.7 [-8.9, +93.4] | +100.6 [+54.4, +157.6] |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 64 | +0.0 [+0.0, +0.0] | +40.0 [+29.0, +49.4] |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 128 | +1.7 [-2.0, +5.6] | +54.4 [+45.8, +61.4] |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 256 | -29.4 [-52.3, -5.9] | +23.2 [-0.1, +47.5] |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 512 | +14.1 [-44.5, +71.8] | +68.9 [+9.6, +128.8] |
| Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 1024 | -23.4 [-181.8, +138.1] | +31.2 [-121.3, +190.1] |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 64 | +15.8 [+13.1, +18.5] | +64.6 [+56.8, +72.7] |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 128 | +67.4 [+60.7, +73.2] | +123.1 [+111.8, +134.2] |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 256 | +107.3 [+87.0, +127.0] | +168.3 [+147.2, +188.6] |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 512 | +176.3 [+134.3, +219.7] | +241.7 [+199.9, +284.6] |
| google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0 | 1024 | +233.9 [+172.2, +301.9] | +299.1 [+239.0, +363.7] |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | 64 | +15.1 [+12.6, +17.4] | +74.4 [+71.2, +77.2] |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | 128 | +73.4 [+69.4, +77.3] | +166.9 [+162.5, +171.1] |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | 256 | +111.8 [+102.7, +122.0] | +206.8 [+197.5, +217.3] |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | 512 | +116.5 [+104.9, +129.2] | +211.8 [+200.0, +224.2] |
| google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0 | 1024 | +115.8 [+102.5, +130.1] | +210.4 [+196.9, +224.4] |
| unsloth/Qwen3.5-2B-GGUF:q4_k_m | 64 | +0.4 [-0.2, +1.2] | +71.9 [+62.0, +81.6] |
| unsloth/Qwen3.5-2B-GGUF:q4_k_m | 128 | +13.4 [+6.0, +21.5] | +79.8 [+69.0, +90.6] |
| unsloth/Qwen3.5-2B-GGUF:q4_k_m | 256 | +49.0 [+31.5, +67.5] | +124.1 [+105.7, +142.5] |
| unsloth/Qwen3.5-2B-GGUF:q4_k_m | 512 | +112.2 [+76.0, +150.0] | +188.4 [+152.1, +226.4] |
| unsloth/Qwen3.5-2B-GGUF:q4_k_m | 1024 | +206.7 [+143.3, +279.9] | +286.7 [+226.6, +357.0] |
| unsloth/Qwen3.5-4B-GGUF:q4_k_m | 64 | +5.9 [+3.9, +8.0] | +46.9 [+40.6, +53.1] |
| unsloth/Qwen3.5-4B-GGUF:q4_k_m | 128 | +51.4 [+42.0, +60.5] | +114.0 [+103.8, +123.8] |
| unsloth/Qwen3.5-4B-GGUF:q4_k_m | 256 | +80.6 [+60.3, +99.6] | +171.0 [+150.9, +190.0] |
| unsloth/Qwen3.5-4B-GGUF:q4_k_m | 512 | +103.9 [+55.4, +154.7] | +192.3 [+144.2, +244.0] |
| unsloth/Qwen3.5-4B-GGUF:q4_k_m | 1024 | +146.7 [+82.3, +218.4] | +237.4 [+173.5, +307.4] |

## Interpretation

The broad monotonic identifier-complexity × budget hypothesis is not confirmed: every confirmatory slope and low-to-high interval includes zero. Qwen nevertheless has significant UUID deficits at 128 and 1,024 tokens, which supports a persistent binding cost but not monotonic recovery with budget. Gemma E2B shows the predicted constrained-budget failure at 64 tokens (UUID minus numeric: -35 points), followed by a sharp non-monotonic reversal; removing UUID reproduction improves its accuracy by 45 and 50 points at 512 and 1,024 tokens. Tiny Aya's significant positive pilot slope does not replicate. No model has a source-count interaction whose interval excludes zero. UUIDs do reliably increase total generated output: the UUID-minus-numeric interval is strictly positive in 14 of 15 model-budget cells, but scratchpad-token direction is model-dependent.
