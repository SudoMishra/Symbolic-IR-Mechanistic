# Findings: Stage 1 Factorial Ablation (LFM 2.5-2.6B)

## Objective
Disentangle decoding configuration (thinking-tag handling) from generation output budget on LFM 2.5-2.6B across 100 paired Stage 1 examples at 5 and 20 sources (structured vs UUID identifiers).

## Design
* **Model:** `LiquidAI/LFM2.5-2.6B-GGUF:q4_k_m`
* **Snapshot Revision:** `e7caca5d835a3901a8e0d63e94009429bafafdfc`
* **GGUF SHA-256:** `02a8b7e17487d326e46d68ce0ba24211e1b80a14c4cd0597fa73c1cd697f52ed`
* **Software:** `llama-cpp-python` v0.3.36
* **Dataset:** 100 paired fictional citation QA examples (`seed=202601`), single-hop, tested at $N=5$ and $N=20$ sources.
* **Factorial Matrix:**
  * Factor 1: Chat Template / Thinking (`default` vs `prefill` closed thinking `<think>\n</think>\n`)
  * Factor 2: Generation Budget (`80` vs `512` tokens)
  * Conditions: `structured` (`[S1]`, `[S2]`, ...) vs `uuid` (`[0-9a-f-]{36}`)
* **Total Generations:** 100 examples $\times$ 2 source counts $\times$ 2 conditions $\times$ 4 arms = 1,600 runs.

## Results

| Sources | Condition | Arm | Content Acc | Strict Ans Acc | Relaxed Recall | Strict Cit Syntax | Truncation Rate | Mean Output Tokens |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **5** | **Structured** | `default_80` | 0.0% | 0.0% | 0.0% | 0.0% | 100.0% | 80.0 |
| | | `default_512` | 96.0% | 96.0% | 99.0% | 19.0% | 6.0% | 388.2 |
| | | `prefill_80` | 97.0% | 92.0% | 98.0% | 66.0% | 0.0% | 18.0 |
| | | `prefill_512` | 97.0% | 92.0% | 98.0% | 66.0% | 0.0% | 18.0 |
| **5** | **UUID** | `default_80` | 1.0% | 0.0% | 0.0% | 0.0% | 100.0% | 80.0 |
| | | `default_512` | 96.0% | 96.0% | 98.0% | 59.0% | 82.0% | 505.6 |
| | | `prefill_80` | 99.0% | 77.0% | 100.0% | 97.0% | 0.0% | 37.6 |
| | | `prefill_512` | 99.0% | 77.0% | 100.0% | 97.0% | 0.0% | 37.6 |
| **20** | **Structured** | `default_80` | 32.0% | 0.0% | 0.0% | 0.0% | 100.0% | 80.0 |
| | | `default_512` | 82.0% | 61.0% | 83.0% | 23.0% | 35.0% | 400.7 |
| | | `prefill_80` | 69.0% | 59.0% | 74.0% | 43.0% | 0.0% | 20.6 |
| | | `prefill_512` | 69.0% | 59.0% | 74.0% | 43.0% | 0.0% | 20.6 |
| **20** | **UUID** | `default_80` | 2.0% | 0.0% | 0.0% | 0.0% | 100.0% | 80.0 |
| | | `default_512` | 12.0% | 11.0% | 15.0% | 9.0% | 84.0% | 494.0 |
| | | `prefill_80` | 85.0% | 85.0% | 60.0% | 57.0% | 0.0% | 35.0 |
| | | `prefill_512` | 85.0% | 85.0% | 60.0% | 57.0% | 0.0% | 35.0 |

## Key Findings
1. **Initial Zero Scores were 100% Truncation:** Under `default_80`, every generation exhausted its 80-token cap inside `<think>...</think>`.
2. **Prefilling Closed Thinking Eliminates Budget Sensitivity:** Under `prefill_80` and `prefill_512`, truncation is 0.0% and metrics are byte-identical across budgets.
3. **UUIDs Inflate Deliberation:** Under `default_512`, UUID runs truncate 82%–84% of the time, collapsing 20-source recall to 15.0%, whereas closed-thinking prefill achieves 60.0% recall.
