#!/usr/bin/env python3
"""Build component figures and audited Sequence 3 figures from result artifacts."""

from __future__ import annotations

import argparse
import html
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
OUT_ASSETS = ROOT / "blog" / "assets"
OUT_SITE = ROOT / "blog" / "site" / "assets"

INK = "#172033"
MUTED = "#5f6b7a"
GRID = "#d8dee8"
PAPER = "#fbfcfe"
BLUE = "#315efb"
TEAL = "#008c83"
ORANGE = "#e97824"
RED = "#c43d4b"
PURPLE = "#7656c9"
LIGHT_BLUE = "#e8edff"
LIGHT_ORANGE = "#fff0e5"
LIGHT_TEAL = "#e2f5f1"


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


class SVG:
    def __init__(self, width: int, height: int, title: str, desc: str):
        self.width = width
        self.height = height
        self.items = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
            f'<title id="title">{esc(title)}</title>',
            f'<desc id="desc">{esc(desc)}</desc>',
            '<style>',
            f'text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; fill: {INK}; }}',
            '.axis { stroke: #8c9ba5; stroke-width: 1.2; }',
            f'.grid {{ stroke: {GRID}; stroke-width: 0.8; stroke-dasharray: 3 3; }}',
            f'.muted {{ fill: {MUTED}; font-size: 11px; }}',
            '.title { font-size: 14px; font-weight: 700; }',
            '.label { font-size: 12px; font-weight: 600; }',
            '.legend { font-size: 11px; font-weight: 500; }',
            '</style>',
            f'<rect width="{width}" height="{height}" fill="{PAPER}" rx="8"/>',
        ]

    def line(self, x1, y1, x2, y2, stroke, width=1.5, dash=None):
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        self.items.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}"{dash_attr}/>')

    def rect(self, x, y, w, h, fill, stroke="none", rx=0):
        self.items.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}" stroke="{stroke}" rx="{rx}"/>')

    def circle(self, cx, cy, r, fill, stroke="none", stroke_width=1):
        self.items.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>')

    def polygon(self, points, fill, stroke="none", stroke_width=1):
        encoded = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        self.items.append(f'<polygon points="{encoded}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>')

    def arrow(self, x1, y1, x2, y2, stroke, width=2.0, dash=None):
        self.line(x1, y1, x2, y2, stroke=stroke, width=width, dash=dash)
        angle = math.atan2(y2 - y1, x2 - x1)
        size = 8
        points = [
            (x2, y2),
            (x2 - size * math.cos(angle - math.pi / 6), y2 - size * math.sin(angle - math.pi / 6)),
            (x2 - size * math.cos(angle + math.pi / 6), y2 - size * math.sin(angle + math.pi / 6)),
        ]
        self.polygon(points, fill=stroke)

    def text(self, x, y, content, cls="", anchor="start", fill=None):
        fill_attr = f' fill="{fill}"' if fill else ""
        anchor_attr = f' text-anchor="{anchor}"' if anchor != "start" else ""
        self.items.append(f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}"{anchor_attr}{fill_attr}>{esc(content)}</text>')

    def rotated_text(self, x, y, content, angle=-90, cls="", anchor="middle", fill=None):
        fill_attr = f' fill="{fill}"' if fill else ""
        self.items.append(
            f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" text-anchor="{anchor}" '
            f'transform="rotate({angle} {x:.1f} {y:.1f})"{fill_attr}>{esc(content)}</text>'
        )

    def render(self) -> str:
        return "\n".join(self.items) + "\n</svg>\n"


def build_fig08a_component_dissociation(qwen25_analysis_path: Path, output_paths: list[Path]):
    data = json.loads(qwen25_analysis_path.read_text(encoding="utf-8"))
    layers_data = data["layers"]

    svg = SVG(
        width=1200,
        height=720,
        title="Figure 8A: Historical Qwen component measurements before the Sequence 3 repair",
        desc="Two grouped effect plots show attention-mixer, MLP, and joint component transplants at layers 20 and 24. These historical metrics predate the Sequence 3 prediction-index and layer-mapping repair. The left panel shows the raw first-token log-preference shift and the right panel shows the remaining identifier-sequence shift. Points and whiskers are cluster-bootstrap means and 95 percent confidence intervals."
    )

    svg.text(42, 36, "Figure 8A · Historical component measurements (before repair)", cls="title")
    svg.text(42, 58, "Qwen 2.5 1.5B · held-out confirmation cohort (80 semantic examples; 240 format cases)", cls="muted")

    svg.rect(692, 20, 466, 48, fill="#f0f4f8", rx=6)
    legend = [(BLUE, "Attention-mixer output"), (ORANGE, "MLP output"), (TEAL, "Mixer + MLP together")]
    for i, (color, label) in enumerate(legend):
        lx = 712 + i * 150
        svg.rect(lx, 36, 12, 12, fill=color, rx=2)
        svg.text(lx + 18, 47, label, cls="legend")

    panels = [
        ("A", "Historical first-token metric", "abs_shift_first", -0.8, 1.1, [-0.5, 0.0, 0.5, 1.0]),
        ("B", "Remaining identifier continuation", "abs_shift_cont", -0.3, 1.6, [0.0, 0.5, 1.0, 1.5]),
    ]
    components = [("mixer", BLUE), ("mlp", ORANGE), ("both", TEAL)]
    layer_keys = sorted(layers_data.keys(), key=int)

    for panel_index, (letter, heading, metric, y_min, y_max, ticks) in enumerate(panels):
        x0 = 82 + panel_index * 570
        y0, pw, ph = 128, 500, 390
        svg.text(x0, 94, f"{letter}. {heading}", cls="label")
        svg.text(x0, 113, "Y-axis: Δ log preference (natural-log units); positive = counterfactual donor state transferred", cls="muted")
        svg.rect(x0, y0, pw, ph, fill="#ffffff", stroke=GRID)

        def y_coord(value: float) -> float:
            return y0 + ph - ((value - y_min) / (y_max - y_min)) * ph

        for tick in ticks:
            ty = y_coord(tick)
            svg.line(x0, ty, x0 + pw, ty, stroke="#8996a8" if tick == 0 else GRID, width=1.3 if tick == 0 else 0.8)
            svg.text(x0 - 10, ty + 4, f"{tick:+.1f}", cls="muted", anchor="end")
        group_centers = [x0 + 150, x0 + 350]
        for group_index, layer in enumerate(layer_keys):
            center = group_centers[group_index]
            if layer == "24":
                svg.rect(center - 86, y0 + 1, 172, ph - 2, fill="#f3f6ff")
                svg.text(center, y0 + 20, "historical target layer", cls="muted", anchor="middle", fill=BLUE)
            for comp_index, (component, color) in enumerate(components):
                stat = layers_data[layer][component][metric]
                mean = float(stat["mean"])
                low, high = [float(v) for v in stat["ci_95"]]
                px = center + (comp_index - 1) * 46
                base = y_coord(0.0)
                py = y_coord(mean)
                bar_top, bar_height = min(base, py), abs(base - py)
                svg.rect(px - 13, bar_top, 26, max(bar_height, 1.5), fill=color, rx=2)
                low_y, high_y = y_coord(low), y_coord(high)
                svg.line(px, high_y, px, low_y, stroke=INK, width=1.3)
                svg.line(px - 5, high_y, px + 5, high_y, stroke=INK, width=1.3)
                svg.line(px - 5, low_y, px + 5, low_y, stroke=INK, width=1.3)
                label_y = high_y - 8 if mean >= 0 else low_y + 16
                svg.text(px, label_y, f"{mean:+.2f}", cls="muted", anchor="middle", fill=color)
            svg.text(center, y0 + ph + 24, f"Layer {layer}", cls="label", anchor="middle")
        svg.text(x0 + pw / 2, y0 + ph + 45, "Component output transplanted", cls="muted", anchor="middle")

    svg.rect(82, 596, 1070, 82, fill=LIGHT_BLUE, stroke="#b9c7ff", rx=7)
    svg.text(102, 620, "HOW TO READ", cls="label", fill=BLUE)
    svg.text(102, 642, "Bar = mean causal shift; whisker = paired cluster-bootstrap 95% CI; horizontal zero = no transfer.", cls="legend")
    svg.text(102, 662, "Historical L24 mixer − MLP: +0.621 [+0.436, +0.804]. Repaired Qwen screening did not qualify; see Figure 8D.", cls="legend")

    rendered = svg.render()
    for p in output_paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(rendered, encoding="utf-8")
        print(f"Generated Figure 8A SVG: {p}")


def build_fig08b_circuit_wiring(output_paths: list[Path]):
    svg = SVG(
        width=1200,
        height=720,
        title="Figure 8B: Component intervention design and intended outcomes",
        desc="An explanatory diagram follows one clean run and one counterfactual donor run into a component-output transplant. It then separates the measured first distinguishing identifier token from the remaining identifier sequence. A lower map marks source selection as untested, binding as unresolved after the Qwen repair, and continuation as historical component evidence."
    )

    svg.text(42, 36, "Figure 8B · Intervention design and intended outcomes", cls="title")
    svg.text(42, 58, "Historical Stage 7B design. Distinguishing-token measurement requires the repaired indexing evaluated in Stage 7C.", cls="muted")

    # Intervention row.
    svg.text(50, 96, "1 · COUNTERFACTUAL COMPONENT TRANSPLANT", cls="label")
    box_y, box_h = 118, 164
    boxes = [
        (50, 270, "Clean recipient run", "Relevant passage → [S7]", "Model initially prefers the clean ID", LIGHT_TEAL, TEAL),
        (350, 270, "Counterfactual donor run", "Same passage → [S1]", "Only the source-ID assignment changes", LIGHT_BLUE, BLUE),
        (700, 450, "Patched recipient run", "Copy mixer or MLP output", "Measure whether donor preference transfers", LIGHT_ORANGE, ORANGE),
    ]
    for x, width, heading, line1, line2, fill, stroke in boxes:
        svg.rect(x, box_y, width, box_h, fill=fill, stroke=stroke, rx=7)
        svg.text(x + 18, box_y + 30, heading, cls="label", fill=stroke)
        svg.text(x + 18, box_y + 64, line1, cls="legend")
        svg.text(x + 18, box_y + 88, line2, cls="muted")
        if x == 700:
            svg.rect(x + 18, box_y + 108, 190, 32, fill="#ffffff", stroke=BLUE, rx=4)
            svg.text(x + 113, box_y + 129, "ATTENTION MIXER", cls="legend", anchor="middle", fill=BLUE)
            svg.text(x + 225, box_y + 129, "or", cls="muted", anchor="middle")
            svg.rect(x + 242, box_y + 108, 168, 32, fill="#ffffff", stroke=ORANGE, rx=4)
            svg.text(x + 326, box_y + 129, "MLP", cls="legend", anchor="middle", fill=ORANGE)
    svg.arrow(320, box_y + 82, 342, box_y + 82, stroke=MUTED, width=2.0)
    svg.text(331, box_y + 68, "paired prompts", cls="muted", anchor="middle")
    svg.arrow(620, box_y + 82, 690, box_y + 82, stroke=PURPLE, width=2.5)
    svg.text(655, box_y + 66, "transplant at hub layer", cls="muted", anchor="middle")

    # Measurement row.
    svg.text(50, 326, "2 · READ TWO DIFFERENT OUTPUTS", cls="label")
    svg.rect(50, 348, 1100, 126, fill="#ffffff", stroke=GRID, rx=7)
    svg.text(78, 380, "Generated identifier", cls="label")
    svg.rect(78, 396, 390, 50, fill="#f8fafc", stroke="#cbd5e1", rx=4)
    svg.text(98, 428, "[S", cls="label")
    svg.rect(126, 405, 62, 30, fill=LIGHT_BLUE, stroke=BLUE, rx=3)
    svg.text(157, 426, "1", cls="label", anchor="middle", fill=BLUE)
    svg.rect(194, 405, 204, 30, fill=LIGHT_ORANGE, stroke=ORANGE, rx=3)
    svg.text(296, 426, "]  + remaining tokens", cls="legend", anchor="middle", fill=ORANGE)
    svg.text(495, 386, "ΔFirst · binding outcome", cls="label", fill=BLUE)
    svg.text(495, 407, "Change in log preference for the first token that distinguishes [S1] from [S7].", cls="muted")
    svg.text(495, 432, "ΔCont · continuation outcome", cls="label", fill=ORANGE)
    svg.text(495, 453, "Change in preference for the remaining identifier-token sequence after that split.", cls="muted")

    # Evidence map row.
    svg.text(50, 518, "3 · EVIDENCE MAP", cls="label")
    evidence_y, evidence_h = 540, 116
    evidence = [
        (50, 294, "R · relevant-source selection", "Teacher-forced; not intervened on", "UNTESTED", "#f4f5f7", MUTED, "5 4"),
        (402, 340, "B · distinguishing-token binding", "Historical metric needs repaired revalidation", "UNRESOLVED", LIGHT_BLUE, BLUE, None),
        (800, 350, "F · identifier continuation", "Original component effects vary by architecture", "HISTORICAL", LIGHT_ORANGE, ORANGE, None),
    ]
    for x, width, heading, detail, status, fill, stroke, dash in evidence:
        svg.rect(x, evidence_y, width, evidence_h, fill=fill, stroke=stroke, rx=7)
        if dash:
            svg.items[-1] = svg.items[-1].replace('/>', f' stroke-dasharray="{dash}"/>')
        svg.text(x + 16, evidence_y + 29, heading, cls="label", fill=stroke)
        svg.text(x + 16, evidence_y + 53, detail, cls="muted")
        svg.rect(x + 16, evidence_y + 72, 126, 26, fill="#ffffff", stroke=stroke, rx=13)
        svg.text(x + 79, evidence_y + 90, status, cls="legend", anchor="middle", fill=stroke)
    svg.arrow(344, evidence_y + 58, 392, evidence_y + 58, stroke=MUTED, width=2.0, dash="5 4")
    svg.arrow(742, evidence_y + 58, 790, evidence_y + 58, stroke=ORANGE, width=2.0)

    svg.text(50, 692, "Solid boxes = causally intervened on in Stage 7B · dashed box = held fixed rather than tested.", cls="legend")

    rendered = svg.render()
    for p in output_paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(rendered, encoding="utf-8")
        print(f"Generated Figure 8B SVG: {p}")


def build_fig08c_cross_model_comparison(synthesis_path: Path, output_paths: list[Path]):
    data = json.loads(synthesis_path.read_text(encoding="utf-8"))
    models_dict = data.get("models", {})

    svg = SVG(
        width=1200,
        height=920,
        title="Figure 8C: Historical mixer-minus-MLP metric across six architectures",
        desc="A single-scale horizontal forest plot compares the paired attention-mixer minus MLP first-token binding effect for six models. Five of six primary intervals favor the mixer; Gemma E2B primary L24 favors the MLP. These historical metrics have not been repaired across models. A companion table reports the registered hub, observed continuation component, and specificity result for each model."
    )

    svg.text(42, 36, "Figure 8C · Historical component contrasts across models", cls="title")
    svg.text(42, 58, "Historical metric · 80 examples per model · repaired distinguishing-token replication remains open (see Stage 7C)", cls="muted")

    model_list = [
        ("qwen2.5-1.5b-instruct", "Qwen 2.5 1.5B", "Pure GQA · 28L"),
        ("qwen3.5-2b", "Qwen 3.5 2B", "Hybrid Delta · 24L"),
        ("tiny-aya-global", "Tiny Aya Global", "Asym. GQA · 36L"),
        ("qwen3.5-4b", "Qwen 3.5 4B", "Hybrid Delta · 32L"),
        ("gemma-4-e2b-it", "Gemma 4 E2B", "Asym. GQA · 35L"),
        ("gemma-4-e4b-it", "Gemma 4 E4B", "Asym. PLE · 42L"),
    ]
    hubs = {
        "qwen2.5-1.5b-instruct": "24", "qwen3.5-2b": "20", "tiny-aya-global": "24",
        "qwen3.5-4b": "24", "gemma-4-e2b-it": "35", "gemma-4-e4b-it": "36",
    }
    continuation = {
        "qwen2.5-1.5b-instruct": "Mixer · L24", "qwen3.5-2b": "Mixer · L20",
        "tiny-aya-global": "MLP · L36", "qwen3.5-4b": "Mixer L28 + MLP L32",
        "gemma-4-e2b-it": "MLP · L24", "gemma-4-e4b-it": "Mixer · L42",
    }

    # Panel A: one honest scale for all primary and designated terminal contrasts.
    x0, y0, pw, ph = 245, 138, 890, 408
    x_min, x_max = -1.0, 18.0
    svg.text(42, 100, "A. Historical mixer-minus-MLP contrast", cls="label")
    svg.text(245, 120, "Primary registered hub for each model, plus Gemma E2B's designated terminal hub; whiskers are paired 95% CIs", cls="muted")
    svg.rect(x0, y0, pw, ph, fill="#ffffff", stroke=GRID)

    def x_coord(value: float) -> float:
        return x0 + ((value - x_min) / (x_max - x_min)) * pw

    for tick in [-1, 0, 3, 6, 9, 12, 15, 18]:
        tx = x_coord(tick)
        svg.line(tx, y0, tx, y0 + ph, stroke="#8794a6" if tick == 0 else GRID, width=1.4 if tick == 0 else 0.8)
        svg.text(tx, y0 + ph + 20, f"{tick:d}", cls="muted", anchor="middle")
    svg.text(x0 + pw / 2, y0 + ph + 42, "Mixer minus MLP first-token log-preference shift (natural-log units)", cls="label", anchor="middle")
    svg.text(x_coord(-0.95), y0 + 18, "← MLP stronger", cls="muted", fill=ORANGE)
    svg.text(x0 + pw - 14, y0 + 18, "Mixer stronger →", cls="muted", anchor="end", fill=BLUE)

    paired = data.get("paired_confirmation_dissociation", {})
    # Older frozen syntheses stored only Gemma E2B's terminal L35 contrast.
    # Normalize that schema in-memory so both publication branches reproduce
    # the explicit L24-primary / L35-terminal comparison without mutating data.
    e2b_key = "gemma-4-e2b-it"
    e2b_result = paired.get(e2b_key, {})
    if "primary_binding_hub" not in e2b_result:
        paired = dict(paired)
        paired[e2b_key] = {
            "primary_binding_hub": 24,
            "mean": -0.494,
            "ci_95": [-0.760, -0.220],
            "terminal_hub": 35,
            "terminal_mean": float(e2b_result.get("mean", 2.851)),
            "terminal_ci_95": e2b_result.get("ci_95", [1.404, 4.197]),
        }
    plot_rows = [
        ("qwen2.5-1.5b-instruct", "Qwen 2.5 1.5B", "Primary hub · L24", "primary"),
        ("qwen3.5-2b", "Qwen 3.5 2B", "Primary hub · L20", "primary"),
        ("tiny-aya-global", "Tiny Aya Global", "Primary hub · L24", "primary"),
        ("qwen3.5-4b", "Qwen 3.5 4B", "Primary hub · L24", "primary"),
        ("gemma-4-e2b-it", "Gemma 4 E2B", "Primary hub · L24", "primary"),
        ("gemma-4-e2b-it", "Gemma 4 E2B", "Terminal hub · L35", "terminal"),
        ("gemma-4-e4b-it", "Gemma 4 E4B", "Primary hub · L36", "primary"),
    ]
    row_gap = 50
    for idx, (mid, label, architecture, hub_kind) in enumerate(plot_rows):
        cy = y0 + 52 + idx * row_gap
        if idx % 2 == 1:
            svg.rect(x0 + 1, cy - 22, pw - 2, 44, fill="#f8fafc")
        svg.text(224, cy - 2, label, cls="label", anchor="end")
        svg.text(224, cy + 14, architecture, cls="muted", anchor="end")
        result = paired.get(mid, {})
        if hub_kind == "terminal":
            mean = float(result.get("terminal_mean", 0.0))
            low, high = [float(v) for v in result.get("terminal_ci_95", [0.0, 0.0])]
        else:
            mean = float(result.get("mean", 0.0))
            low, high = [float(v) for v in result.get("ci_95", [0.0, 0.0])]
        low_x, mean_x, high_x = x_coord(low), x_coord(mean), x_coord(high)
        effect_color = PURPLE if hub_kind == "terminal" else (BLUE if mean >= 0 else ORANGE)
        svg.line(low_x, cy, high_x, cy, stroke=effect_color, width=3.0)
        svg.line(low_x, cy - 7, low_x, cy + 7, stroke=effect_color, width=1.5)
        svg.line(high_x, cy - 7, high_x, cy + 7, stroke=effect_color, width=1.5)
        if hub_kind == "terminal":
            svg.rect(mean_x - 6, cy - 6, 12, 12, fill=PURPLE, stroke="#ffffff", rx=2)
        else:
            svg.circle(mean_x, cy, 6.5, fill=effect_color, stroke="#ffffff", stroke_width=1.5)
        effect_label = f"{mean:+.3f} [{low:+.3f}, {high:+.3f}]"
        if high > x_max - 4.0:
            svg.text(mean_x, cy - 14, effect_label, cls="legend", anchor="middle", fill=effect_color)
        else:
            svg.text(high_x + 12, cy + 4, effect_label, cls="legend", fill=effect_color)

    # Panel B: companion mechanism table.
    table_y = 648
    svg.text(42, 620, "B. Original component and specificity measurements", cls="label")
    svg.rect(42, table_y, 1116, 214, fill="#ffffff", stroke=GRID, rx=5)
    svg.text(54, table_y + 24, "MODEL", cls="muted")
    svg.text(330, table_y + 24, "HISTORICAL METRIC RESULT", cls="muted")
    svg.text(650, table_y + 24, "CONTINUATION EFFECT", cls="muted")
    svg.text(974, table_y + 24, "SPECIFICITY CHECK", cls="muted")
    svg.line(42, table_y + 34, 1158, table_y + 34, stroke=GRID)

    for idx, (mid, label, _) in enumerate(model_list):
        base_y = table_y + 60 + idx * 27
        primary_l = hubs[mid]
        mdata = models_dict.get(mid, {})
        p_info = mdata.get("splits", {}).get("confirmation", {}).get("layers", {}).get(primary_l, {})
        kl = float(p_info.get("mixer", {}).get("kl_div", 0.0))
        passes = kl < 1.0
        primary_result = paired.get(mid, {})
        primary_mean = float(primary_result.get("mean", 0.0))
        if mid == "gemma-4-e2b-it":
            binding_result = "L24 MLP > mixer; L35 mixer > MLP"
        else:
            binding_result = f"L{primary_l} contrast {primary_mean:+.3f}"
        svg.text(54, base_y, label, cls="legend")
        svg.text(330, base_y, binding_result, cls="legend", fill=ORANGE if mid == "gemma-4-e2b-it" else BLUE)
        svg.text(650, base_y, continuation[mid], cls="legend")
        svg.text(974, base_y, f"KL {kl:.3f} · {'PASS' if passes else 'FAIL'}", cls="legend", fill=TEAL if passes else RED)

    svg.rect(42, 878, 1116, 30, fill=LIGHT_BLUE, stroke="#b9c7ff", rx=5)
    svg.text(58, 898, "Historical effects only: 5/6 primary contrasts favor the mixer. Qwen repaired screening failed; cross-model binding confirmation remains open.", cls="legend", fill=BLUE)

    rendered = svg.render()
    for p in output_paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(rendered, encoding="utf-8")
        print(f"Generated Figure 8C SVG: {p}")


def build_fig08d_computation_vs_transport(synthesis_path: Path, output_paths: list[Path]):
    """Discovery effects from the repaired synthesis; no claim about computation origin."""
    data = json.loads(synthesis_path.read_text(encoding="utf-8"))
    layers = data["corruptions"]["label_swap"]["layers"]
    svg = SVG(1200, 740, "Figure 8D: Repaired discovery interventions and head-screening gate",
              "Layer 14 label-swap residual, mixer and MLP shifts at four sampled positions, with paired cluster-bootstrap 95% intervals. The repaired Layer 24 citation mixer does not qualify for head screening. Source-label effects alone do not identify evidence binding or linear transport.")
    svg.text(42, 36, "Figure 8D · Repaired discovery interventions", cls="title")
    svg.text(42, 58, "Qwen 2.5 1.5B · 32 semantic examples / 96 format cases · label swap · 1,000 example-cluster bootstrap replicates", cls="muted")
    svg.text(62, 96, "A. Layer 14: effects depend on intervention site", cls="label")
    svg.text(62, 115, "Raw logit shift, natural-log units; whiskers = paired 95% CI", cls="muted")
    x0, y0, width, height = 70, 140, 525, 340
    def y(value):
        return y0 + height - (value + 0.3) / 3.1 * height
    svg.rect(x0, y0, width, height, fill="#ffffff", stroke=GRID)
    for tick in (0, 0.5, 1, 1.5, 2, 2.5):
        svg.line(x0, y(tick), x0 + width, y(tick), stroke=INK if tick == 0 else GRID, width=1)
        svg.text(x0 - 8, y(tick) + 4, f"{tick:.1f}", cls="muted", anchor="end")
    components = [("residual", PURPLE, "Residual"), ("mixer", BLUE, "Mixer"), ("mlp", ORANGE, "MLP")]
    for index, (component, color, name) in enumerate(components):
        svg.circle(90 + index * 155, 535, 5, fill=color)
        svg.text(102 + index * 155, 539, name, cls="legend")
    for index, (position, label) in enumerate([
        ("pos_source_label", "Source label"), ("pos_evidence", "Evidence"),
        ("pos_post_evidence", "Post-evidence"), ("pos_citation", "Citation")
    ]):
        center = x0 + 68 + index * 130
        for offset, (component, color, _) in zip((-25, 0, 25), components):
            stat = layers["14"][position][component]
            mean = stat["abs_shift_first"]
            low, high = stat["shift_ci_95"]
            px = center + offset
            svg.line(px, y(low), px, y(high), stroke=color, width=2)
            svg.line(px - 4, y(low), px + 4, y(low), stroke=color)
            svg.line(px - 4, y(high), px + 4, y(high), stroke=color)
            svg.circle(px, y(mean), 4, fill=color)
        svg.text(center, 505, label, cls="legend", anchor="middle")
    svg.text(640, 96, "B. Repaired citation-position mixer gate", cls="label")
    svg.rect(640, 140, 518, 402, fill="#ffffff", stroke=GRID, rx=7)
    stat = layers["24"]["pos_citation"]["mixer"]
    mean = stat["abs_shift_first"]
    low, high = stat["shift_ci_95"]
    for ypos, text, cls in [
        (173, "Layer 24 · pos_citation · distinguishing token (d−1)", "label"),
        (209, f"Mixer shift: {mean:+.3f} [{low:+.3f}, {high:+.3f}]", "title"),
        (242, "Interval spans zero; positive-control gate did not qualify.", "legend"),
        (266, "Head-level screening stopped under the registered rule.", "legend"),
        (308, "Scope of the result", "label"),
        (333, "Other heads, layers and positions remain open questions.", "muted"),
        (357, "Historical Stage 7B and repaired discovery use different", "muted"),
        (378, "cohorts and implementations; this is not a paired repair effect.", "muted"),
        (420, "Source-label patching precedes relevant evidence.", "label"),
        (446, "An identifier-identity or copying effect can occur there", "muted"),
        (467, "without isolating evidence–identifier binding.", "muted"),
        (502, "Computation versus transport remains unresolved.", "label"),
    ]:
        svg.text(660, ypos, text, cls=cls)
    svg.rect(62, 578, 1096, 120, fill=LIGHT_BLUE, stroke="#b9c7ff", rx=7)
    source = layers["14"]["pos_source_label"]["residual"]
    low, high = source["shift_ci_95"]
    svg.text(82, 606, f"Source-label residual: {source['abs_shift_first']:+.3f} [{low:+.3f}, {high:+.3f}]", cls="label")
    svg.text(82, 632, "Large residual-patch effects do not prove direct transport from embeddings, linear computation, or the first site of binding.", cls="legend")
    svg.text(82, 658, "Discovery position effects motivate further tests; they do not validate the later fitted subspace.", cls="legend")
    for path in output_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(svg.render(), encoding="utf-8")
        print(f"Generated Figure 8D SVG: {path}")


def build_fig08e_subspace_confirmation(confirmation_synthesis_path: Path, bridge_synthesis_path: Path,
                                     output_paths: list[Path], validation_synthesis_path: Path):
    """Use audited V2 artifacts, including paired behavioral effects rather than prevalence claims."""
    confirmation = json.loads(confirmation_synthesis_path.read_text(encoding="utf-8"))
    validation = json.loads(validation_synthesis_path.read_text(encoding="utf-8"))
    bridge = json.loads(bridge_synthesis_path.read_text(encoding="utf-8"))
    svg = SVG(1200, 740, "Figure 8E: Audited subspace outcome and paired behavioral effects",
              "No rank passed registered validation. Raw logit shifts on the consumed confirmation cohort are exploratory. Recovery ratios are unavailable under the audited denominator guard. Clean and patched counterfactual citations have zero paired transitions in 96 cases.")
    svg.text(42, 36, "Figure 8E · No qualified rank; no observed counterfactual citation redirection", cls="title")
    svg.text(42, 58, "Qwen 2.5 1.5B · Layer 14 post-evidence · audited V2 summaries · paired 95% CIs, 1,000 example-cluster bootstrap replicates", cls="muted")
    svg.text(52, 96, "A. Exploratory raw logit shifts (80 examples / 240 cases)", cls="label")
    svg.rect(52, 118, 548, 424, fill="#ffffff", stroke=GRID, rx=6)
    # Horizontal forest plot: labels and numeric intervals remain readable at blog width.
    def x(value):
        return 144 + (value + 0.01) / 0.065 * 228
    for tick in (0, 0.02, 0.04):
        svg.line(x(tick), 151, x(tick), 443, stroke=INK if tick == 0 else GRID, width=1)
        svg.text(x(tick), 467, f"{tick:+.2f}", cls="muted", anchor="middle")
    for index, (rank, stat) in enumerate(confirmation["rank_summaries"].items()):
        cy = 184 + index * 54
        low, high = stat["shift_ci_95"]
        svg.text(68, cy + 4, f"k={rank}", cls="label")
        svg.line(x(low), cy, x(high), cy, stroke=BLUE, width=2.5)
        svg.line(x(low), cy - 5, x(low), cy + 5, stroke=BLUE)
        svg.line(x(high), cy - 5, x(high), cy + 5, stroke=BLUE)
        svg.circle(x(stat["shift_mean"]), cy, 5, fill=BLUE)
        svg.text(390, cy + 4, f"{stat['shift_mean']:+.4f} [{low:+.4f}, {high:+.4f}]", cls="legend")
    svg.text(74, 501, "No rank was frozen. This cohort is exploratory and consumed.", cls="legend")
    svg.text(74, 523, "Positive raw shifts do not meet the registered recovery criterion.", cls="muted")
    svg.text(634, 96, "B. Validation gate and denominator limits", cls="label")
    svg.rect(634, 118, 524, 180, fill=LIGHT_BLUE, stroke="#b9c7ff", rx=6)
    thresholds = validation["preregistered_thresholds"]
    ranks = list(validation["rank_summaries"].values())
    n_qualified = sum(r["qualifies_preregistered_rule"] for r in ranks)
    svg.text(652, 147, f"{n_qualified}/{len(ranks)} validation ranks qualified · no rank selected or frozen", cls="label")
    svg.text(652, 174, f"Required: recovery ≥ {thresholds['min_recovery_pct']:.0f}% and margin ≥ {thresholds['min_margin_pct']:.0f} percentage points.", cls="legend")
    svg.text(652, 201, "Validation ratio CIs: unidentifiable under post-audit policy.", cls="legend")
    denom = next(iter(confirmation["rank_summaries"].values()))
    svg.text(652, 228, f"Confirmation: {denom['eligible_denominator_rows']}/{denom['total_rows']} eligible; mean denominator {denom['aggregate_denominator_mean']:+.4f}.", cls="legend")
    svg.text(652, 254, "Below the absolute 0.5 guard: aggregate ratios unavailable.", cls="legend")
    svg.text(652, 280, "Basis fitted on all formats; unseen-format transfer was not tested.", cls="muted")
    svg.text(634, 332, "C. Free generation (32 examples / 96 cases; rank 8)", cls="label")
    svg.rect(634, 352, 524, 190, fill="#ffffff", stroke=GRID, rx=6)
    for px, label in [(650, "Metric"), (898, "Clean"), (973, "Patched"), (1100, "Δ (pp)")]:
        svg.text(px, 378, label, cls="label", anchor="end" if px > 650 else "start")
    for index, (key, label) in enumerate([
        ("answer_em", "Answer exact match"), ("cites_counterfactual", "Counterfactual citation"),
        ("answer_correct_with_counterfactual_citation", "Correct answer + counterfactual cite"),
        ("cites_gold", "Gold citation"), ("citation_precision", "Citation precision")
    ]):
        stat = bridge["paired_effects"][key]
        cy = 408 + index * 26
        svg.text(650, cy, label, cls="muted")
        for px, value in [(898, f"{stat['clean_prevalence_pct']:.2f}%"),
                          (973, f"{stat['patched_prevalence_pct']:.2f}%"),
                          (1100, f"{stat['paired_mean_diff_pct']:+.2f}")]:
            svg.text(px, cy, value, cls="legend", anchor="end")
    cf = bridge["paired_effects"]["cites_counterfactual"]
    precision = bridge["paired_effects"]["citation_precision"]
    low, high = precision["paired_ci_95"]
    svg.rect(52, 574, 1106, 126, fill=LIGHT_TEAL, stroke="#86d3c8", rx=7)
    svg.text(72, 601, f"Counterfactual citation transitions: 0→1 = {cf['transitions']['0->1']}; 1→0 = {cf['transitions']['1->0']}. Paired difference 0.00 pp [0.00, 0.00].", cls="label")
    svg.text(72, 626, "The same eight cases have correct answers plus counterfactual citations before and after patching; 8.33% is baseline prevalence.", cls="legend")
    svg.text(72, 652, f"Citation precision change: {precision['paired_mean_diff_pct']:+.2f} pp [{low:+.2f}, {high:+.2f}]. Equal answer EM does not establish equal text or fluency.", cls="legend")
    svg.text(72, 678, "Scope: this tested linear difference basis failed qualification; other binding mechanisms remain open questions.", cls="legend")
    for path in output_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(svg.render(), encoding="utf-8")
        print(f"Generated Figure 8E SVG: {path}")


def main():
    parser = argparse.ArgumentParser(description="Build circuit localization figures")
    parser.add_argument("--analysis", default="results/circuit/confirmation_qwen25_15b_analysis.json")
    args = parser.parse_args()

    analysis_p = ROOT / args.analysis
    synthesis_p = ROOT / "results/circuit/cross_model_circuit_synthesis.json"
    rep_synthesis_p = ROOT / "results/circuit/sequence3_work/qwen25_computation_vs_transport_discovery_n32_synthesis_repaired.json"
    subspace_conf_p = ROOT / "results/circuit/sequence3_work/qwen25_subspace_confirmation_synthesis_exploratory_audited_v2.json"
    bridge_p = ROOT / "results/circuit/sequence3_work/qwen25_behavioral_bridge_synthesis_audited_v2.json"

    # Figure 8A
    out_8a = [OUT_ASSETS / "08a_component_dissociation.svg", OUT_SITE / "08a_component_dissociation.svg"]
    if analysis_p.exists():
        build_fig08a_component_dissociation(analysis_p, out_8a)

    # Figure 8B
    out_8b = [OUT_ASSETS / "08b_circuit_wiring_diagram.svg", OUT_SITE / "08b_circuit_wiring_diagram.svg"]
    build_fig08b_circuit_wiring(out_8b)

    # Figure 8C
    out_8c = [OUT_ASSETS / "08c_cross_model_circuit_comparison.svg", OUT_SITE / "08c_cross_model_circuit_comparison.svg"]
    if synthesis_p.exists():
        build_fig08c_cross_model_comparison(synthesis_p, out_8c)

    # Figure 8D
    out_8d = [OUT_ASSETS / "08d_computation_vs_transport.svg", OUT_SITE / "08d_computation_vs_transport.svg"]
    build_fig08d_computation_vs_transport(rep_synthesis_p, out_8d)

    # Figure 8E
    out_8e = [OUT_ASSETS / "08e_subspace_confirmation.svg", OUT_SITE / "08e_subspace_confirmation.svg"]
    build_fig08e_subspace_confirmation(
        subspace_conf_p, bridge_p, out_8e,
        ROOT / "results/circuit/sequence3_work/qwen25_subspace_validation_synthesis_audited_v2.json",
    )


if __name__ == "__main__":
    main()
