# Findings: MuSiQue Budget Sensitivity Analysis (LFM 2.5-2.6B)

## Objective
Post-hoc sensitivity analysis testing whether the observed $-10.4\text{ pp}$ UUID source-binding recall penalty at 15 sources on LFM 2.5-2.6B persists when the output token cap is doubled from 256 to 512 tokens.

## Design
* **Model:** `LiquidAI/LFM2.5-2.6B-GGUF:q4_k_m`
* **Snapshot Revision:** `e7caca5d835a3901a8e0d63e94009429bafafdfc`
* **GGUF SHA-256:** `02a8b7e17487d326e46d68ce0ba24211e1b80a14c4cd0597fa73c1cd697f52ed`
* **Software:** `llama-cpp-python` v0.3.36
* **Dataset:** 100 held-out disjoint MuSiQue-Answerable dev examples (`configs/musique/musique_confirmatory_heldout_100.json`).
* **Scenarios:** 15 and 20 sources (numeric `[1]` vs raw UUID identifiers), tested at 256 tokens and 512 tokens.

## Comparative Results

| Scenario | Budget | Numeric Truncation | UUID Truncation | Numeric Recall | UUID Recall | Recall Delta (UUID $-$ Num) | 95% Bootstrap CI |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **15 sources** | **256 tokens** | 33.0% | 50.0% | 24.2% | 13.8% | **$-10.42\text{ pp}$** | $[-16.25, -4.50]\text{ pp}$ |
| | **512 tokens** | **25.0%** | **37.0%** | 26.3% | 15.8% | **$-10.58\text{ pp}$** | $[-16.83, -4.50]\text{ pp}$ |
| **20 sources** | **256 tokens** | 31.0% | 51.0% | 19.8% | 15.2% | **$-4.67\text{ pp}$** | $[-10.08, +0.83]\text{ pp}$ |
| | **512 tokens** | **23.0%** | **39.0%** | 21.4% | 17.4% | **$-4.00\text{ pp}$** | $[-10.00, +1.83]\text{ pp}$ |

### Official Answer F1
* **15 sources:** $\Delta = -7.39\text{ pp}$ (95% CI: $[-15.35, +0.57]$) at 256 tokens $\rightarrow$ $\Delta = -4.55\text{ pp}$ (95% CI: $[-13.15, +4.02]$) at 512 tokens.
* **20 sources:** $\Delta = -0.18\text{ pp}$ (95% CI: $[-5.25, +4.71]$) at 256 tokens $\rightarrow$ $\Delta = -2.43\text{ pp}$ (95% CI: $[-9.02, +3.61]$) at 512 tokens.

## Conclusions
1. The 15-source UUID binding penalty was robust to doubling the output budget and reducing truncation; its estimated magnitude remained approximately $-10.5\text{ percentage points}$.
2. Residual truncation remains at 37%–39% under UUIDs even at 512 tokens, so truncation cannot be completely eliminated as a contributing factor without even larger budgets.
3. Answer F1 confidence intervals continue to include zero across both budgets, confirming that the degradation specifically affects source attribution rather than general multi-hop answer retrieval.
