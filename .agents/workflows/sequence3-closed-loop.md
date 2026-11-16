# Sequence 3 Closed-Loop Experiment Workflow

Execute this workflow as an autonomous engineering-and-science loop. Do not merely
write a plan. Inspect the repository, implement the smallest correct change, test
it, run the appropriate experiment, inspect the resulting artifact, diagnose any
failure, and repeat until the relevant completion contract below is satisfied.

Default mode is `THROUGH_VALIDATION`. Do not read or run
`data/circuit/confirmation_n80.jsonl` in this mode. The only permitted pre-gate
operations on that file are checking its existence and verifying its SHA-256
against `data/circuit/dataset_manifest.json`.

Enter `CONFIRMATION` mode only when the user has supplied the exact phrase:

```text
CONFIRMATION AUTHORIZED
```

Use Gemini 3.8 Flash High when selectable. Read `AGENTS.md` completely before any
action and obey it throughout.

## Objective

Produce a scientifically valid, reproducible Sequence 3 investigation that:

1. repairs and reruns the invalid Sequence 2 position/layer/control logic;
2. localizes a citation-routing head set only where a corrected whole-mixer
   positive control exists;
3. tests a post-evidence causal source-handle subspace;
4. tests the upstream writer-to-router path when supported by the earlier gates;
5. connects the mechanism to free-generation citation behavior when supported;
6. treats a well-measured null result as a valid result rather than tuning until
   a preferred finding appears.

The target scientific distinction is binding/handle construction (`B`) versus
citation serialization/continuation (`F`). Do not call a component a binding
head merely because it changes the final citation token.

## Non-negotiable constraints

- Preserve all pre-existing user changes. Record the initial `git status` and do
  not revert, overwrite, or format unrelated files.
- Never modify or overwrite `*pilot12*` artifacts.
- Never alter historical raw result files to make them agree with new code.
- Do not edit `results/circuit/circuit_preregistration.json`. It is a historical,
  hashed preregistration.
- Create a new immutable `results/circuit/sequence3_preregistration.json` and add
  it to the manifest under a new key. Preserve the old preregistration entry.
- Keep discovery, validation, and confirmation examples strictly disjoint.
- All causal effect intervals must be paired cluster-bootstrap 95% confidence
  intervals clustered by `example_id`, with exactly `B=1000` replicates.
- Do not invent p-values, significance labels, or post-hoc thresholds.
- Do not change candidate-selection rules after looking at validation results.
- Do not change hypotheses, rank, head set, intervention, metric, or exclusion
  rule after confirmation is authorized or accessed.
- Never hide a null, failed condition, skipped example, OOM, NaN, or alignment
  failure. Emit counts and reasons in machine-readable artifacts.
- A scientific null is not an engineering failure and must not trigger tuning.
- Do not weaken, delete, skip, or rewrite a failing test simply to make it pass.
- Use `.venv/bin/python` and `.venv/bin/pytest tests/`.
- Do not edit the blog during this workflow.

## Persistent loop state

Create and continuously update:

```text
results/circuit/sequence3_work/loop_state.json
```

Write updates atomically. It must contain at least:

```json
{
  "schema_version": 1,
  "run_id": "UTC timestamp or stable UUID",
  "mode": "THROUGH_VALIDATION",
  "phase": "BASELINE",
  "status": "running",
  "baseline_commit": null,
  "initial_git_status": [],
  "dataset_hashes": {},
  "historical_artifact_hashes": {},
  "sequence3_preregistration_sha256": null,
  "completed_gates": [],
  "attempts_by_failure_signature": {},
  "commands": [],
  "modified_files": [],
  "confirmation_authorized": false,
  "confirmation_accessed": false,
  "confirmation_completed": false,
  "last_observation": null,
  "next_action": null,
  "terminal_outcome": null
}
```

Before every phase, reload this file and verify the datasets and frozen artifacts
still have their recorded hashes. Resume from the first incomplete gate. Never
rerun a completed expensive experiment merely because the conversation restarted.

Store failed or partial heavy-run output under:

```text
results/circuit/sequence3_work/failed_runs/<run_id-or-attempt>/
```

Do not overwrite a successful artifact with a retry.

## The engineering loop

For every phase, use this exact cycle:

1. **Observe**: read current state, relevant code, tests, logs, output schemas,
   hashes, and resource availability.
2. **Specify**: state the current gate, expected invariant, exact command, and
   machine-checkable success condition before changing or running anything.
3. **Change minimally**: patch only the smallest cause supported by evidence.
4. **Targeted verification**: run the narrowest new or existing regression tests.
5. **Smoke run**: use synthetic fixtures or at most one discovery example. Never
   use validation or confirmation for smoke testing.
6. **Phase verification**: run the phase command on the intended split and inspect
   output content, not just exit code.
7. **Repository verification**: run `.venv/bin/pytest tests/` before closing every
   implementation phase and at final completion.
8. **Record**: update loop state, command provenance, hashes, exclusions, and the
   next action.
9. **Decide**:
   - pass -> advance exactly one gate;
   - engineering failure -> classify, repair, and retry;
   - scientific null -> record the null and follow the preregistered branch;
   - protected-data or design ambiguity -> stop at the human gate.

### Retry policy

Classify failures before retrying:

- `DETERMINISTIC_CODE`: traceback, assertion, schema error, wrong tensor shape.
  Reproduce with a minimal test, patch, rerun targeted test, smoke test, then the
  failed command.
- `SEMANTIC_ALIGNMENT`: wrong token, position, source, donor, layer, or contrast.
  Add a regression test that fails before the patch and proves the semantic
  invariant after it. Do not proceed with only an exit-code check.
- `RESOURCE_OOM`: preserve examples, estimand, precision policy, and seed. Reduce
  microbatch size, store donor activations on CPU, stream rows, or add checkpoint
  and resume. Do not reduce sample size to obtain a result.
- `TRANSIENT_INFRASTRUCTURE`: retry the identical command at most twice. Preserve
  logs. Do not change scientific settings.
- `CORRUPT_OR_PARTIAL_OUTPUT`: quarantine the artifact, determine whether any row
  was completed, then resume into a new file with deduplication by a stable row
  key. Never silently concatenate duplicates.
- `SCIENTIFIC_NULL`: do not retry. Record the point estimate, CI, case count, and
  the branch it disables.
- `CONFIRMATION_FAILURE`: if no complete confirmation rows were produced, repair
  the infrastructure without inspecting outcomes and rerun the exact frozen
  command. If any complete outcome rows were produced, do not alter the plan;
  resume only with identical code/config or stop for human review.

After three occurrences of the same deterministic failure signature, stop making
near-identical patches. Re-read the surrounding architecture, formulate a new
root-cause hypothesis, and try at most two materially different repairs. If still
blocked, produce a blocker report with reproduction command, logs, attempted
fixes, affected gate, and the smallest human decision required.

## Phase 0 — Baseline and provenance gate

1. Read `AGENTS.md`, the existing circuit runners/analysers/tests, dataset
   manifest, and both current Sequence 2 artifacts.
2. Record initial `git status`, current commit if available, Python/Torch/CUDA
   versions, GPU memory, dataset hashes, historical preregistration hash, and all
   `*pilot12*` hashes.
3. Run `.venv/bin/pytest tests/` without editing anything.
4. Verify the three split ID sets are pairwise disjoint and their hashes agree
   with the manifest.

Pass only when the baseline suite passes and provenance checks are green. Existing
unrelated dirty files are not a failure; record and avoid them.

## Phase 1 — Sequence 2R semantic repair gate

Add regression tests first, then repair the implementation. The tests must prove:

1. **Distinguishing-token logit position**
   - For clean and donor labels independently, find the first distinguishing token
     index `d`.
   - Evaluate that token at `target_positions[d] - 1`, not always before the first
     citation token.
   - Cover a structured label such as `[1]` versus `[2]`, a compact label, and a
     multi-token UUID-like label.

2. **One-based scientific layer convention**
   - Scientific layer `L` maps to `layers[L - 1]`.
   - Store both the one-based public layer number and zero-based stack index in
     every result row.
   - Reject out-of-range and ambiguous layer inputs.

3. **Order-permutation estimand**
   - Preserve a frozen clean-label versus fixed-distractor contrast across clean
     and order-permuted prompts.
   - Never call `find_first_distinguishing_index` on identical targets and then
     compare unrelated tokens.
   - Emit an explicit invariant showing that content-label pairings are unchanged
     while passage slots changed.

4. **Question-swap grounding**
   - Every alternative question has exactly one gold supporting source.
   - The expected answer is entailed by that source.
   - Do not select an arbitrary non-relevant source or fabricate a generic answer.
   - If the dataset lacks a valid alternative, mark the row ineligible with a
     reason; do not invent one.

5. **Semantic position alignment**
   - Align source-handle/evidence boundaries semantically when clean and donor
     labels have unequal token counts.
   - Never silently drop an example because two raw spans differ in length.
   - Emit alignment diagnostics and exclusion reasons.

6. **Autoregressive causal interpretation**
   - Source-label states that occur before passage evidence may be described as
     handle-identity states, not evidence-label binding states.
   - Binding construction targets must occur after both label and evidence have
     entered causal context.

Run targeted tests, one-example smoke tests for each format, then the complete
test suite. Do not run a full GPU experiment until all invariants pass.

## Phase 2 — Corrected Sequence 2R execution and eligibility gate

Run the corrected discovery experiment across structured, compact, and UUID-like
conditions. Use deterministic seeds, resumable row output, inference mode, and
explicit schema/version metadata.

For every layer x semantic position x component x condition, report:

- paired case count and excluded count with reasons;
- mean absolute causal shift;
- paired cluster-bootstrap 95% CI by `example_id`, `B=1000`;
- vocabulary KL at the actual evaluated citation position;
- clean and donor label/token/position diagnostics;
- pooled estimate plus condition-specific estimates.

Do not reuse the old `+0.701` Stage 7B estimate as the position-specific Sequence
2R whole-mixer positive control.

Eligibility branches:

- A head screen is eligible only at a layer-position whose corrected whole
  attention mixer has a nonzero effect in the predicted direction with a paired
  bootstrap CI not spanning zero and no semantic-alignment failure.
- A residual subspace experiment is eligible only at a post-evidence position
  with a corrected residual-stream causal effect and adequate aligned case count.
- L14/L20 source-label heads are not eligible merely because a residual patch is
  large. If their whole mixers remain null, record that null and skip that head
  screen.
- If no head target is eligible, this is a valid terminal result for head
  localization. Continue only with an independently eligible post-evidence
  residual-subspace branch.
- If neither branch is eligible, stop with a valid negative Sequence 3 outcome;
  do not search extra layers/positions post hoc.

## Phase 3 — Freeze the new preregistration

Before any head or subspace discovery screen, create
`results/circuit/sequence3_preregistration.json`. Include:

- input artifact hashes and code commit;
- eligible layer-position-component targets from the mechanical gate above;
- one-based/zero-based layer convention;
- semantic token/position definitions;
- discovery ranking rule;
- validation selection rule and allowed `K`/rank grid;
- frozen confirmation metric and contrasts;
- paired cluster-bootstrap procedure with `B=1000`;
- recovery estimator defined as a jointly bootstrapped ratio of aggregate paired
  means, with a prespecified denominator-magnitude guard;
- necessity, sufficiency, specificity, minimality, and behavioral metrics;
- ablation/intervention definitions;
- exclusion and failure-handling rules;
- all branch conditions and terminal null outcomes;
- the exact confirmation command template, without executing it.

Add a new manifest key and test its SHA-256. Never replace the existing
`preregistration` key. Once hashed, treat Sequence 3 preregistration as immutable.
If a genuine implementation defect is found later, create an amendment file with
timestamp, reason, affected analyses, and old/new hashes; never silently edit.

## Phase 4 — Sequence 3A citation-routing head loop

Run only for eligible whole-mixer targets.

Implementation invariants:

- Patch pre-`o_proj` query-head slices using the model's actual query-head count
  and head dimension; do not assume them without asserting configuration values.
- An identity patch leaves logits equal within numerical tolerance.
- Patching all query-head slices equals patching the complete `o_proj` input.
- Concatenated/projected head slices reconstruct the unpatched mixer output within
  tolerance.
- The evaluated logit position is the corrected citation distinguishing token.

Discovery:

- Score every head using the preregistered absolute causal effect.
- Report CIs descriptively; do not use `z >= 1.5` or an invented significance
  threshold for discovery selection.
- Apply the frozen ranking rule and carry only its candidates to validation.

Validation:

- Choose `K` only from the preregistered grid and rule.
- Compare the candidate set against many size-`K` random head subsets using the
  same examples and paired bootstrap.
- Measure candidate-set sufficiency and necessity.
- Make matched-mean or matched-resampling ablation primary; zero ablation is a
  robustness analysis. Record activation-norm shift.
- For `K <= 4`, evaluate all `2^K` subsets and define exact minimality as no proper
  subset meeting the frozen faithfulness/specificity criterion. For larger `K`,
  use greedy pruning and label it approximate minimality.
- Freeze the selected set before confirmation.

If the selected set does not beat the frozen random-subset control or fails the
specificity rule, report no validated compact router. Do not substitute another
set after inspecting validation.

## Phase 5 — Sequence 3B post-evidence causal subspace loop

Run only at preregistered eligible post-evidence residual positions.

- Fit donor-clean counterfactual-difference bases on discovery only.
- Keep discovery, validation, and confirmation transforms completely separate.
- Center within condition or implement the preregistered shared-versus-specific
  decomposition so surface morphology cannot dominate the basis unnoticed.
- Select rank on validation using only the frozen grid/rule.
- Compare with equal-rank random bases, norm-matched random directions, shuffled
  donor pairing, and the orthogonal complement.
- Report retained variance separately from causal recovery.
- Test cross-format transfer in a matrix, not only a pooled estimate.
- Freeze basis-construction code, rank, and intervention strength before
  confirmation.

Call this a `counterfactual-difference subspace` unless causal controls justify a
stronger name. Failure of a linear basis does not establish high dimensionality;
report it as failure of the tested linear subspace.

## Phase 6 — Writer-to-router and behavioral bridge

Run path localization only if both a validated post-evidence subspace and a
validated routing receiver exist.

- Search only the preregistered upstream components/positions.
- Use a cheap attribution/path screen on discovery if specified, then exact path
  patching for frozen candidates on validation.
- Test whether the post-evidence subspace mediates the upstream-component to
  citation-router effect.
- Preserve the distinction between writing a handle, transporting it, and
  serializing it.

For the behavioral bridge, evaluate free generation under clean/corrupt prompts
and frozen interventions. Report separately:

- answer correctness;
- citation-source correctness;
- citation precision/recall where defined;
- citation syntax validity;
- answer-citation consistency;
- wrong-source, omitted-citation, and spurious-citation error counts.

The strongest supported claim is an intervention that changes citation behavior
in the predicted direction while preserving answer correctness. If that does not
occur, report the dissociation; do not optimize intervention strength on
confirmation.

## Phase 7 — Confirmation gate and one-shot execution

In default `THROUGH_VALIDATION` mode, stop here and produce a gate report containing:

- full test result;
- git diff summary;
- dataset and preregistration hashes;
- validated frozen head set, rank, basis construction, metrics, and commands;
- validation estimates and CIs;
- skipped branches and scientific nulls;
- estimated GPU/runtime requirements;
- exact confirmation command;
- statement that confirmation has not been read or run.

Ask only for the exact authorization phrase `CONFIRMATION AUTHORIZED`.

After authorization:

1. Set `confirmation_authorized=true` before accessing rows.
2. Reverify all hashes, complete tests, frozen configuration, and confirmation
   command against preregistration.
3. Set `confirmation_accessed=true` immediately before the first command that
   loads confirmation examples.
4. Run the frozen confirmation command once with checkpoint/resume enabled.
5. Permit retries only under the `CONFIRMATION_FAILURE` rules above.
6. Analyze with the frozen metric and `B=1000` cluster bootstrap.
7. Report results regardless of direction or CI.

## Phase 8 — Final audit and definition of done

The workflow is `DONE` only when all applicable statements are true:

- All repository tests pass.
- All new semantic regression tests pass.
- Dataset splits are disjoint and manifest hashes are correct.
- Historical preregistration and `*pilot12*` hashes are unchanged.
- Every output has schema version, code/config provenance, split, seed, case counts,
  exclusion reasons, and stable row identifiers.
- Sequence 2R uses correct distinguishing-token positions and one-based layers.
- Every executed Sequence 3 branch passed its prerequisite positive-control gate.
- Discovery selected; validation chose/froze; confirmation tested exactly once.
- All causal CIs use paired `example_id` cluster bootstrap with `B=1000`.
- Random, shuffled, ablation, specificity, and cross-format controls required by
  the applicable preregistered branch are present.
- Nulls and disabled branches are explicitly reported.
- No blog or historical result file was edited.
- A final reproducibility walkthrough exists at
  `results/circuit/SEQUENCE3_WALKTHROUGH.md`.
- `loop_state.json` has status `done` and a terminal outcome chosen from:
  `validated_mechanism`, `validated_partial_mechanism`, or
  `valid_negative_result`.

The walkthrough must include exact commands, changed files, test evidence, result
artifact links, hashes, limitations, and the narrowest scientifically supported
claim. Do not claim completion based only on code compiling or commands exiting 0.

## Final response contract

Lead with the terminal scientific outcome. Then report:

1. which gates passed or terminated as null;
2. the frozen confirmation result if authorized;
3. exact test count/status;
4. created/modified files;
5. protected artifacts verified unchanged;
6. remaining limitations or the single blocker requiring human action.

If stopped at the confirmation gate, do not say the project is done. Say it is
`READY_FOR_CONFIRMATION` and request the exact authorization phrase.
