# Excluded Artifacts: Liquid Foundation Models (LFM 2.5 1.2B & 2.6B)

Per study locked decisions **D-02** and **D-03**:
- **D-02 — LFM exclusion:** Exclude LFM 2.5 1.2B and LFM 2.5 2.6B from all published counts, analyses, tables, figures, captions, and conclusions until their behavior is independently investigated.
- **D-03 — Exclusion transparency:** Preserve LFM raw artifacts internally and include one short public methods note explaining that two LFM checkpoints were excluded because the inference behavior could not be validated. Do not publish their numerical results.

## Model Checkpoints Preserved
1. `models/lfm2.5-1.2b-instruct-q4_k_m.gguf` & `models/lfm2.5-1.2b-instruct-hf`
2. `models/LFM2.5-2.6B-Q4_K_M.gguf`

## Preserved Raw and Processed Artifacts
All LFM artifacts are retained unmodified in their original locations but are strictly classified as `excluded`. They are excluded from all aggregates, manifests, figures, and publication tables.

### Raw Artifacts (Sample Inventory)
- `results/raw/01_citation_mve_lfm25_12b_q4km/e3210d69324a.jsonl`
- `results/raw/01_citation_mve_500_lfm25_12b/7d4e5d979379.jsonl`
- `results/raw/01_citation_mve_500_lfm25_26b/d03cc1f1013f.jsonl`
- `results/raw/stage1_lfm25_26b.jsonl`
- `results/raw/stage1_lfm25_26b_factorial.jsonl`
- `results/raw/musique_confirmatory_lfm25_12b/`
- `results/raw/musique_confirmatory_lfm25_26b/fb81c257b56d.jsonl`
- `results/raw/musique_500_lfm25_12b/8bb6215a0807.jsonl`
- `results/raw/musique_500_lfm25_26b/9831ecc9d70e.jsonl`
- `results/raw/musique_stages_2_4_lfm25_12b/`
- `results/raw/musique_stages_2_4_lfm25_26b/`
- `results/raw/stage5_pilot_lfm25_12b/`
- `results/raw/stage5_pilot_lfm25_26b/a816243d2fff.jsonl`
- `results/raw/stage5_confirm_lfm25_26b/`
- `results/raw/longproc_tom_tracking_2k_lfm25_12b/`
- `results/raw/longproc_tom_tracking_2k_lfm25_26b/`
- `results/raw/stage8_pii_lfm25_12b/`
- `results/raw/stage8_pii_lfm25_26b/aa21eef2841f.jsonl`
- `results/raw/stage8_pii_500_lfm25_12b/ec4acb19064e.jsonl`
- `results/raw/stage8_pii_500_lfm25_26b/3fb6d35d320d.jsonl`

### Processed Artifacts (Excluded from Publication)
- `results/processed/stage1_lfm25_26b.json`
- `results/processed/stage1_lfm25_26b_factorial.json`
- `results/processed/stage1_500_lfm25_12b.json`
- `results/processed/stage1_500_lfm25_26b.json`
- `results/processed/stage6_lfm25_12b.json`
- `results/processed/stage8_pii_lfm25_12b.json`
- `results/processed/stage8_pii_lfm25_26b.json`
- `results/processed/stage8_pii_500_lfm25_12b.json`
- `results/processed/stage8_pii_500_lfm25_26b.json`

## Rationale for Exclusion
Inference validation revealed non-standard tokenization behavior, unvalidated EOS handling, and unresolvable prompt template sensitivities in the community GGUF/HF implementations of the hybrid Conv/Linear-Attention architecture that could not be verified against official vendor reference weights within the study timeline.
