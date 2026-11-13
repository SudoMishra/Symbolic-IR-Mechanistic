# Agent Instructions & Workflow Protocol

## 1. Upfront Visibility & Communication Protocol (Mandatory)
- **Show Before Doing**: Before running tools, executing shell commands, or modifying files, always state clearly in visible text what you are about to do, why you are doing it, and the specific sequence of actions you plan to take.
- **No Black-Box Execution**: Never run long chains of silent tool operations where the user only sees executing commands without rationale or context. Provide visible reasoning and plans ahead of execution.
- **Progress Tracking**: For multi-step tasks, summarize intermediate findings and state the next planned action before executing it.

## 2. Project Architecture & Context
- **Workspace**: Symbolic IR Mechanistic Interpretability (`Symbolic IR Mechanistic`).
- **Core Investigation**: Causal component-level circuit decomposition (Stage 7B) across open-weights LLMs (Qwen 2.5 1.5B, Qwen 3.5 2B/4B, Tiny Aya Global, Gemma 4 E2B/E4B), examining binding ($B$) vs. serialization/continuation ($F$) dissociation.
- **Python Environment**: Local virtual environment `.venv/bin/python` (Python 3.12, PyTorch 2.5.1+cu121).
- **Test Suite**: Run tests using `.venv/bin/pytest tests/`. Ensure all tests pass before completing tasks.

## 3. Scientific & Data Rigor Standards
- **Statistical Integrity**: All causal intervention metrics report paired cluster-bootstrap 95% confidence intervals clustered by `example_id` ($B=1,000$). Never report uncomputed p-values or arbitrary significance thresholds.
- **Data Provenance**: All split datasets (`discovery_n32.jsonl`, `validation_n32.jsonl`, `confirmation_n80.jsonl`) and `circuit_preregistration.json` are tracked with relative paths and SHA-256 hashes in `data/circuit/dataset_manifest.json`. Splits must remain strictly disjoint.
- **Documentation Fidelity**: Never overwrite historical pilot artifacts (`*pilot12*`). Maintain exact numeric consistency across `blog/`, `blog/site/`, `results/`, and `tests/`.
