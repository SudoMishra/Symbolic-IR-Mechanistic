# Repair Start State Audit Note

- **Timestamp**: 2026-10-30T02:05:00+05:30
- **Git Commit Hash**: `f0160fbd9c939eaf9c77347cb29c306054257049`
- **Branch**: `narrative-restructure`
- **Dirty Worktree Status**: Cleaned baseline commit with working directory modifications and untracked files from earlier exploratory/scaling phases.

## Summary of Modified Files

The following files are modified in the working tree relative to `HEAD`:
- `.gitignore`
- `FINDINGS_MUSIQUE_CONFIRMATORY.md`
- `FINDINGS_MUSIQUE_STAGES_2_4.md`
- `FINDINGS_STAGE1.md`
- `FINDINGS_STAGE8_CROSS_MODEL.md`
- `MODEL_PROVENANCE.md`
- `blog/appendix.md`
- `blog/assets/02_evidence_funnel.svg`
- `blog/assets/02_evidence_funnel_mobile.svg`
- `blog/assets/03_musique_confirmation.svg`
- `blog/assets/04_reasoning_budget.svg`
- `blog/assets/05_longproc.svg`
- `blog/assets/06_stage6_geometry.svg`
- `blog/assets/07_stage7_swaps.svg`
- `blog/assets/08_stage8_entities.svg`
- `blog/evidence_manifest.csv`
- `blog/scripts/build_figures.py`
- `blog/site/assets/02_evidence_funnel.svg`
- `blog/site/assets/02_evidence_funnel_mobile.svg`
- `blog/site/assets/03_musique_confirmation.svg`
- `blog/site/assets/04_reasoning_budget.svg`
- `blog/site/assets/05_longproc.svg`
- `blog/site/assets/06_stage6_geometry.svg`
- `blog/site/assets/07_stage7_swaps.svg`
- `blog/site/assets/08_stage8_entities.svg`
- `blog/site/index.html`
- `blog/site/styles.css`
- `blog/symbolic-ir-engineering-blog.md`
- `results/processed/musique_confirmatory.json`
- `results/processed/musique_stages_2_4.json`
- `scripts/analyze_musique_confirmatory.py`
- `scripts/analyze_musique_stages.py`
- `scripts/analyze_stage1.py`
- `scripts/analyze_stage8_cross_model.py`
- `scripts/run_musique_stages.py`
- `src/symbolic_ir/evaluation/evaluate.py`
- `src/symbolic_ir/evaluation/parser.py`
- `src/symbolic_ir/inference/factory.py`
- `src/symbolic_ir/inference/openai_api.py`
- `src/symbolic_ir/runner.py`
- `src/symbolic_ir/schema.py`
- `tests/test_blog_claims.py`
- `tests/test_config.py`
- `tests/test_parser.py`

## Untracked Scientific Artifacts & Additions

The untracked files include:
- Finding notes:
  - `FINDINGS_FRONTIER_ANTHROPIC.md`
  - `FINDINGS_LONGPROC_LFM25_26B_NATIVE_DIAGNOSTIC.md`
  - `FINDINGS_MUSIQUE_500.md`
  - `FINDINGS_MUSIQUE_500_DISJOINT_401.md`
  - `FINDINGS_STAGE1_500_*.md` (8 models)
  - `FINDINGS_STAGE1_QWEN35_*.md`
  - `FINDINGS_STAGE8_500_*.md` (8 models)
  - `FINDINGS_STAGE8_*.md` (various)
  - `MECHINTERP_RESEARCH_ROADMAP.md`
- Checklist:
  - `blog/STUDY_CONSISTENCY_REPAIR_CHECKLIST.md`
- Figures:
  - `blog/assets/03b_frontier_musique.svg`
  - `blog/assets/04b_anthropic_reasoning.svg`
  - `blog/site/assets/03b_frontier_musique.svg`
  - `blog/site/assets/04b_anthropic_reasoning.svg`
- Experiment configs:
  - `configs/experiments/citation_mve_500*.yaml`
  - `configs/experiments/stage5_*.yaml`
  - `configs/experiments/stage8_pii_500*.yaml`
  - `configs/musique/musique_500*.yaml`
  - `configs/longproc/`
- Batches & Ledger:
  - `results/batches/prepared/`
  - `results/batches/tracking/`
  - `results/budget_ledger.jsonl`
- Scripts & Infrastructure:
  - `scripts/execute_frontier_batches.py`
  - `scripts/prepare_frontier_*.py`
  - `scripts/run_frontier_phase1_stability.py`
  - `src/symbolic_ir/budget.py`
  - `src/symbolic_ir/inference/anthropic_api.py`
  - `src/symbolic_ir/inference/batch.py`
  - `src/symbolic_ir/statistics.py`
  - `tests/test_frontier_analysis.py`

This note establishes the reproducible starting baseline before study consistency repairs.
