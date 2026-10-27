# Stage 1 findings: structured aliases vs UUIDs (Preliminary Prefill Run)

> [!NOTE]
> This preliminary 400-generation run evaluated LFM 2.5-2.6B with closed-thinking prefill (`<think>\n</think>\n`) at an 80-token budget. It has been superseded by the full 1,600-generation factorial study documented in [FINDINGS_STAGE1_FACTORIAL.md](file:///home/sudomishra/Documents/ChatGPT/Symbolic%20IR%20Mechanistic/FINDINGS_STAGE1_FACTORIAL.md), which tests default chat template vs closed thinking crossed with 80-token vs 512-token generation limits.

**Model:** LiquidAI/LFM2.5-2.6B-GGUF:q4_k_m  
**Snapshot Revision:** `e7caca5d835a3901a8e0d63e94009429bafafdfc`  
**GGUF SHA-256:** `02a8b7e17487d326e46d68ce0ba24211e1b80a14c4cd0597fa73c1cd697f52ed`  
**Software:** `llama-cpp-python` v0.3.36  
**Design:** 400 deterministic generations; 100 paired examples per condition at 5 and 20 sources with closed thinking prefill.

## Accuracy and binding

| Sources | Identifier | Answer exact | Answer content | Citation strict | Source binding exact | Source recall |
|---:|---|---:|---:|---:|---:|---:|
| 5 | structured | 92.0% | 97.0% | 66.0% | 96.0% | 98.0% |
| 5 | uuid | 77.0% | 99.0% | 97.0% | 97.0% | 100.0% |
| 20 | structured | 59.0% | 69.0% | 43.0% | 68.0% | 74.0% |
| 20 | uuid | 85.0% | 85.0% | 57.0% | 57.0% | 60.0% |

`Citation strict` requires the literal identifier, including wrappers, and no extra IDs. `Source binding exact` accepts wrapper omissions but still requires exactly the correct source set. `Answer content` accepts the gold short answer inside a verbose answer field.

## Efficiency

| Sources | Identifier | Mean ID tokens | Input tokens | Output tokens | Latency (s) | Surface-only failures |
|---:|---|---:|---:|---:|---:|---:|
| 5 | structured | 4.00 | 216.17 | 18.02 | 0.21 | 30.0% |
| 5 | uuid | 24.73 | 319.84 | 37.56 | 0.42 | 2.0% |
| 20 | structured | 4.00 | 599.54 | 20.61 | 0.33 | 25.0% |
| 20 | uuid | 24.88 | 1017.09 | 34.98 | 0.57 | 0.0% |

## Paired effects

Effects are UUID minus structured; negative values favor structured aliases for accuracy.

| Sources | Metric | Paired delta | Bootstrap 95% CI | Structured-only / UUID-only | Exact p |
|---:|---|---:|---:|---:|---:|
| 5 | answer_exact | -15.0 pp | [-25.0, -5.0] pp | 22 / 7 | 0.00813 |
| 5 | answer_content_correct | +2.0 pp | [-2.0, +6.0] pp | 1 / 3 | 0.625 |
| 5 | citation_strict_correct | +31.0 pp | [+21.0, +41.0] pp | 3 / 34 | 1.23e-07 |
| 5 | source_binding_exact | +1.0 pp | [-2.0, +5.0] pp | 1 / 2 | 1 |
| 20 | answer_exact | +26.0 pp | [+16.0, +36.0] pp | 4 / 30 | 6.16e-06 |
| 20 | answer_content_correct | +16.0 pp | [+7.0, +25.0] pp | 4 / 20 | 0.00154 |
| 20 | citation_strict_correct | +14.0 pp | [+1.0, +27.0] pp | 15 / 29 | 0.0488 |
| 20 | source_binding_exact | -11.0 pp | [-22.0, +0.0] pp | 21 / 10 | 0.0708 |

## Findings

1. **Compact aliases improved source binding at 20 sources under closed-thinking prefill.** Source recall was 98% vs 100% at 5 sources, but 74% vs 60% at 20 sources (structured vs UUID). Exact binding was 96% vs 97% at 5 sources, and 68% vs 57% at 20 sources.
2. **Strict citation fidelity reversed at 5 sources.** Structured IDs showed 66% strict citation syntax vs 97% for UUIDs at 5 sources (due to emitting bare `S1` instead of `[S1]`), and 43% vs 57% at 20 sources.
3. **Answer content was high across conditions.** Content accuracy was 97% vs 99% at 5 sources and 69% vs 85% at 20 sources.
4. **UUID overhead scaled sharply.** UUID prompts used about 48% more input tokens at 5 sources (320 vs 216) and 70% more at 20 sources (1017 vs 600).
5. **Prefill bypassed the reasoning token trap.** Prefilling `<think>\n</think>\n` allowed LFM 2.6B to emit direct answers without getting stuck in deliberation loops. See [FINDINGS_STAGE1_FACTORIAL.md](file:///home/sudomishra/Documents/ChatGPT/Symbolic%20IR%20Mechanistic/FINDINGS_STAGE1_FACTORIAL.md) for full factorial comparison with default decoding.

## Limitations

- One small 2.6B-parameter hybrid model and one Q4_K_M quantization; these results do not generalize to larger or proprietary models.
- One deterministic seed and no between-run sampling variance.
- Single-hop fictional QA only; no multi-hop or length-matched controls yet.
- Latency combines prompt prefill and output generation, so it is not a pure reasoning-cost measure.
