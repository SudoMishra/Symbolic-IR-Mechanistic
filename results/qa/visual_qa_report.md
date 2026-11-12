# Visual QA Audit Report

**Audit Execution Time:** `2026-11-12 05:54:45` (`2026-11-12T00:24:45.394343+00:00`)
**Target Site:** `blog/site/index.html`
**Browser Engine:** Google Chrome Headless (Chrome DevTools Protocol)

## 1. Viewport Responsiveness & Layout Geometry

All three standardized screen widths were measured for layout geometry and horizontal overflow:

| Viewport | Screen Width | Viewport Height | Total Page Height | Horizontal Overflow Diff | Viewport Shot | Full Page Shot | Status |
|---|---:|---:|---:|---:|---|---|:---:|
| Mobile | 390 px | 844 px | 47,364 px | `0 px` | [`site_mobile_390px_viewport.png`](site_mobile_390px_viewport.png) | [`site_mobile_390px_full.png`](site_mobile_390px_full.png) | **PASS (0px overflow)** |
| Tablet | 768 px | 1024 px | 36,880 px | `0 px` | [`site_tablet_768px_viewport.png`](site_tablet_768px_viewport.png) | [`site_tablet_768px_full.png`](site_tablet_768px_full.png) | **PASS (0px overflow)** |
| Desktop | 1440 px | 900 px | 41,733 px | `0 px` | [`site_desktop_1440px_viewport.png`](site_desktop_1440px_viewport.png) | [`site_desktop_1440px_full.png`](site_desktop_1440px_full.png) | **PASS (0px overflow)** |

## 2. In-Context Figure & Caption Adjacency Verification

Every figure in the publication was evaluated in its actual DOM context inside `blog/site/index.html`:

| Figure Asset | Figure Role | Context Dimensions (WxH) | Caption Pairing | Rendered In-Context Screenshot | Status |
|---|---|:---:|---|---|:---:|
| `01_raw_vs_symbolic.svg` | `assets/01_raw_vs_symbolic.svg` | 1361 x 1031 px | Verified (`<figcaption>` adjacent) | [`figure_context_01_raw_vs_symbolic.png`](figure_context_01_raw_vs_symbolic.png) | **PASS** |
| `02_evidence_funnel.svg` | `assets/02_evidence_funnel.svg` | 1361 x 917 px | Verified (`<figcaption>` adjacent) | [`figure_context_02_evidence_funnel.png`](figure_context_02_evidence_funnel.png) | **PASS** |
| `03_musique_confirmation.svg` | `assets/03_musique_confirmation.svg` | 1361 x 1040 px | Verified (`<figcaption>` adjacent) | [`figure_context_03_musique_confirmation.png`](figure_context_03_musique_confirmation.png) | **PASS** |
| `03b_frontier_musique.svg` | `assets/03b_frontier_musique.svg` | 652 x 412 px | Verified (`<figcaption>` adjacent) | [`figure_context_03b_frontier_musique.png`](figure_context_03b_frontier_musique.png) | **PASS** |
| `04_reasoning_budget.svg` | `assets/04_reasoning_budget.svg` | 1361 x 1210 px | Verified (`<figcaption>` adjacent) | [`figure_context_04_reasoning_budget.png`](figure_context_04_reasoning_budget.png) | **PASS** |
| `04b_anthropic_reasoning.svg` | `assets/04b_anthropic_reasoning.svg` | 1361 x 565 px | Verified (`<figcaption>` adjacent) | [`figure_context_04b_anthropic_reasoning.png`](figure_context_04b_anthropic_reasoning.png) | **PASS** |
| `05_longproc.svg` | `assets/05_longproc.svg` | 1294 x 997 px | Verified (`<figcaption>` adjacent) | [`figure_context_05_longproc.png`](figure_context_05_longproc.png) | **PASS** |
| `06_stage6_geometry.svg` | `assets/06_stage6_geometry.svg` | 1361 x 1348 px | Verified (`<figcaption>` adjacent) | [`figure_context_06_stage6_geometry.png`](figure_context_06_stage6_geometry.png) | **PASS** |
| `07_stage7_swaps.svg` | `assets/07_stage7_swaps.svg` | 1361 x 1286 px | Verified (`<figcaption>` adjacent) | [`figure_context_07_stage7_swaps.png`](figure_context_07_stage7_swaps.png) | **PASS** |
| `07b_stage7_patching.svg` | `assets/07b_stage7_patching.svg` | 1361 x 1265 px | Verified (`<figcaption>` adjacent) | [`figure_context_07b_stage7_patching.png`](figure_context_07b_stage7_patching.png) | **PASS** |
| `08_stage8_entities.svg` | `assets/08_stage8_entities.svg` | 1361 x 1032 px | Verified (`<figcaption>` adjacent) | [`figure_context_08_stage8_entities.png`](figure_context_08_stage8_entities.png) | **PASS** |
| `09_trust_boundary.svg` | `assets/09_trust_boundary.svg` | 1361 x 1135 px | Verified (`<figcaption>` adjacent) | [`figure_context_09_trust_boundary.png`](figure_context_09_trust_boundary.png) | **PASS** |

## 3. Isolated SVG Asset Visual Inspections

| Figure | File | Isolated Render | Visual QA Result |
|---|---|---|---|
| Figure 1 | `01_raw_vs_symbolic.svg` | [`render_01_raw_vs_symbolic.png`](render_01_raw_vs_symbolic.png) | Verified: no clipped labels, legible typography, contained legends |
| Figure 2 | `02_evidence_funnel.svg` | [`render_02_evidence_funnel.png`](render_02_evidence_funnel.png) | Verified: no clipped labels, legible typography, contained legends |
| Figure 2 (Mobile) | `02_evidence_funnel_mobile.svg` | [`render_02_evidence_funnel_mobile.png`](render_02_evidence_funnel_mobile.png) | Verified: no clipped labels, legible typography, contained legends |
| Figure 3 | `03_musique_confirmation.svg` | [`render_03_musique_confirmation.png`](render_03_musique_confirmation.png) | Verified: no clipped labels, legible typography, contained legends |
| Figure 3B | `03b_frontier_musique.svg` | [`render_03b_frontier_musique.png`](render_03b_frontier_musique.png) | Verified: no clipped labels, legible typography, contained legends |
| Figure 4A | `04_reasoning_budget.svg` | [`render_04_reasoning_budget.png`](render_04_reasoning_budget.png) | Verified: no clipped labels, legible typography, contained legends |
| Figure 4B | `04b_anthropic_reasoning.svg` | [`render_04b_anthropic_reasoning.png`](render_04b_anthropic_reasoning.png) | Verified: no clipped labels, legible typography, contained legends |
| Figure 5 | `05_longproc.svg` | [`render_05_longproc.png`](render_05_longproc.png) | Verified: no clipped labels, legible typography, contained legends |
| Figure 6 | `06_stage6_geometry.svg` | [`render_06_stage6_geometry.png`](render_06_stage6_geometry.png) | Verified: no clipped labels, legible typography, contained legends |
| Figure 7A | `07_stage7_swaps.svg` | [`render_07_stage7_swaps.png`](render_07_stage7_swaps.png) | Verified: no clipped labels, legible typography, contained legends |
| Figure 7B | `07b_stage7_patching.svg` | [`render_07b_stage7_patching.png`](render_07b_stage7_patching.png) | Verified: no clipped labels, legible typography, contained legends |
| Figure 8 | `08_stage8_entities.svg` | [`render_08_stage8_entities.png`](render_08_stage8_entities.png) | Verified: no clipped labels, legible typography, contained legends |
| Figure 9 | `09_trust_boundary.svg` | [`render_09_trust_boundary.png`](render_09_trust_boundary.png) | Verified: no clipped labels, legible typography, contained legends |

## 4. Checklist Verification Summary (P8-17 through P8-23)

- [x] **P8-17 (390px Mobile):** Rendered cleanly (`site_mobile_390px_viewport.png`, `site_mobile_390px_full.png`). Page width conforms strictly to 390px with exactly 0px horizontal overflow. Mobile layout automatically activates stacked SVG (`02_evidence_funnel_mobile.svg`).
- [x] **P8-18 (768px Tablet):** Rendered cleanly (`site_tablet_768px_viewport.png`, `site_tablet_768px_full.png`). Main grid column centers with 24px margins; exactly 0px horizontal overflow.
- [x] **P8-19 (1,440px Desktop):** Rendered cleanly (`site_desktop_1440px_viewport.png`, `site_desktop_1440px_full.png`). Centered readable content column with balanced side margins and crisp SVG asset resolution.
- [x] **P8-20 (No Clipped Legends):** All 12 publication figures verified. Axis tick labels are constrained (e.g. `Figure 7B` uses compact `[-0.2, 0.0, 0.5, 1.0, 1.2]` ticks with internal reference text to prevent left-margin clipping).
- [x] **P8-21 (Figure 3 Centering & Bounds):** Confirmed in context and isolation: 'Favors Numeric' and 'Favors UUID' directional markers are centered above data bars; bottom methodology notes are contained within bounds.
- [x] **P8-22 (Caption-Figure Adjacency):** DOM evaluation confirms 100% of `<figure>` elements contain an immediate, adjacent `<figcaption>` block at all screen widths.
- [x] **P8-23 (Model Name Consistency):** Uniform nomenclature verified across all plots, tables, prose, and metadata: `Qwen 2.5 1.5B`, `Tiny Aya Global`, `Gemma 4 E2B`, `Gemma 4 E4B`, `Qwen 3.5 2B`, `Qwen 3.5 4B`.

---
**Certification:** Current visual QA audit PASSED with 100% compliance across all checklist criteria.
