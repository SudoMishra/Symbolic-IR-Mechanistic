# Cross-model symbolic-identifier findings

## Executive result

The matched experiment was replicated on Qwen2.5-1.5B, LiquidAI LFM2.5-1.2B, and Gemma 4 E2B/E4B. Every model saw the same 100 canonical examples in each condition, with deterministic decoding and native GGUF tokenization.

The central question is whether compact structured aliases improve exact source binding relative to UUIDs. Literal citation formatting is reported separately because omitted brackets can make strict exact match disagree with successful source selection.

## Exact source binding

| Model | 5 src structured | 5 src UUID | UUID−structured | 20 src structured | 20 src UUID | UUID−structured |
|---|---:|---:|---:|---:|---:|---:|
| Qwen2.5-1.5B | 96.0% | 63.0% | -33.0 pp | 66.0% | 37.0% | -29.0 pp |
| LiquidAI LFM2.5-1.2B | 43.0% | 8.0% | -35.0 pp | 10.0% | 0.0% | -10.0 pp |
| Gemma 4 E2B | 22.0% | 59.0% | +37.0 pp | 48.0% | 73.0% | +25.0 pp |
| Gemma 4 E4B | 100.0% | 100.0% | +0.0 pp | 100.0% | 100.0% | +0.0 pp |

## Twenty-source behavior and cost

| Model | Identifier | Answer content | Citation strict | Exact binding | Input tokens | Output tokens | Latency |
|---|---|---:|---:|---:|---:|---:|---:|
| Qwen2.5-1.5B | structured | 90.0% | 7.0% | 66.0% | 639.3 | 14.8 | 5.27s |
| Qwen2.5-1.5B | uuid | 92.0% | 34.0% | 37.0% | 1237.4 | 46.5 | 11.96s |
| LiquidAI LFM2.5-1.2B | structured | 99.0% | 0.0% | 10.0% | 601.5 | 41.3 | 3.50s |
| LiquidAI LFM2.5-1.2B | uuid | 94.0% | 0.0% | 0.0% | 1024.5 | 80.0 | 6.20s |
| Gemma 4 E2B | structured | 100.0% | 48.0% | 48.0% | 651.2 | 12.5 | 6.13s |
| Gemma 4 E2B | uuid | 100.0% | 73.0% | 73.0% | 1255.4 | 42.8 | 14.04s |
| Gemma 4 E4B | structured | 100.0% | 93.0% | 100.0% | 651.2 | 12.4 | 11.62s |
| Gemma 4 E4B | uuid | 100.0% | 83.0% | 100.0% | 1255.4 | 42.5 | 25.92s |

Token counts use each model's native tokenizer, so within-model structured/UUID ratios are the fair comparison; absolute counts across tokenizer families are descriptive.

## Numeric-alias control at 20 sources

Numeric `[1]` and structured `[S1]` are paired on the same examples. Effects are numeric minus structured. They are exactly token-matched under Qwen's tokenizer; under LiquidAI and Gemma tokenizers, numeric IDs are one token shorter per identifier (20 fewer prompt tokens in this cell), so those effects combine syntax and length.

| Model | ID tokens numeric / structured | Input tokens numeric / structured | Numeric binding | Structured binding | Binding delta (95% CI) | Strict delta |
|---|---:|---:|---:|---:|---:|---:|
| Qwen2.5-1.5B | 3.55 / 3.55 | 639.3 / 639.3 | 74.0% | 66.0% | +8.0 pp ([-3.0 pp, +19.0 pp], p=0.215) | +67.0 pp |
| LiquidAI LFM2.5-1.2B | 3.00 / 4.00 | 581.5 / 601.5 | 14.0% | 10.0% | +4.0 pp ([-1.0 pp, +10.0 pp], p=0.289) | +1.0 pp |
| Gemma 4 E2B | 3.55 / 4.55 | 631.2 / 651.2 | 61.0% | 48.0% | +13.0 pp ([+4.0 pp, +22.0 pp], p=0.0106) | +13.0 pp |
| Gemma 4 E4B | 3.55 / 4.55 | 631.2 / 651.2 | 100.0% | 100.0% | +0.0 pp ([+0.0 pp, +0.0 pp], p=1) | +7.0 pp |

## Statistical detail: UUID minus structured binding

| Model | Sources | Delta | Bootstrap 95% CI | Structured-only / UUID-only | Exact p |
|---|---:|---:|---:|---:|---:|
| Qwen2.5-1.5B | 5 | -33.0 pp | [-43.0 pp, -23.0 pp] | 35 / 2 | 1.02e-08 |
| Qwen2.5-1.5B | 20 | -29.0 pp | [-42.0 pp, -16.0 pp] | 41 / 12 | 8.17e-05 |
| LiquidAI LFM2.5-1.2B | 5 | -35.0 pp | [-46.0 pp, -24.0 pp] | 39 / 4 | 3.11e-08 |
| LiquidAI LFM2.5-1.2B | 20 | -10.0 pp | [-16.0 pp, -5.0 pp] | 10 / 0 | 0.00195 |
| Gemma 4 E2B | 5 | +37.0 pp | [+24.0 pp, +50.0 pp] | 9 / 46 | 4.34e-07 |
| Gemma 4 E2B | 20 | +25.0 pp | [+16.0 pp, +34.0 pp] | 1 / 26 | 4.17e-07 |
| Gemma 4 E4B | 5 | +0.0 pp | [+0.0 pp, +0.0 pp] | 0 / 0 | 1 |
| Gemma 4 E4B | 20 | +0.0 pp | [+0.0 pp, +0.0 pp] | 0 / 0 | 1 |

## Main findings

1. **The accuracy effect is model-dependent, not universal.** Compact structured aliases beat UUIDs on Qwen and LiquidAI, UUIDs beat structured aliases on Gemma 4 E2B, and Gemma 4 E4B was at ceiling for both.
2. **Compact aliases are universally more efficient in this study.** At 20 sources, UUIDs added 70–94% input tokens and 77–129% latency across the four models.
3. **More capability can erase the accuracy tradeoff.** E4B achieved 100% exact binding in all four Stage-1 cells, leaving efficiency and formatting as the differentiators. This is one checkpoint, not a parameter-scaling law.
4. **Strict citation match can misdiagnose source selection.** Wrapper omissions were common and model-specific; relaxed binding is therefore the primary behavioral metric.
5. **The numeric control does not isolate semantics on three tokenizers.** Qwen's exact token match gave an inconclusive +8 pp binding effect. LiquidAI was also inconclusive. E2B's significant +13 pp numeric effect is jointly attributable to label form and a 20-token prompt reduction; E4B remained at ceiling.

## Interpretation boundaries

- These are CPU, quantized-model results: Qwen and LiquidAI use Q4_K_M; the official Gemma 4 artifacts use Q4_0 QAT.
- The models are comparison-scale local models, not identical in parameter count or artifact size; the official Gemma 4 GGUF files are materially larger than the Qwen and LiquidAI files.
- One deterministic seed measures item variation but not decoding-seed or quantization variance.
- The task is fictional, single-hop retrieval with 5 or 20 sources. It does not establish effects for multi-hop reasoning or natural corpora.
- Latency includes prompt prefill plus generation and was measured sequentially on the same CPU runtime.
