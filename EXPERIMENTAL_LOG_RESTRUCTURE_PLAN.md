# Experimental Log UI Restructure Plan

## Objective

Replace the current long-form engineering blog with a dense, multi-page
experimental log. The new site should make the research program easy to scan at
the top level and make every experimental question easy to inspect in depth.

This is a presentation and information-architecture change only. Existing run
data, processed results, analysis outputs, experiment code, configurations, and
figure-generation logic are read-only inputs to this work.

## Current-state diagnosis

The public UI currently concentrates the entire narrative in
`blog/site/index.html` (717 lines) and supports it with a single large stylesheet
and one small interaction script. The article mixes motivation, experiment
design, results, caveats, production guidance, and reproduction details into a
single reading path.

The repository already has a better underlying evidence structure than the UI:

- `blog/evidence_manifest.csv` separates the evidence into 19 run families;
- the main article describes nine numbered stages plus supporting controls and
  the LongProc reality check;
- `blog/appendix.md` contains definitions, full tables, provenance, and
  reproduction details;
- `FINDINGS*.md` and checked-in processed/analysis artifacts are the source of
  truth for each study family;
- the existing SVGs already map cleanly to specific experimental questions.

The redesign should expose that structure without creating a separate page for
every model-specific run or processed file.

## Product decision: organize by experimental question

The primary unit in the UI will be an **experiment page**, not a blog chapter,
model, or artifact. Scaled runs, confirmatory cohorts, frontier extensions, and
sensitivity checks will appear as named study blocks within the relevant
experiment page. Each study block will have its own anchor so it can still be
linked directly.

This gives readers a compact set of stable pages while preserving traceability
to all rows in the evidence manifest.

## Target information architecture

### 1. Landing page: the research program at a glance

Route: `blog/site/index.html`

The landing page should contain:

1. **Motivation** — backend identifiers are transport keys, not necessarily good
   model interfaces.
2. **Problem statement** — distinguish transport cost, source binding, reasoning
   capacity, representation geometry, causal effects, privacy/exposure, and the
   software trust boundary.
3. **Research thesis and falsifiers** — state the narrow claim and what evidence
   would disconfirm it.
4. **TL;DR evidence summary** — a compact set of evidence-backed conclusions,
   with clear qualification rather than one oversized headline count.
5. **Experiment directory** — the main navigation surface, showing experiment
   number, question, regime, status/evidence tier, scale, one-line outcome, and a
   link to the full page.
6. **Program map** — a compact sequence from behavioral observation to controls,
   mechanistic evidence, generalization, and the deterministic systems boundary.
7. **Open questions / planned work** — future experiments kept visually distinct
   from completed evidence.
8. **Artifacts** — links to the appendix, evidence manifest, repository, and
   reproduction entry points.

The landing page is a dashboard and executive summary, not a shortened version
of every experiment page.

### 2. Experiment pages

Recommended v1 routes:

| Route | Page | Evidence grouped here |
|---|---|---|
| `experiments/00-harness-validation/` | Harness validation | Stage 0 smoke test and paired-rendering controls |
| `experiments/01-citation-baseline/` | Citation baseline and identifier controls | Stage 1, scaled Stage 1, token-length/bracket/no-reproduction controls, decoding factorial |
| `experiments/02-multihop-musique/` | Multi-hop retrieval and confirmation | Stages 2–3, held-out confirmation, scaled MuSiQue, disjoint sensitivity, relevant frontier replication |
| `experiments/04-dual-labels/` | Dual-label ablation | Stage 4 alias-only vs UUID-only vs dual-label conditions |
| `experiments/05-reasoning-budget/` | Reasoning-budget scaling | Stage 5 pilot, confirmation, expanded fleet, budget sensitivity, relevant frontier extension |
| `experiments/longproc/` | Long-output reality check | LongProc smoke, GPU suite, and expanded seven-model suite |
| `experiments/06-representation-geometry/` | Representation geometry | Stage 6 hidden-state passes and Linear CKA analyses |
| `experiments/07-causal-interventions/` | Causal source-ID interventions | Stage 7 counterfactual swaps and activation patching |
| `experiments/08-entity-canonicalization/` | Cross-domain entity resolution | Stage 8 pilot, scaled suite, exposure results, and relevant frontier extension |
| `experiments/09-systems-boundary/` | Operational symbolic IR boundary | Stage 9 valid round trips, adversarial payloads, replay checks, and semantic bypass boundary |

Stage numbers remain visible because they are already used throughout the
repository. The UI should not force artificial numbering onto LongProc, which is
a supporting reality check rather than a numbered stage.

Cross-cutting runs such as the Anthropic extension should be represented in each
affected experiment page and linked through a shared `frontier-extension`
anchor/tag. They should not become a duplicate page containing the same result
tables a second time.

## Standard experiment-page anatomy

Every page should use the same semantic order so readers can compare studies
quickly:

1. Experiment identity: stage, title, status, evidence type, and last verified
   artifact set.
2. Question and motivation.
3. Hypothesis and falsifier.
4. Design: dataset, models, conditions, controls, decoding, and sample counts.
5. Metrics, including the distinction between strict formatting, relaxed
   binding, answer quality, exposure, and mechanistic measurements where
   applicable.
6. Run matrix: pilot, confirmation, scaled replication, sensitivity, or frontier
   blocks.
7. Results: headline effects followed by dense tables and existing figures.
8. Interpretation: what the experiment supports.
9. Boundaries: what it does not establish, anomalies, counter-results, and known
   confounds.
10. Reproduction and provenance: configs, scripts, findings reports, processed
    artifacts, and commands.
11. Related experiments: previous/next and conceptually related pages.

Dense tables may use horizontally scrollable containers on small screens, but
the primary conclusion and limitation must remain readable without opening a
collapsed disclosure.

## Visual and interaction direction

The visual language should shift from editorial magazine to research notebook /
experimental ledger:

- compact, readable typography and a restrained neutral palette;
- persistent experiment navigation on desktop and a compact index control on
  mobile;
- metadata chips for `behavioral`, `confirmatory`, `mechanistic`, `causal`,
  `system`, `complete`, and `open`;
- strong visual separation between measured result, interpretation, and open
  question;
- monospaced treatment for artifact paths, identifiers, configs, and commands;
- existing SVGs reused on their relevant experiment pages;
- accessible focus states, skip links, semantic headings, descriptive figure
  captions, and reduced-motion behavior;
- no dependence on animation for understanding or navigation.

The site should remain a local/static multi-page site compatible with the
existing `.nojekyll` deployment model. No framework migration is needed for this
restructure.

## Proposed file layout

```text
blog/site/
  index.html
  styles.css
  script.js
  .nojekyll
  assets/
    ...existing generated SVGs...
  experiments/
    00-harness-validation/index.html
    01-citation-baseline/index.html
    02-multihop-musique/index.html
    04-dual-labels/index.html
    05-reasoning-budget/index.html
    longproc/index.html
    06-representation-geometry/index.html
    07-causal-interventions/index.html
    08-entity-canonicalization/index.html
    09-systems-boundary/index.html
```

All pages will share `styles.css` and `script.js`. Experiment-page authors will
use a fixed class/section contract established before parallel work begins; they
will not independently edit shared CSS or navigation behavior.

The existing long-form Markdown article can remain as a historical source during
the migration. Whether it is later renamed to an archive is a separate editorial
decision and is not required for the UI restructure.

## Content-to-page source map

| Page | Primary narrative sources | Existing visual assets |
|---|---|---|
| Harness validation | `README.md`, `BLOG_PLAN.md`, Stage 0 row in `blog/evidence_manifest.csv` | `02_evidence_funnel.svg` (program-level context) |
| Citation baseline | `FINDINGS_STAGE1*.md`, `FINDINGS_CROSS_MODEL.md`, `FINDINGS_STAGE1_FACTORIAL.md` | `01_raw_vs_symbolic.svg`, relevant baseline tables |
| Multi-hop MuSiQue | `FINDINGS_MUSIQUE_STAGES_2_4.md`, `FINDINGS_MUSIQUE_CONFIRMATORY.md`, `FINDINGS_MUSIQUE_500.md`, `FINDINGS_MUSIQUE_SENSITIVITY.md` | `03_musique_confirmation.svg`, `03b_frontier_musique.svg` |
| Dual labels | Stage 4 sections in MuSiQue findings and the current article | reuse MuSiQue context; add no decorative figure unless evidence warrants it |
| Reasoning budget | `FINDINGS_STAGE5*.md`, frontier reasoning report | `04_reasoning_budget.svg`, `04b_anthropic_reasoning.svg` |
| LongProc | `FINDINGS_LONGPROC_SMOKE.md`, `FINDINGS_LONGPROC_GPU.md` | `05_longproc.svg` |
| Representation geometry | `FINDINGS_STAGE6*.md` | `06_stage6_geometry.svg` |
| Causal interventions | `FINDINGS_STAGE7*.md` | `07_stage7_swaps.svg` |
| Entity canonicalization | `FINDINGS_STAGE8*.md`, frontier Stage 8 results | `08_stage8_entities.svg` |
| Systems boundary | `FINDINGS_STAGE9.md`, reference implementation docs/results | `09_trust_boundary.svg` |

`blog/appendix.md` and `blog/evidence_manifest.csv` remain the shared definitions
and traceability sources across all pages.

## Hard scope boundaries

The implementation must not modify:

- `results/**`;
- `data/**`;
- `configs/**`;
- `experiments/**`;
- `src/**`;
- analysis or run scripts outside the blog/site presentation layer;
- generated numerical values or statistical claims without tracing them to an
  existing checked-in source artifact.

Expected edits are limited to:

- `blog/site/**`;
- blog-facing content/tests needed to validate the new page structure;
- optionally this plan and documentation that explains the new navigation.

Existing figures should be copied or referenced, not regenerated, unless a later
task explicitly requests figure changes.

## Parallel implementation plan

### Wave 0 — shared contract (primary agent)

Before delegation:

1. Freeze route names and the page anatomy above.
2. Establish the shared header, footer, experiment navigation, CSS tokens, page
   classes, relative-link conventions, and reusable accessibility patterns.
3. Create minimal page shells or a reference experiment page.
4. Record a per-page artifact checklist derived from
   `blog/evidence_manifest.csv`.

This short sequential step prevents parallel agents from inventing incompatible
layouts or editing the same shared files.

### Wave 1 — parallel page construction

With three sub-agents plus the primary integrator:

| Owner | Exclusive file ownership | Work |
|---|---|---|
| Sub-agent A | `blog/site/index.html` | Build the landing-page TL;DR, motivation, program map, experiment directory, and open-questions block using the shared shell. |
| Sub-agent B | pages `00`, `01`, `02`, and `04` only | Build behavioral, validation, multi-hop, and identifier-control pages from existing findings and manifest rows. |
| Sub-agent C | pages `05`, `longproc`, `06`, and `07` only | Build reasoning-budget, long-output, representation, and causal pages. |
| Primary agent | pages `08` and `09`; shared files only | Build applied/system pages, maintain `styles.css` and `script.js`, and integrate navigation and cross-links. |

Rules for the parallel wave:

- sub-agents do not edit shared CSS, JavaScript, figures, tests, results, or the
  evidence manifest;
- every numerical claim must name its source artifact in the page's provenance
  section;
- pages should use only the predeclared shared classes;
- unresolved claim conflicts are reported to the primary agent rather than
  silently normalized.

### Wave 2 — integration and QA (primary agent)

1. Verify all landing-page links, previous/next links, asset URLs, and repository
   links.
2. Check that all 19 evidence-manifest rows are represented by a page or anchored
   study block.
3. Update `tests/test_blog_claims.py` so claim checks target the new experiment
   pages rather than assuming all public claims live in `index.html`.
4. Add structural tests for required routes, unique page titles, required
   provenance sections, and local-link integrity.
5. Run the existing test suite relevant to blog claims.
6. Perform responsive browser QA at narrow mobile, tablet, and desktop widths;
   check keyboard navigation, focus visibility, table overflow, reduced motion,
   and no-JavaScript readability.
7. Review `git diff --name-only` and fail the handoff if any protected data/run
   paths changed.

## Acceptance criteria

The restructure is complete when:

- the landing page communicates the motivation, problem, thesis, evidence TL;DR,
  experiment program, and open questions without requiring a long linear read;
- every experiment-directory entry opens a dedicated comprehensive page;
- all current public evidence is mapped to exactly one primary experiment page,
  with cross-links rather than duplicated authoritative tables;
- each page includes question, design, metrics, results, limitations,
  provenance, reproduction, and related-experiment navigation;
- all existing checked-in figures used by the current site remain reachable from
  a relevant page;
- claim-validation and link-integrity tests pass;
- the site remains usable on mobile and with keyboard-only navigation;
- no underlying run data, processed results, configs, experiment code, or model
  pipeline files are modified.

## Deliberately deferred decisions

The following should not block the first implementation pass:

- rewriting experimental prose beyond what is needed to split and label it;
- adding new charts or recomputing old charts;
- adopting a JavaScript framework or CMS;
- changing hosting or deployment;
- deleting the historical long-form Markdown article;
- changing experiment names, stage numbers, or research conclusions.

These can be evaluated after the multi-page log is working and its content gaps
are visible.
