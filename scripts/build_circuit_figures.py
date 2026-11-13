#!/usr/bin/env python3
"""Build publication-grade SVG figures for Stage 7B: Component-Level Circuit Localization."""

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
            '.axis {{ stroke: #8c9ba5; stroke-width: 1.2; }}',
            f'.grid {{ stroke: {GRID}; stroke-width: 0.8; stroke-dasharray: 3 3; }}',
            f'.muted {{ fill: {MUTED}; font-size: 11px; }}',
            '.title {{ font-size: 14px; font-weight: 700; }}',
            '.label {{ font-size: 12px; font-weight: 600; }}',
            '.legend {{ font-size: 11px; font-weight: 500; }}',
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

    def text(self, x, y, content, cls="", anchor="start", fill=None):
        fill_attr = f' fill="{fill}"' if fill else ""
        anchor_attr = f' text-anchor="{anchor}"' if anchor != "start" else ""
        self.items.append(f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}"{anchor_attr}{fill_attr}>{esc(content)}</text>')

    def render(self) -> str:
        return "\n".join(self.items) + "\n</svg>\n"


def build_fig08a_component_dissociation(qwen25_analysis_path: Path, output_paths: list[Path]):
    data = json.loads(qwen25_analysis_path.read_text(encoding="utf-8"))
    layers_data = data["layers"]

    svg = SVG(
        width=1000,
        height=540,
        title="Figure 8A: Component-Level Dissociation (Attention vs. MLP)",
        desc="Causal recovery across layer depth for Attention Mixer vs MLP interventions on Qwen 2.5 1.5B (Confirmation Split N=80)"
    )

    svg.text(40, 36, "Figure 8A: Functional Dissociation of Source Binding vs. Continuation", cls="title")
    svg.text(40, 56, "Isolated component transplant on high-powered confirmation cohort (N=80 clusters, 240 cases). Attention mediates binding at Layer 24.", cls="muted")

    # Legend
    svg.rect(610, 22, 350, 42, fill="#f0f4f8", rx=6)
    svg.circle(628, 43, 5, fill=BLUE)
    svg.text(640, 47, "Attention Mixer (B)", cls="legend")
    svg.rect(745, 38, 10, 10, fill=ORANGE, rx=2)
    svg.text(762, 47, "MLP Component (Continuation)", cls="legend")
    svg.line(915, 43, 933, 43, stroke=TEAL, width=2.5, dash="4 2")
    svg.text(939, 47, "Both", cls="legend")

    x0, y0, pw, ph = 70, 110, 400, 350
    svg.text(x0, y0 - 18, "A. First-Token Binding Recovery (%) across Depth", cls="label")
    svg.rect(x0, y0, pw, ph, fill="#ffffff", stroke=GRID)

    y_min, y_max = -20.0, 80.0
    for y_val in [-20, 0, 20, 40, 60, 80]:
        y_pos = y0 + ph - ((y_val - y_min) / (y_max - y_min)) * ph
        svg.line(x0, y_pos, x0 + pw, y_pos, stroke=GRID if y_val != 0 else "#a0aec0", width=1.2 if y_val == 0 else 0.8)
        svg.text(x0 - 8, y_pos + 4, f"{y_val:+d}%" if y_val != 0 else "0%", cls="muted", anchor="end")

    layer_keys = sorted(layers_data.keys(), key=int)
    x_coords = {}
    for i, l_str in enumerate(layer_keys):
        frac = (int(l_str) - 20) / (24 - 20) if len(layer_keys) > 1 else 0.5
        x_pos = x0 + 60 + frac * (pw - 120)
        x_coords[l_str] = x_pos
        svg.line(x_pos, y0 + ph, x_pos, y0 + ph + 5, stroke="#8c9ba5")
        svg.text(x_pos, y0 + ph + 18, f"Layer {l_str}", cls="muted", anchor="middle")

    l24_x = x_coords.get("24", x0 + pw * 0.75)
    svg.rect(l24_x - 35, y0, 70, ph, fill="rgba(49, 94, 251, 0.08)")
    svg.text(l24_x, y0 + 22, "Binding Hub (L24)", cls="muted", anchor="middle", fill=BLUE)

    for comp, color, is_dash in [("both", TEAL, "4 2"), ("mixer", BLUE, None), ("mlp", ORANGE, None)]:
        points = []
        for l_str in layer_keys:
            val = layers_data[l_str][comp].get("recov_first_mean", 0.0)
            val = max(min(val, y_max), y_min)
            y_pos = y0 + ph - ((val - y_min) / (y_max - y_min)) * ph
            points.append((x_coords[l_str], y_pos))
        
        for p1, p2 in zip(points[:-1], points[1:]):
            svg.line(p1[0], p1[1], p2[0], p2[1], stroke=color, width=2.2, dash=is_dash)
        for px, py in points:
            if comp == "mixer":
                svg.circle(px, py, 5.0, fill=color, stroke="#ffffff", stroke_width=1.5)
            elif comp == "mlp":
                svg.rect(px - 4, py - 4, 8, 8, fill=color, rx=1.5)

    x1, y1 = 550, y0
    svg.text(x1, y1 - 18, "B. Double Dissociation: Binding (ΔFirst) vs. Serialization (ΔCont)", cls="label")
    svg.rect(x1, y1, pw, ph, fill="#ffffff", stroke=GRID)

    svg.line(x1 + pw / 2, y1, x1 + pw / 2, y1 + ph, stroke="#a0aec0", width=1.0)
    svg.line(x1, y1 + ph / 2, x1 + pw, y1 + ph / 2, stroke="#a0aec0", width=1.0)
    svg.text(x1 + pw - 10, y1 + ph / 2 - 8, "+ΔFirst (Binding)", cls="muted", anchor="end")
    svg.text(x1 + pw / 2 + 8, y1 + 18, "+ΔCont (Serialization)", cls="muted")

    for l_str in layer_keys:
        for comp, fill, is_circ in [("mixer", BLUE, True), ("mlp", ORANGE, False)]:
            first_shift = layers_data[l_str][comp].get("abs_shift_first", {}).get("mean", 0.0)
            cont_shift = layers_data[l_str][comp].get("abs_shift_cont", {}).get("mean", 0.0)

            px = x1 + pw / 2 + (first_shift / 1.5) * (pw / 2.2)
            py = y1 + ph / 2 - (cont_shift / 1.5) * (ph / 2.2)

            px = max(min(px, x1 + pw - 8), x1 + 8)
            py = max(min(py, y1 + ph - 8), y1 + 8)

            if is_circ:
                svg.circle(px, py, 6.0, fill=fill, stroke="#ffffff", stroke_width=1.5)
                svg.text(px + 8, py + 4, f"L{l_str} Attn ({first_shift:+.2f})", cls="muted", fill=fill)
            else:
                svg.rect(px - 5, py - 5, 10, 10, fill=fill, rx=1.5)
                svg.text(px + 8, py + 4, f"L{l_str} MLP ({first_shift:+.2f})", cls="muted", fill=fill)

    svg.text(x0, y0 + ph + 42, "High-Powered Confirmatory Split: N=80 clusters (240 cases) with cluster-robust 95% CIs. Layer 24 Attention recovers positive binding (+0.701 vs MLP +0.080).", cls="muted")

    rendered = svg.render()
    for p in output_paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(rendered, encoding="utf-8")
        print(f"Generated Figure 8A SVG: {p}")


def build_fig08b_circuit_wiring(output_paths: list[Path]):
    svg = SVG(
        width=1000,
        height=500,
        title="Figure 8B: Working Causal Model: Partial B–F Decomposition (Selection R Untested)",
        desc="Visual model of citation generation: Source-ID Binding (B) and Identifier Continuation (F) are causally tested; Relevant-Source Selection (R) is teacher-forced and untested."
    )

    svg.text(40, 36, "Figure 8B: Working Causal Model: Partial B–F Decomposition", cls="title")
    svg.text(40, 56, "Binding (B) and downstream Continuation (F) are dissociated across 6 architectures; Selection (R) is teacher-forced (untested).", cls="muted")

    # Stage 1: R
    r_x, r_y, rw, rh = 60, 110, 250, 320
    svg.rect(r_x, r_y, rw, rh, fill="#f8fafc", stroke=GRID, rx=6)
    svg.text(r_x + 16, r_y + 28, "Stage 1: Selection (R) [Untested]", cls="label")
    svg.text(r_x + 16, r_y + 46, "Prompt Context Evidence (Teacher-Forced)", cls="muted")
    svg.rect(r_x + 16, r_y + 70, rw - 32, 60, fill="#ffffff", stroke="#cbd5e1", rx=4)
    svg.text(r_x + 26, r_y + 94, "Context Documents {S₁...Sₖ}", cls="legend")
    svg.text(r_x + 26, r_y + 112, "Query attends to evidence fact", cls="muted")
    svg.rect(r_x + 16, r_y + 150, rw - 32, 60, fill="#ffffff", stroke="#cbd5e1", rx=4)
    svg.text(r_x + 26, r_y + 174, "Intermediate Representation", cls="legend")
    svg.text(r_x + 26, r_y + 192, "Semantic truth state S*", cls="muted")
    svg.text(r_x + 16, r_y + 245, "Untested in Stage 7B: prompt answer", cls="muted")
    svg.text(r_x + 16, r_y + 265, "is teacher-forced; R not isolated", cls="muted")

    # Arrow R -> B
    svg.line(r_x + rw, r_y + rh / 2, r_x + rw + 40, r_y + rh / 2, stroke=BLUE, width=2.5)
    svg.text(r_x + rw + 20, r_y + rh / 2 - 8, "S*", cls="muted", anchor="middle")

    # Stage 2: B
    b_x, b_y, bw, bh = 370, 110, 260, 320
    svg.rect(b_x, b_y, bw, bh, fill="#f0f7ff", stroke="#bae6fd", rx=6)
    svg.text(b_x + 16, b_y + 28, "Stage 2: Binding (B) [Confirmed]", cls="label", fill=BLUE)
    svg.text(b_x + 16, b_y + 46, "Late Attention / Mixer Hubs", cls="muted")
    svg.rect(b_x + 16, b_y + 70, bw - 32, 60, fill="#ffffff", stroke=BLUE, rx=4)
    svg.text(b_x + 26, b_y + 94, "Citation Delimiter '['", cls="legend", fill=BLUE)
    svg.text(b_x + 26, b_y + 112, "Attends to source header ID", cls="muted")
    svg.rect(b_x + 16, b_y + 150, bw - 32, 60, fill="#ffffff", stroke=BLUE, rx=4)
    svg.text(b_x + 26, b_y + 174, "Critical Binding Mixers", cls="legend", fill=BLUE)
    svg.text(b_x + 26, b_y + 192, "Qwen L20/L24 | Gemma L35/L36", cls="muted")
    svg.text(b_x + 16, b_y + 245, "Empirical: ΔFirst = +0.70 to +18.07", cls="label", fill=BLUE)
    svg.text(b_x + 16, b_y + 265, "Mixer − MLP 95% CIs strictly > 0", cls="muted")

    # Arrow B -> F
    svg.line(b_x + bw, b_y + bh / 2, b_x + bw + 40, b_y + bh / 2, stroke=ORANGE, width=2.5)
    svg.text(b_x + bw + 20, b_y + bh / 2 - 8, "ID(S*)", cls="muted", anchor="middle")

    # Stage 3: F
    f_x, f_y, fw, fh = 690, 110, 250, 320
    svg.rect(f_x, f_y, fw, fh, fill="#fffaf0", stroke="#fed7aa", rx=6)
    svg.text(f_x + 16, f_y + 28, "Stage 3: Serialization (F) [Confirmed]", cls="label", fill=ORANGE)
    svg.text(f_x + 16, f_y + 46, "Downstream Mixers & MLPs", cls="muted")
    svg.rect(f_x + 16, f_y + 70, fw - 32, 60, fill="#ffffff", stroke=ORANGE, rx=4)
    svg.text(f_x + 26, f_y + 94, "Token Continuation [t₂...tₘ]", cls="legend", fill=ORANGE)
    svg.text(f_x + 26, f_y + 112, "Unpacks multi-token identifiers", cls="muted")
    svg.rect(f_x + 16, f_y + 150, fw - 32, 60, fill="#ffffff", stroke=ORANGE, rx=4)
    svg.text(f_x + 26, f_y + 174, "Late Serialization Components", cls="legend", fill=ORANGE)
    svg.text(f_x + 26, f_y + 192, "Tiny Aya L36 | Qwen4B L28/L32", cls="muted")
    svg.text(f_x + 16, f_y + 245, "Empirical: ΔCont = +0.12 to +1.63", cls="label", fill=ORANGE)
    svg.text(f_x + 16, f_y + 265, "Specificity: 5/6 models pass KL < 1.0", cls="muted")

    rendered = svg.render()
    for p in output_paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(rendered, encoding="utf-8")
        print(f"Generated Figure 8B SVG: {p}")


def build_fig08c_cross_model_comparison(synthesis_path: Path, output_paths: list[Path]):
    data = json.loads(synthesis_path.read_text(encoding="utf-8"))
    models_dict = data.get("models", {})

    svg = SVG(
        width=1000,
        height=560,
        title="Figure 8C: Cross-Model Circuit Topology Comparison",
        desc="Comparative breakdown of binding and continuation causal attribution across all 6 models on confirmation split"
    )

    svg.text(40, 36, "Figure 8C: Cross-Model Circuit Localization across 6 Architectures", cls="title")
    svg.text(40, 56, "Normalized layer depth and component attribution on High-Power Confirmation Split (N=80, 1,440 cases total).", cls="muted")

    # Legend
    svg.rect(680, 22, 280, 42, fill="#f0f4f8", rx=6)
    svg.circle(700, 43, 5, fill=BLUE)
    svg.text(712, 47, "Mixer Binding (ΔFirst)", cls="legend")
    svg.rect(820, 38, 10, 10, fill=ORANGE, rx=2)
    svg.text(837, 47, "MLP Binding", cls="legend")

    x0, y0, pw, ph = 80, 110, 840, 370
    svg.rect(x0, y0, pw, ph, fill="#ffffff", stroke=GRID)

    model_list = [
        ("qwen2.5-1.5b-instruct", "Qwen 2.5 1.5B\n(Pure GQA, 28L)"),
        ("qwen3.5-2b", "Qwen 3.5 2B\n(Hybrid Delta, 24L)"),
        ("tiny-aya-global", "Tiny Aya\n(Asym GQA, 36L)"),
        ("qwen3.5-4b", "Qwen 3.5 4B\n(Hybrid Delta, 32L)"),
        ("gemma-4-e2b-it", "Gemma 4 E2B\n(Asym GQA, 35L)"),
        ("gemma-4-e4b-it", "Gemma 4 E4B\n(Asym PLE, 42L)"),
    ]

    col_w = pw / len(model_list)
    for idx, (mid, mlabel) in enumerate(model_list):
        cx = x0 + idx * col_w + col_w / 2
        svg.line(x0 + idx * col_w, y0, x0 + idx * col_w, y0 + ph, stroke=GRID)

        lines = mlabel.split("\n")
        svg.text(cx, y0 + ph + 18, lines[0], cls="label", anchor="middle")
        svg.text(cx, y0 + ph + 32, lines[1], cls="muted", anchor="middle")

        mdata = models_dict.get(mid, {})
        conf_layers = mdata.get("splits", {}).get("confirmation", {}).get("layers", {})
        hub_layers = mdata.get("hub_layers", [])

        # Find the primary binding hub
        primary_l = str(hub_layers[-1]) if hub_layers else ""
        if mid == "qwen2.5-1.5b-instruct":
            primary_l = "24"
        elif mid == "qwen3.5-2b":
            primary_l = "20"
        elif mid == "tiny-aya-global":
            primary_l = "24"
        elif mid == "qwen3.5-4b":
            primary_l = "24"
        elif mid == "gemma-4-e2b-it":
            primary_l = "35"
        elif mid == "gemma-4-e4b-it":
            primary_l = "36"

        p_info = conf_layers.get(primary_l, {})
        m_first = p_info.get("mixer", {}).get("abs_shift_first", 0)
        mlp_first = p_info.get("mlp", {}).get("abs_shift_first", 0)
        m_cont = p_info.get("mixer", {}).get("abs_shift_cont", 0)

        # Draw bars for Mixer vs MLP First Token shift
        scale = 14.0 if mid == "gemma-4-e4b-it" else 1.2
        bar_max_h = ph * 0.65

        # Normalize height for visualization
        # Use log-like or capped scaling for Gemma 4 E4B so it fits nicely
        h_m = min((m_first / 3.0) * bar_max_h if mid != "gemma-4-e4b-it" else (m_first / 25.0) * bar_max_h, bar_max_h)
        h_mlp = min((max(mlp_first, 0) / 3.0) * bar_max_h if mid != "gemma-4-e4b-it" else (max(mlp_first, 0) / 25.0) * bar_max_h, bar_max_h)

        base_y = y0 + ph - 40
        # Mixer bar
        svg.rect(cx - 28, base_y - h_m, 24, h_m, fill=BLUE, rx=3)
        svg.text(cx - 16, base_y - h_m - 8, f"{m_first:+.2f}", cls="muted", anchor="middle", fill=BLUE)

        # MLP bar
        svg.rect(cx + 4, base_y - h_mlp, 24, h_mlp, fill=ORANGE, rx=3)
        svg.text(cx + 16, base_y - h_mlp - 8, f"{mlp_first:+.2f}", cls="muted", anchor="middle", fill=ORANGE)

        # Layer Label badge
        svg.rect(cx - 36, y0 + 16, 72, 24, fill="#f1f5f9", stroke="#cbd5e1", rx=4)
        svg.text(cx, y0 + 32, f"Hub L{primary_l}", cls="legend", anchor="middle")

        # Dissociation metric with paired cluster CI
        paired_d = data.get("paired_confirmation_dissociation", {}).get(mid, {})
        diff = paired_d.get("mean", m_first - mlp_first)
        ci = paired_d.get("ci_95", [0, 0])
        svg.text(cx, y0 + 58, f"Δ: {diff:+.2f}", cls="label", anchor="middle", fill=BLUE)
        svg.text(cx, y0 + 72, f"[{ci[0]:+.2f}, {ci[1]:+.2f}]", cls="muted", anchor="middle", fill=BLUE)

    svg.text(x0, y0 + ph + 52, "Paired cluster-bootstrap 95% CIs (N=80 clusters, 240 cases each). Gemma 4 E4B specificity limit: D_KL = 3.16 nats > 1.0 threshold.", cls="muted")

    rendered = svg.render()
    for p in output_paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(rendered, encoding="utf-8")
        print(f"Generated Figure 8C SVG: {p}")


def main():
    parser = argparse.ArgumentParser(description="Build circuit localization figures")
    parser.add_argument("--analysis", default="results/circuit/confirmation_qwen25_15b_analysis.json")
    args = parser.parse_args()

    analysis_p = ROOT / args.analysis
    synthesis_p = ROOT / "results/circuit/cross_model_circuit_synthesis.json"

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


if __name__ == "__main__":
    main()
