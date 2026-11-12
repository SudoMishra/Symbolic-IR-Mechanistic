# Experiment page contract

This file is an implementation aid for parallel page authors. It is not linked
from the public site.

## Shared files

Do not edit `styles.css`, `script.js`, `index.html`, assets, or tests. Each page
author owns only the experiment directories assigned to them.

Every page loads `../../styles.css` and `../../script.js` and links the landing
page as `../../index.html`. Existing assets use `../../assets/<name>.svg`.

## Required shell

Every experiment page contains:

- `.skip-link` targeting `#main-content`;
- `.site-header > .header-inner` with `.brand`, `[data-nav-toggle]`, and
  `[data-site-nav]`;
- `.page-shell` with `.experiment-sidebar` and `.experiment-main#main-content`;
- the full `.experiment-nav`, marking the current page with
  `aria-current="page"`;
- `.hero` and `.meta-grid`;
- sections with IDs: `question`, `design`, `results`, `interpretation`,
  `boundaries`, `provenance`, and `related`;
- `.site-footer` and the shared script before `</body>`.

## Content rules

- Treat repository findings, the current blog, appendix, evidence manifest, and
  checked-in result summaries as read-only sources.
- Never invent or recompute numerical claims. If exact values are unclear, state
  the qualitative finding and name the source artifact.
- Distinguish measured evidence (`.callout`), supported interpretation
  (`.callout.supports`), limitations (`.callout.boundary`), and future work
  (`.callout.open`).
- Use `.study-block` for pilot, confirmation, scaled, sensitivity, or frontier
  cohorts and give each block a stable ID.
- Use accessible tables with a caption, header cells, and `.table-wrap`.
- Use `.figure-card` with an informative `figcaption` for existing SVGs.
- Include artifact paths under `.artifact-list`; these are provenance labels,
  not necessarily browser links from the deployed static directory.

## Experiment routes

The sidebar order is: 00 harness; 01 baseline; 02 MuSiQue; 04 dual labels; 05
reasoning; LP LongProc; 06 geometry; 07 interventions; 08 entities; 09 systems.
