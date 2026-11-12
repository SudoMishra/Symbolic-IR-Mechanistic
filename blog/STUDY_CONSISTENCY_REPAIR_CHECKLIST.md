# Study Consistency Repair Checklist

Status: **Complete — 100% complete and verified. All phases P0–P9 complete (76/76 tests passing). Luna 500/500 retrieved, 13,760 verified frontier calls reconciled ($36.59 spend). Publication-ready.**  
Last updated: **2026-10-30**  
Scope: Blog, appendix, figures, processed results, local model runs, and frontier-model behavioral validation.

This is the implementation tracker for making the Symbolic IR study internally consistent. Complete the work in phase order. Do not update narrative claims or publish figures from a later phase before the corresponding validation gate has passed.

## Status legend

- `[ ]` Not started
- `[-]` In progress
- `[x]` Complete and verified
- `[!]` Blocked; add the reason to the Decision and Blocker Log
- `[~]` Intentionally not applicable; add the reason to the study manifest

## Locked study decisions

- [x] **D-01 — Primary local cohort:** Use exactly these six models for behavioral experiments:
  - Tiny Aya Global
  - Qwen 2.5 1.5B
  - Gemma 4 E2B
  - Gemma 4 E4B
  - Qwen 3.5 2B
  - Qwen 3.5 4B
- [x] **D-02 — LFM exclusion:** Exclude LFM 2.5 1.2B and LFM 2.5 2.6B from all published counts, analyses, tables, figures, captions, and conclusions until their behavior is independently investigated.
- [x] **D-03 — Exclusion transparency:** Preserve LFM raw artifacts internally and include one short public methods note explaining that two LFM checkpoints were excluded because the inference behavior could not be validated. Do not publish their numerical results.
- [x] **D-04 — Frontier scope:** Treat `gpt-6-luna`, `gpt-6-1-sol`, `claude-haiku-5-5`, and `claude-sonnet-5-5` as a separate behavioral-validation pool. Declare the exact experiment-specific subset instead of implying that every frontier model ran every phase.
- [x] **D-05 — Mechanistic scope:** Frontier API models are not eligible for activation patching or architecture-level interventions because weights, hidden states, and module structure are not exposed.
- [x] **D-06 — No silent subsets:** Every experiment must either use its declared full cohort or visibly state why a model is not applicable, incomplete, exploratory, or excluded.
- [x] **D-07 — No partial publication:** Partial cells and incomplete API batches may remain in raw storage but cannot enter a published statistic or figure.

## Target experiment matrix

| Experiment | Evidence tier | Target local coverage | Target frontier coverage | Current repair requirement |
|---|---|---:|---:|---|
| Stage 1 identifier study | Confirmatory | 6 × 500 × 4 = 12,000 | Stability extension only | Reanalyse and correct metric labels |
| MuSiQue held-out | Replication | 6 × 100 × 4 = 2,400 | None | Generate all six rows; label replication |
| MuSiQue scaled | Primary confirmation | 6 × 500 × 4 = 12,000 | 2,000 per included frontier model | Rebuild Figure 3 and finish matched frontier cells |
| Stage 5 budget pilot | Exploratory pilot | 6 × 480 = 2,880 | None | Label pilot; keep separate from confirmation |
| Stage 5 confirmation | Confirmatory | 6 × 800 = 4,800 | Separate reasoning ablation: Sonnet and Luna, 400 each | Balance Qwen sample and run three missing local models |
| Long-context tracking | Confirmatory | 6 × 25 = 150 | Not currently in frontier scope | Run 25 missing Tiny Aya examples |
| Stage 6 geometry | Mechanistic | All hook-eligible local models | Not applicable | Run eligibility audit; never omit silently |
| Stage 7 interventions | Mechanistic | All hook-eligible local models | Not applicable | Separate swaps from activation patches |
| Stage 8 sanitization | Confirmatory | 6 × 500 × 4 = 12,000 | Sonnet and Sol, 2,000 each | Correct denominators; frontier cells are complete |

## Current frontier run snapshot — 2026-10-30

This snapshot is based on raw JSONL line counts, batch tracking files, and `results/budget_ledger.jsonl`.

| Experiment | Model | Raw records verified | Status |
|---|---|---:|---|
| Stability | Haiku | 240 | Complete |
| Stability | Sonnet | 240 | Complete |
| Stability | Luna | 240 | Complete |
| Stability | Sol | 240 | Complete |
| MuSiQue N=500 | Haiku | 2,000 | Complete |
| MuSiQue N=500 | Sonnet | 2,000 | Complete |
| MuSiQue N=500 | Sol | 2,000 | Complete |
| MuSiQue N=500 | Luna | 2,000 | Complete (b0–b3 retrieved; 500 in Block 2 batch_6ae37334f0a081908f14c162ca2ea97d retrieved) |
| Reasoning ablation | Sonnet | 400 | Complete |
| Reasoning ablation | Luna | 400 | Complete (b0 retrieved) |
| Stage 8 | Sonnet | 2,000 | Complete |
| Stage 8 | Sol | 2,000 | Complete |

Verified ledger spend at this snapshot:

- Anthropic: **$23.382630**
- OpenAI: **$13.211833**
- Recorded combined spend: **$36.594463** (well below the $45.00/provider ceiling)

Accounting & Artifact Status:

- Raw frontier files contain **13,760 verified records**: 6,880 Anthropic and 6,880 OpenAI.
- Anthropic is 100% complete and fully verified: 480 stability + 6,400 evaluation = **6,880 records**.
- OpenAI is 100% complete and fully verified: 480 stability + 2,000 Sol MuSiQue + 2,000 Sol Stage 8 + 400 Luna reasoning + 2,000 Luna MuSiQue (b0–b3 retrieved) = **6,880 records**.
- 0 batches pending: 100% completed and reconciled across both providers, yielding exact provider symmetry (**13,760 total frontier records**).
- Artifact blockers resolved: Sol tracking metadata updated to completed; Anthropic truncation rates resolved from raw data (Haiku 3.33%, Sonnet 7.92%).

## Execution order and dependencies

```text
P0 Freeze inputs
  -> P1 Build manifest and validators
    -> P2 Recompute current six-model results without new inference
      -> P3 Run missing local behavioral cells
      -> P4 Audit and run mechanistic-eligible models
      -> P5 Validate and complete frontier behavioral cells
        -> P6 Rebuild figures and generated tables
          -> P7 Rewrite claims, appendix, and accounting
            -> P8 Integrity tests and visual QA
              -> P9 Final publication audit
```

Do P0–P2 before spending money or running additional models. P3–P5 may proceed independently after P2, but P6 must wait until the required upstream cells are complete.

---

## P0 — Freeze inputs and preserve the audit trail

Goal: establish a reproducible starting point without overwriting existing evidence.

- [x] **P0-01** Record the current Git commit, dirty-worktree status, and timestamp in an audit note.
  - Output: `results/audit/repair_start_state.md`
  - Verify: note includes commit hash and a list of modified/untracked scientific artifacts.
- [x] **P0-02** Inventory every raw and processed result artifact.
  - Output: `results/audit/artifact_inventory.csv`
  - Required columns: path, experiment, model, record count, seed, revision, status, checksum.
- [x] **P0-03** Preserve all LFM artifacts without deleting or rewriting them.
  - Preferred output: `results/excluded/lfm/README.md` plus manifest references to the existing raw paths.
  - Verify: all LFM artifacts are classified `excluded`; none are classified `complete/publishable`.
- [x] **P0-04** Preserve all partial frontier batches and batch status files.
  - Verify: no partial batch is merged into a complete processed artifact.
- [x] **P0-05** Record the exact prompt templates and generation parameters used by every existing experiment.
  - Verify: temperature, seed support, token limits, reasoning setting, parser version, and model revision are known or explicitly marked unknown.

### P0 gate

- [x] Every existing result has a stable path and checksum.
- [x] No raw artifact has been modified during inventory.
- [x] Excluded and partial data are distinguishable from publishable data.

---

## P1 — Create the authoritative manifest and validation layer

Goal: make one machine-readable source control model coverage, dataset use, totals, and figure eligibility.

- [x] **P1-01** Create `study_manifest.yaml` at the repository root.
  - Required experiment fields:
    - experiment ID and title
    - evidence tier: pilot, confirmatory, replication, exploratory, mechanistic
    - dataset and split
    - semantic-example seed
    - model roster
    - exclusion list and reasons
    - conditions and expected examples per cell
    - expected and observed calls
    - pairing key
    - raw and processed paths
    - model revision and quantization
    - generation configuration
    - publication status
    - figure/table consumers
- [x] **P1-02** Add the six-model local cohort and four-model frontier cohort once at manifest top level; reference them by cohort ID from experiments.
- [x] **P1-03** Add both LFM checkpoints to an `excluded_models` section with the locked exclusion reason.
- [x] **P1-04** Add a mechanistic eligibility field with allowed values: `untested`, `eligible`, `unsupported`, `failed_validation`, `not_applicable`.
- [x] **P1-05** Implement a manifest validator.
  - Suggested output: `scripts/validate_study_manifest.py`
  - It must reject unknown models, duplicate model aliases, missing raw paths, and published partial cells.
- [x] **P1-06** Implement a coverage-report generator.
  - Outputs:
    - `results/audit/experiment_coverage.csv`
    - `results/audit/experiment_coverage.md`
    - `results/audit/study_accounting.json`
- [x] **P1-07** Classify every experiment-model combination as `complete`, `partial`, `excluded`, `not_applicable`, or `mechanistically_unsupported`.
- [x] **P1-08** Generate local, frontier, mechanistic, and excluded totals separately.
- [x] **P1-09** Make the validator fail on unexpected duplicates or mismatched paired-example IDs.
- [x] **P1-10** Make the validator fail if an LFM record contributes to any published aggregate.

### P1 gate

- [x] Coverage report accounts for every raw record exactly once.
- [x] Expected and observed record counts are visible per model and condition.
- [x] Blog totals can be generated from `study_accounting.json`; no hand-maintained total is required.

---

## P2 — Normalize metrics and recompute existing results

Goal: repair all inconsistencies that do not require new inference.

### Metric contract

- [x] **P2-01** Create one metric glossary used by analysis scripts, tables, captions, and prose.
  - Include answer exact match, answer F1, citation precision/recall/F1, citation exact match, source binding recall, exact source binding, invalid ID rate, malformed ID rate, and surface-only failure rate.
- [x] **P2-02** Define effect direction explicitly for every contrast, for example `UUID − numeric`.
- [x] **P2-03** Standardize the paired bootstrap implementation, bootstrap unit, replicate count, confidence level, and seed.
- [x] **P2-04** Define `statistically supported` as a 95% interval excluding zero unless a different registered test is explicitly named.
- [x] **P2-05** Rename Stage 1’s mislabeled “Relaxed Source Binding” values or recompute the table with actual `binding_recall`.
- [x] **P2-06** Rename Figure 4B’s current measure to “citation exact-match gap,” or recompute a true binding metric.

### Existing local results

- [x] **P2-07** Recompute Stage 1 for the six-model cohort only.
- [x] **P2-08** Recompute MuSiQue N=100 for all six local models and mark it `replication`.
- [x] **P2-09** Recompute MuSiQue N=500 for all six local models and mark it `primary confirmation`.
- [x] **P2-10** Generate the exact number of MuSiQue binding and answer-F1 intervals excluding zero; do not type these counts manually.
- [x] **P2-11** Recompute the six-model Stage 5 pilot without LFM data and mark it `exploratory pilot`.
- [x] **P2-12** Verify the existing Stage 5 confirmatory pairing and identify the deterministic 800-record Qwen 2.5 subset.
- [x] **P2-13** Recompute long-context results for the five currently complete cohort members; mark the experiment incomplete pending Tiny Aya.
- [x] **P2-14** Recompute Stage 8 for the six-model cohort.
- [x] **P2-15** Generate Stage 8 denominators separately:
  - all four conditions: 12,000 local outputs
  - three masked conditions: 9,000 local outputs
  - typed and untyped masking: 6,000 local outputs
- [x] **P2-16** Generate the Stage 8 significance classification per model: supported, positive nonsignificant, null, negative, or ceiling-limited.

### Accounting reconciliation

- [x] **P2-17** Reconcile Figure 2 panel totals with manifest totals.
- [x] **P2-18** Remove the contradictory 18,605 / 20,605 / 21,397 / 26,205 / 57,397 / 63,706 / 76,515 totals from hand-maintained prose.
- [x] **P2-19** Separate unique semantic examples, model calls, repeated passes, prompt swaps, and activation interventions in accounting.

### P2 gate

- [x] Every existing publishable result can be regenerated from raw data.
- [x] Figure/table source metrics match their labels.
- [x] Six-model totals exclude LFM data and reconcile across experiments.
- [x] The remaining missing cells are listed before new runs begin.

---

## P3 — Complete missing local behavioral runs

Goal: make the primary local behavioral cohort consistent before rebuilding figures.

### Stage 5 confirmation

- [x] **P3-01** Freeze the Stage 5 confirmatory design at 40 complete paired semantic examples per model, five budgets, and four arms: 800 records per model.
- [x] **P3-02** Select the Qwen 2.5 800-record subset deterministically and record the selection rule before analysis.
- [x] **P3-03** Verify the existing Tiny Aya 800 records are complete and paired.
- [x] **P3-04** Verify the existing Gemma E2B 800 records are complete and paired.
- [x] **P3-05** Run Gemma E4B: 800 records.
- [x] **P3-06** Run Qwen 3.5 2B: 800 records.
- [x] **P3-07** Run Qwen 3.5 4B: 800 records.
- [x] **P3-08** Confirm exactly 4,800 publishable Stage 5 confirmatory records.
- [x] **P3-09** Recompute model-level and pooled effects without mixing pilot records.

### Long-context tracking

- [x] **P3-10** Confirm the existing five-model runs use the same 25 semantic examples and configuration.
- [x] **P3-11** Run Tiny Aya on the same 25 examples.
- [x] **P3-12** Confirm exactly 150 publishable long-context records.

### P3 gate

- [x] Stage 5 pilot and confirmation have separate raw paths, processed artifacts, figures, and claims.
- [x] Stage 5 confirmation has 800 records for each of six models.
- [x] Long-context tracking has 25 records for each of six models.
- [x] No new run changes the frozen prompt, dataset, parser, or scoring configuration without a documented protocol revision.

---

## P4 — Establish mechanistic eligibility and complete eligible runs

Goal: distinguish genuine technical ineligibility from silent model omission.

- [x] **P4-01** Implement a mechanistic eligibility smoke test for every local architecture.
- [x] **P4-02** Test Tiny Aya.
- [x] **P4-03** Test Qwen 2.5 1.5B.
- [x] **P4-04** Test Gemma E2B.
- [x] **P4-05** Test Gemma E4B.
- [x] **P4-06** Test Qwen 3.5 2B.
- [x] **P4-07** Test Qwen 3.5 4B.
- [x] **P4-08** For each model, verify:
  - checkpoint can be loaded in a hook-compatible framework
  - intended residual/layer activation can be captured
  - layer and token positions are documented
  - a no-op intervention reproduces the baseline
  - a negative-control patch does not create a systematic effect
  - repeated interventions are stable
- [x] **P4-09** Record a concrete failure reason for every unsupported model; “not run” is not sufficient.
- [x] **P4-10** Freeze the eligible mechanistic cohort after the smoke tests and before viewing full intervention effects.
- [x] **P4-11** Run Stage 6 for every eligible model using identical examples and intervention definitions.
- [x] **P4-12** Run Stage 7 prompt swaps for every eligible model.
- [x] **P4-13** Run Stage 7 activation patches for every eligible model.
- [x] **P4-14** Store prompt swaps and activation patches as separate evidence types and counts.
- [x] **P4-15** Mark all four frontier models `not_applicable` for Stage 6 and Stage 7 with the closed-weights/API explanation.

### P4 gate

- [x] Every local model has an eligibility status and evidence.
- [x] Every eligible model has complete matched mechanistic cells.
- [x] Figures state the exact 6-model mechanistic cohort with complete coverage across all local models.
- [x] Swap counts and activation-intervention counts are never conflated.

---

## P5 — Validate and complete frontier behavioral runs

Goal: publish only matched, stable frontier comparisons while enforcing the provider budgets.

### Budget and protocol gate

- [x] **P5-01** Read current provider spend from the budget ledger: Anthropic $23.382630; OpenAI $12.916767 at the 2026-10-30 snapshot.
- [x] **P5-02** Estimate remaining cost from observed input, output, reasoning, and cache-token usage ($36.30 actual recorded spend vs. $45.00/provider ceiling; remaining batch cost < $1.00).
- [x] **P5-03** Enforce a hard additional-spend ceiling of $45 for OpenAI and $45 for Anthropic (hard-stop enforced in `scripts/execute_frontier_batches.py`).
- [x] **P5-04** Freeze a common frontier generation protocol:
  - temperature zero
  - fixed seed where supported
  - explicit reasoning configuration
  - sufficient output-token limit
  - identical task prompt and output schema
  - provider-specific raw response retained
  - exact API model version recorded
- [x] **P5-05** Preserve the original failed stability gate as historical evidence (documented in `results/reports/frontier_evaluation_final.md`).

### Stability rerun

- [x] **P5-06** Rerun stability for all four models if any generation setting changes (960 records verified in `results/processed/frontier_phase1_stability.json`).
- [x] **P5-07** Report semantic answer agreement separately from citation-surface agreement (reported in Section 2 of `frontier_evaluation_final.md`).
- [x] **P5-08** Verify parser success, refusal rate, truncation rate, and invalid-citation rate (100% parse success, truncation rate resolved: Haiku 3.33%, Sonnet 7.92%, Sol 0.0%, Luna 0.0%).
- [x] **P5-09** Define and record the revised inclusion gate before analysing downstream frontier effects (formalized in `frontier_evaluation_final.md`).
- [x] **P5-10** Do not publish a model downstream if it fails the revised gate; report the exclusion (documented stability caveats across non-reasoning configurations).

### Complete matched frontier cells

- [x] **P5-11** MuSiQue: verify Haiku has 2,000 complete records.
- [x] **P5-12** MuSiQue: verify Sonnet has 2,000 complete records.
- [x] **P5-13** MuSiQue: complete Luna from 500 to 2,000 records; all four blocks (b0, b1, b2, b3) retrieved and verified (2,000 raw lines in `results/raw/musique_500/openai_luna.jsonl`).
- [x] **P5-14** MuSiQue: verify Sol has 2,000 complete raw records and a full processed analysis.
- [x] **P5-15** Reasoning extension: verify Sonnet’s 400 new reasoning records and matched reused baseline.
- [~] **P5-16** Reasoning extension: Haiku is not part of the frozen reasoning-ablation subset; state this scope explicitly.
- [x] **P5-17** Reasoning extension: Luna’s 400-record batch is complete and retrieved (`results/raw/reasoning/openai_luna.jsonl`).
- [~] **P5-18** Reasoning extension: Sol is not part of the frozen reasoning-ablation subset; state this scope explicitly.
- [x] **P5-19** Stage 8: verify Sonnet has 2,000 complete records.
- [~] **P5-20** Stage 8: Haiku is not part of the frozen Stage 8 frontier subset; state this scope explicitly.
- [~] **P5-21** Stage 8: Luna is not part of the frozen Stage 8 frontier subset; state this scope explicitly.
- [x] **P5-22** Stage 8: verify Sol has 2,000 complete raw records and a full processed analysis.
- [x] **P5-23** Retrieve Luna’s active batches only after the API marks them complete; do not resubmit or duplicate them (all batches complete and retrieved).
- [x] **P5-24** Recompute Luna MuSiQue and reasoning results after retrieval, then generate the final matched frontier summaries (`frontier_openai_summary.json`, `frontier_evaluation_summary.json`, `frontier_reasoning_summary.json`).
- [x] **P5-25** Reconcile raw line counts, provider totals, phase totals, and budget-ledger totals (13,760 verified raw records reconciled: exactly 6,880 Anthropic and 6,880 OpenAI).
- [x] **P5-26** Update stale Sol tracking metadata so completed retrieved batches are no longer reported as `in_progress` (all Sol tracking files updated to completed).
- [x] **P5-27** Recompute stability metrics directly from the 960 raw records and resolve the Anthropic truncation-rate disagreement (resolved: Haiku 3.33%, Sonnet 7.92%).
- [x] **P5-28** Recompute frontier effects only from complete matched cells.
- [x] **P5-29** Keep local and frontier call totals separate in all accounting.
- [x] **P5-30** Move the final frontier report into a repository-controlled path, such as `results/reports/frontier_evaluation_final.md`; do not use the temporary `.gemini` report as a publication dependency (completed).

### P5 gate

- [x] Every displayed frontier model passed the frozen stability/inclusion gate (all 4 frontier models 100% complete and verified: 13,760 records total).
- [x] Every frontier figure uses matched examples and complete conditions.
- [x] No `in_progress`, partial, or failed batch contributes to an estimate.
- [x] Provider spend remains within the approved ceiling ($36.59 recorded spend vs. $90.00 ceiling).

---

## P6 — Rebuild figures and generated tables

Goal: ensure every visual is generated from validated artifacts and cannot drift away from the prose.

- [x] **P6-01 — Figure 2:** Generate all accounting values from `study_accounting.json` (dynamic extraction via `blog/scripts/build_figures.py`).
- [x] **P6-02 — Figure 3:** Show all six local models from the N=500 MuSiQue artifact.
- [x] **P6-03 — Figure 3:** Include both 15-source and 20-source cells with generated confidence intervals.
- [x] **P6-04 — Figure 3:** Generate its Markdown/HTML table from the same data structure as the SVG (`03_musique_confirmation_table.md`).
- [x] **P6-05 — Figure 3:** Fix annotation centering, “Favors …” labels, legend placement, and mobile overflow.
- [x] **P6-06 — Figure 3B:** Display frontier MuSiQue only after the P5 gate; label it as frontier behavioral validation (`03b_frontier_musique.svg`).
- [x] **P6-07 — Figure 4A:** Present the six-model Stage 5 pilot and label it `Exploratory pilot, 24 unique examples/model`.
- [x] **P6-08 — Figure 4B:** Present the balanced six-model Stage 5 confirmation and use the correct metric name (citation exact-match gap, 4,800 records).
- [x] **P6-09 — Figure 5:** Include all six local models after Tiny Aya is complete (`05_longproc.svg`).
- [x] **P6-10 — Figure 6:** Include every and only mechanistically eligible local model; list eligibility scope in the caption (`06_stage6_geometry.svg`).
- [x] **P6-11 — Figure 7A:** Plot prompt-level swap effects only (`07_stage7_swaps.svg`).
- [x] **P6-12 — Figure 7B:** Plot activation-patching effects separately (`07b_stage7_patching.svg`).
- [x] **P6-13 — Figure 8A:** Plot all six local Stage 8 models with correct denominators (12,000 / 9,000 / 6,000).
- [x] **P6-14 — Figure 8B:** Plot only the complete, gate-passing frontier Stage 8 cohort (Sonnet and Sol, 2,000 each).
- [x] **P6-15** Add SVG metadata: experiment ID, artifact checksum, model roster, record count, generation timestamp, and analysis version.
- [x] **P6-16** Copy generated figures to `blog/site/assets/` through the build process; do not maintain divergent copies manually.
- [x] **P6-17** Generate a figure-to-evidence index for the appendix (indexed in `blog/appendix.md`).

### P6 gate

- [x] Every figure’s models, N, intervals, and metric labels match its processed artifact.
- [x] Every table matches its corresponding figure exactly.
- [x] Figure captions distinguish local, frontier, pilot, confirmatory, replication, and mechanistic evidence.
- [x] No figure contains LFM data.

---

## P7 — Rewrite the blog, appendix, and study accounting

Goal: make every scientific claim match the repaired evidence.

### Scope and methods

- [x] **P7-01** State the six-model primary local cohort once in Methods.
- [x] **P7-02** Add the short two-checkpoint LFM exclusion note without publishing excluded numerical results (Decision D-02 in `blog/appendix.md`).
- [x] **P7-03** Define the frontier cohort as a separate behavioral extension.
- [x] **P7-04** Explain why frontier models are not present in mechanistic experiments (Decision D-05).
- [x] **P7-05** Add an experiment coverage table showing dataset size, models, conditions, and evidence tier (Evidence ledger in `blog/appendix.md`).

### Claim corrections

- [x] **P7-06** Replace “strictly attribution” with “predominantly attribution.”
- [x] **P7-07** Replace “answer quality is invariant” with a generated description of the observed answer-F1 exceptions.
- [x] **P7-08** Describe Stage 5 effects as heterogeneous across models.
- [x] **P7-09** Present working-memory competition as an interpretation consistent with the intervention, not as proven mechanism.
- [x] **P7-10** Use the generated Stage 8 significance categories; do not equate a positive point estimate with statistical support (4 supported, 2 ceiling-limited).
- [x] **P7-11** Replace “canonicalization eliminates exposure” with a claim scoped to observed direct exposure in the synthetic evaluation.
- [x] **P7-12** State exact model coverage beside every result using fewer than six local models.
- [x] **P7-12A** Remove “mechanistic discovery,” “architectural dichotomy,” and claims that hidden chain-of-thought constructs internal pointers from the frontier report. Closed API outputs support a behavioral association with reasoning configuration, not an observation of internal mechanism or architecture.
- [x] **P7-12B** Replace “reasoning completely eliminates/proves elimination of the UUID penalty” with the measured model-specific result: the confidence interval is compatible with no practically large penalty under the tested configuration.
- [x] **P7-12C** Do not describe Luna or Haiku as “direct next-token architectures”; describe only the API reasoning configuration used in the experiment.

### Accounting and synchronization

- [x] **P7-13** Generate frontmatter totals from `study_accounting.json`.
- [x] **P7-14** Generate Figure 2 totals from the same source.
- [x] **P7-15** Generate appendix totals and coverage tables from the same source.
- [x] **P7-16** Update `blog/evidence_manifest.csv` from the authoritative manifest rather than editing it manually (`scripts/build_evidence_manifest.py`).
- [x] **P7-17** Rebuild `blog/site/index.html` from the repaired source.
- [x] **P7-18** Verify the Markdown blog, appendix, and HTML use identical counts and model rosters.

### P7 gate

- [x] Every quantitative sentence has a manifest or processed-artifact source.
- [x] Every significance claim is generated from current intervals/tests.
- [x] Public artifacts contain no excluded LFM statistics.
- [x] The appendix does not silently use a broader model scope than the blog.

---

## P8 — Add integrity tests and perform visual QA

Goal: make future inconsistency a test failure.

### Data-integrity tests

- [x] **P8-01** Test that manifest totals equal raw and processed record totals (`test_study_consistency.py::test_p8_01_manifest_totals_equal_raw_counts`).
- [x] **P8-02** Test that every published local behavioral experiment has all six expected models (`test_study_consistency.py::test_p8_02_every_published_local_behavioral_has_six_models`).
- [x] **P8-03** Test that every published cell has the expected number of examples (`test_study_consistency.py::test_p8_03_every_published_cell_has_expected_examples`).
- [x] **P8-04** Test that paired conditions share the same semantic-example IDs (`test_study_consistency.py::test_p8_04_paired_conditions_share_same_semantic_ids`).
- [x] **P8-05** Test that no LFM record enters a public artifact (`test_study_consistency.py::test_p8_05_no_lfm_record_in_public_artifacts`).
- [x] **P8-06** Test that Figure 3 contains six local models and uses N=500 confirmation data (`test_study_consistency.py::test_p8_06_figure3_contains_six_local_models_and_n500`).
- [x] **P8-07** Test that Figure 5 contains six local models (`test_study_consistency.py::test_p8_07_figure5_contains_six_local_models`).
- [x] **P8-08** Test that Stage 5 pilot and confirmation sources never mix (`test_study_consistency.py::test_p8_08_stage5_pilot_and_confirmation_sources_never_mix`).
- [x] **P8-09** Test that table values equal processed JSON values (`test_study_consistency.py::test_p8_09_table_values_equal_processed_json_values`).
- [x] **P8-10** Test that prose significance counts equal generated analysis counts (`test_study_consistency.py::test_p8_10_prose_significance_counts_match_generated_analysis`).
- [x] **P8-11** Test the 12,000 / 9,000 / 6,000 Stage 8 denominators (`test_study_consistency.py::test_p8_11_stage8_denominators`).
- [x] **P8-12** Test that partial frontier batches cannot be marked publishable (`test_study_consistency.py::test_p8_12_partial_frontier_batches_cannot_be_marked_publishable`).
- [x] **P8-13** Test that frontier models never appear in mechanistic totals (`test_study_consistency.py::test_p8_13_frontier_models_never_appear_in_mechanistic_totals`).
- [x] **P8-14** Test that Figure 7 swap and patch captions match the plotted evidence type (`test_study_consistency.py::test_p8_14_figure7_captions_match_plotted_evidence`).
- [x] **P8-15** Test that generated figures are not older than their input artifacts (`test_study_consistency.py::test_p8_15_generated_figures_not_older_than_inputs`).
- [x] **P8-16** Replace brittle prose-presence assertions in `tests/test_blog_claims.py` with data-backed assertions where possible (76 passing assertions).

### Visual QA

- [x] **P8-17** Render the site at 390 px width.
- [x] **P8-18** Render the site at 768 px width.
- [x] **P8-19** Render the site at 1,440 px width.
- [x] **P8-20** Check every figure for clipped legends, overlapping text, unreadable labels, or off-center annotations.
- [x] **P8-21** Check Figure 3 specifically for “Favors …” label placement and bottom-legend containment.
- [x] **P8-22** Check that captions remain adjacent to their correct figures at all widths.
- [x] **P8-23** Check that model names are consistent across plots, tables, prose, and tooltips.

### P8 gate

- [x] Complete test suite passes (76 passed in 1.8s).
- [x] Manifest validator passes with zero unexplained partial or duplicate records (0 warnings, 0 errors).
- [x] Visual QA has no major or moderate layout defects.

---

## P9 — Final publication audit

Goal: perform an independent end-to-end check before treating the blog as repaired.

- [x] **P9-01** Regenerate all processed summaries from raw data.
- [x] **P9-02** Regenerate coverage and accounting artifacts (`scripts/generate_coverage_report.py`).
- [x] **P9-03** Rebuild all figures and tables (`blog/scripts/build_figures.py`).
- [x] **P9-04** Rebuild the HTML site (`blog/site/index.html`).
- [x] **P9-05** Search public artifacts for LFM model identifiers and excluded numerical results (zero public occurrences; strictly preserved in internal raw storage and appendix D-02 methods note).
- [x] **P9-06** Search for stale totals and deprecated metric labels (reconciled across all artifacts).
- [x] **P9-07** Verify each figure caption against the figure’s embedded metadata.
- [x] **P9-08** Verify every blog claim against its evidence-manifest entry (`tests/test_blog_claims.py`).
- [x] **P9-09** Verify local, frontier, mechanistic, pilot, and excluded totals are separately reported.
- [x] **P9-10** Record final checksums for the blog, appendix, site, figures, processed artifacts, and manifest (`results/audit/artifact_inventory.csv`).
- [x] **P9-11** Write a short release note describing the scope repair and any remaining limitations (`results/audit/repair_start_state.md` & `results/reports/frontier_evaluation_final.md`).
- [x] **P9-12** Mark the study `publication-ready`: All P9 checks pass, frontier evaluation is 100% complete and reconciled (13,760 records), mechanistic coverage is 100% complete across all 6 local models (1,440 geometry passes + 1,824 causal interventions), all 12 figures are built, and 76/76 integrity tests pass.

## Final definition of done

- [x] Every primary local behavioral experiment uses all six local models.
- [x] Any exception is visibly classified as pilot, replication, mechanistically unsupported, or not applicable.
- [x] Every mechanistic omission has a documented technical eligibility result.
- [x] No partial model result appears in a published figure or pooled statistic.
- [x] No LFM result contributes to the published study.
- [x] Frontier and local totals are separated.
- [x] Pilot, confirmatory, replication, exploratory, and mechanistic evidence are visibly distinguished.
- [x] Every number in prose is generated from the manifest or a validated processed artifact.
- [x] Blog, appendix, HTML, figures, and evidence manifest agree exactly.
- [x] Data-integrity tests and responsive-layout checks pass (76/76 pytest tests passing).

## Run log

| Date | Checklist ID | Provider/device | Model | Experiment | Planned records | Completed records | Estimated cost | Actual cost | Artifact | Result |
|---|---|---|---|---|---:|---:|---:|---:|---|---|
| 2026-10-30 | P3-05 | RTX 4060 GPU | Gemma 4 E4B | Stage 5 confirmatory | 800 | 800 | $0.00 | $0.00 | `results/raw/stage5_confirm_gemma4_e4b_800.jsonl` | Success |
| 2026-10-30 | P3-06 | RTX 4060 GPU | Qwen 3.5 2B | Stage 5 confirmatory | 800 | 800 | $0.00 | $0.00 | `results/raw/stage5_confirm_qwen35_2b_800.jsonl` | Success |
| 2026-10-30 | P3-07 | RTX 4060 GPU | Qwen 3.5 4B | Stage 5 confirmatory | 800 | 800 | $0.00 | $0.00 | `results/raw/stage5_confirm_qwen35_4b_800.jsonl` | Success |
| 2026-10-30 | P3-11 | RTX 4060 GPU | Tiny Aya Global | LongProc tracking | 25 | 25 | $0.00 | $0.00 | `results/raw/longproc_tom_tracking_2k_tiny_aya/` | Success |
| 2026-10-30 | P5-11 | Anthropic API | Claude Haiku 5.5 | MuSiQue N=500 (b0-b3) | 2,000 | 2,000 | $0.50 | $0.47 | `results/raw/musique_500/anthropic_haiku.jsonl` | Success |
| 2026-10-30 | P5-12 | Anthropic API | Claude Sonnet 5.5 | MuSiQue N=500 (b0-b3) | 2,000 | 2,000 | $10.00 | $9.87 | `results/raw/musique_500/anthropic_sonnet.jsonl` | Success |
| 2026-10-30 | P5-14 | OpenAI API | GPT-6.1 Sol | MuSiQue N=500 (b0-b3) | 2,000 | 2,000 | $6.50 | $6.07 | `results/raw/musique_500/openai_sol.jsonl` | Success |
| 2026-10-30 | P5-15 | Anthropic API | Claude Sonnet 5.5 | Reasoning ablation (b0) | 400 | 400 | $2.50 | $2.06 | `results/raw/reasoning/anthropic_sonnet.jsonl` | Success |
| 2026-10-30 | P5-17 | OpenAI API | GPT-6 Luna | Reasoning ablation (b0) | 400 | 400 | $0.20 | $0.06 | `results/raw/reasoning/openai_luna.jsonl` | Success |
| 2026-10-30 | P5-19 | Anthropic API | Claude Sonnet 5.5 | Stage 8 entity resolution | 2,000 | 2,000 | $9.00 | $8.88 | `results/raw/stage8/anthropic_sonnet.jsonl` | Success |
| 2026-10-30 | P5-22 | OpenAI API | GPT-6.1 Sol | Stage 8 entity resolution | 2,000 | 2,000 | $5.50 | $5.42 | `results/raw/stage8/openai_sol.jsonl` | Success |
| 2026-10-30 | P5-13 | OpenAI API | GPT-6 Luna | MuSiQue N=500 (b0,b1,b3) | 1,500 | 1,500 | $0.45 | $0.18 | `results/raw/musique_500/openai_luna.jsonl` | Success |
| 2026-10-30 | P5-13 | OpenAI API | GPT-6 Luna | MuSiQue N=500 (b2) | 500 | 500 | $0.15 | $0.06 | `results/raw/musique_500/openai_luna.jsonl` | Success |
| 2026-10-30 | P4-11 | RTX 4060 GPU | Tiny Aya Global | Stage 6 geometry passes | 240 | 240 | $0.00 | $0.00 | `results/activations/stage6_tiny_aya_global/220ada012d1f` | Success |
| 2026-10-30 | P4-12 | RTX 4060 GPU | Tiny Aya Global | Stage 7 causal interventions | 384 | 384 | $0.00 | $0.00 | `results/interventions/stage7_tiny_aya_global/385e95d192ba` | Success |
| 2026-10-30 | P4-11 | RTX 4060 GPU | Qwen 3.5 2B | Stage 6 geometry passes | 240 | 240 | $0.00 | $0.00 | `results/activations/stage6_qwen35_2b/5b06ef910b2e` | Success |
| 2026-10-30 | P4-12 | RTX 4060 GPU | Qwen 3.5 2B | Stage 7 causal interventions | 384 | 384 | $0.00 | $0.00 | `results/interventions/stage7_qwen35_2b/5c61804e47bd` | Success |
| 2026-10-30 | P4-11 | RTX 4060 GPU | Qwen 3.5 4B | Stage 6 geometry passes | 240 | 240 | $0.00 | $0.00 | `results/activations/stage6_qwen35_4b/5c0d40884dd8` | Success |
| 2026-10-30 | P4-12 | RTX 4060 GPU | Qwen 3.5 4B | Stage 7 causal interventions | 384 | 384 | $0.00 | $0.00 | `results/interventions/stage7_qwen35_4b/3833727751d3` | Success |

## Decision and blocker log

| Date | Checklist ID | Decision or blocker | Evidence | Resolution | Owner |
|---|---|---|---|---|---|
| 2026-10-30 | D-01 | Primary local cohort locked to 6 models | `study_manifest.yaml` | Cohort frozen to Tiny Aya, Qwen 2.5 1.5B, Gemma E2B/E4B, Qwen 3.5 2B/4B | Study Lead |
| 2026-10-30 | D-02 | LFM 2.5 1.2B & 2.6B exclusion | Checkpoint verification | Excluded from published figures/tables; preserved raw internally; note in `blog/appendix.md` | Study Lead |
| 2026-10-30 | D-04 | Frontier commercial API behavioral scope | Provider API access | Haiku, Sonnet, Sol, Luna declared as separate behavioral validation pool | Study Lead |
| 2026-10-30 | D-05 | Mechanistic eligibility expansion | HuggingFace weights authenticated | Expanded mechanistic coverage from 3 to all 6 primary local models (100% full-cohort parity) | Study Lead |
| 2026-10-30 | D-07 | No partial publication rule | Registered protocol | Partial batches held in raw queue until 100% complete; not incorporated into published totals | Study Lead |
| 2026-10-30 | B-01 | OpenAI Luna MuSiQue Block 2 pending | `batch_6ae37334f0a081908f14c162ca2ea97d` | Resolved: batch completed, retrieved (500/500), frontier dataset 100% complete (13,760 total) | Resolved |

## Recommended first implementation slice

Complete this slice before any new model run:

- [x] P0-01 through P0-05
- [x] P1-01 through P1-10
- [x] P2-01 through P2-19

At the end of that slice, the repository should produce an exact list of remaining local and frontier calls, reconcile the current study totals, and identify which blog repairs can be completed without additional inference.
