# Mechanistic Eligibility & Framework Compatibility Audit Report

Governed by locked decisions **D-05** and **D-06**.

## Summary of Frozen Mechanistic Cohort
- **Eligible Local Models (6):** tiny_aya_global, qwen25_15b, gemma4_e2b, gemma4_e4b, qwen35_2b, qwen35_4b
- **Unsupported Local Models (0):** 
- **Frontier Models (4):** All marked `not_applicable` per D-05.

## Detailed Local Model Audit

| Model | Eligibility Status | Hook Framework Compatible | Residual Stream Capture | Technical Ground / Failure Reason |
|---|---|:---:|:---:|---|
| Tiny Aya Global (`tiny_aya_global`) | **`eligible`** | Yes | Yes | Passed all hook validation, residual capture, and intervention tests. |
| Qwen 2.5 1.5B Instruct (`qwen25_15b`) | **`eligible`** | Yes | Yes | Passed all hook validation, residual capture, and intervention tests. |
| Gemma 4 E2B IT (`gemma4_e2b`) | **`eligible`** | Yes | Yes | Passed all hook validation, residual capture, and intervention tests. |
| Gemma 4 E4B IT (`gemma4_e4b`) | **`eligible`** | Yes | Yes | Passed all hook validation, residual capture, and intervention tests. |
| Qwen 3.5 2B (`qwen35_2b`) | **`eligible`** | Yes | Yes | Passed all hook validation, residual capture, and intervention tests. |
| Qwen 3.5 4B (`qwen35_4b`) | **`eligible`** | Yes | Yes | Passed all hook validation, residual capture, and intervention tests. |

## Frontier Model Scope

| Model | Status | Technical Ground |
|---|---|---|
| `claude-haiku-5-5` | `not_applicable` | Closed-weights commercial API (Anthropic / OpenAI). Internal weights, hidden layers, and attention matrices are not exposed (locked decision D-05). |
| `claude-sonnet-5-5` | `not_applicable` | Closed-weights commercial API (Anthropic / OpenAI). Internal weights, hidden layers, and attention matrices are not exposed (locked decision D-05). |
| `gpt-6-1-sol` | `not_applicable` | Closed-weights commercial API (Anthropic / OpenAI). Internal weights, hidden layers, and attention matrices are not exposed (locked decision D-05). |
| `gpt-6-luna` | `not_applicable` | Closed-weights commercial API (Anthropic / OpenAI). Internal weights, hidden layers, and attention matrices are not exposed (locked decision D-05). |
