# Anthropic Frontier Extension

## Scope

This report compiles only completed Anthropic batches. Partial OpenAI batches are excluded. The checked-in processed artifact is `results/processed/frontier_anthropic_summary.json`.

- MuSiQue: 500 matched questions × 2 identifier conditions × 2 source counts for each of Claude Haiku 5.5 and Claude Sonnet 5.5 (4,000 generations).
- Reasoning setting: 100 matched Sonnet questions × 2 identifier conditions × 2 source counts (400 generations).
- Stage 8 entity resolution: 500 matched cases × 4 representations on Sonnet (2,000 generations).
- Total: 6,400 generations; analyzed batch cost $21.22. The broader Anthropic budget ledger includes separate stability checks and totals $23.38.

## MuSiQue primary endpoint

The primary endpoint is relaxed source-binding recall. Confidence intervals use 10,000 paired bootstrap resamples over matched questions.

| Model | Sources | Numeric | UUID | UUID − Numeric (95% CI) |
|---|---:|---:|---:|---:|
| Claude Haiku 5.5 | 15 | 73.28% | 6.08% | -67.20 pp [-70.05, -64.33] |
| Claude Haiku 5.5 | 20 | 72.40% | 6.22% | -66.18 pp [-69.12, -63.15] |
| Claude Sonnet 5.5 | 15 | 89.18% | 88.42% | -0.77 pp [-2.08, +0.47] |
| Claude Sonnet 5.5 | 20 | 89.07% | 87.27% | -1.80 pp [-3.03, -0.63] |

Haiku suffered a large binding collapse while its answer-exact difference stayed near zero. Sonnet retained high binding recall: the 15-source interval included zero and the 20-source effect was small but negative. The result is model-dependent, not a universal frontier-model effect.

## Reasoning-setting check

On 200 paired Sonnet source-count cells, the UUID-minus-numeric exact-binding gap was -1.0 pp with the no-reasoning execution and +2.0 pp with adaptive-low. The between-setting change was +3.0 pp (95% CI [-3.0, +9.0]). The API reported zero reasoning tokens for all adaptive-low responses, so this comparison does not establish how much hidden reasoning occurred.

## Stage 8

Sonnet scored 100.0% under raw, random-masked, and untyped conditions and 99.8% with typed handles. Typed minus untyped was -0.2 pp (95% CI [-0.6, 0.0]). Raw-value output exposure was 100.0% in the raw condition and 0.0% in each masked condition. The accuracy task was saturated, so this run supports exposure control but not a typed-handle accuracy benefit.

## Reproduction

```bash
PYTHONPATH=src:. .venv/bin/python scripts/generate_frontier_final_report.py --provider anthropic
```
