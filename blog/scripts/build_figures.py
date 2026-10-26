#!/usr/bin/env python3
"""Build the blog's SVG figures from checked-in result artifacts."""

from __future__ import annotations

import html
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "blog" / "assets"
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
GREEN = "#2d8a57"
LIGHT_BLUE = "#e8edff"
LIGHT_TEAL = "#e2f5f1"
LIGHT_ORANGE = "#fff0e5"
LIGHT_RED = "#fbe9ec"
LIGHT_PURPLE = "#f0ebff"


def load(path: str):
    return json.loads((ROOT / path).read_text())


def esc(value) -> str:
    return html.escape(str(value), quote=True)


class SVG:
    def __init__(self, width: int, height: int, title: str, desc: str):
        self.width = width
        self.height = height
        self.items = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
            f"<title id=\"title\">{esc(title)}</title>",
            f"<desc id=\"desc\">{esc(desc)}</desc>",
            "<style>",
            "text{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;fill:#172033}",
            ".title{font-size:28px;font-weight:700}.subtitle{font-size:15px;fill:#5f6b7a}",
            ".label{font-size:14px;font-weight:600}.body{font-size:14px}.small{font-size:12px;fill:#5f6b7a}",
            ".mono{font-family:'SFMono-Regular',Consolas,'Liberation Mono',monospace;font-size:13px}",
            ".axis{stroke:#aeb8c8;stroke-width:1}.grid{stroke:#e5e9f0;stroke-width:1}.zero{stroke:#172033;stroke-width:1.4}",
            "</style>",
        ]

    def add(self, raw: str):
        self.items.append(raw)

    def text(self, x, y, value, cls="body", anchor="start", fill=None, weight=None):
        attrs = [f'x="{x}"', f'y="{y}"', f'class="{cls}"', f'text-anchor="{anchor}"']
        if fill:
            attrs.append(f'fill="{fill}"')
        if weight:
            attrs.append(f'font-weight="{weight}"')
        self.add(f"<text {' '.join(attrs)}>{esc(value)}</text>")

    def multiline(self, x, y, lines, cls="body", line_height=21, anchor="start"):
        self.add(f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}">')
        for idx, line in enumerate(lines):
            dy = 0 if idx == 0 else line_height
            self.add(f'<tspan x="{x}" dy="{dy}">{esc(line)}</tspan>')
        self.add("</text>")

    def rect(self, x, y, w, h, fill=PAPER, stroke=GRID, radius=12, sw=1):
        self.add(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
        )

    def line(self, x1, y1, x2, y2, stroke=GRID, sw=1, dash=None):
        extra = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{stroke}" stroke-width="{sw}"{extra}/>'
        )

    def circle(self, x, y, r, fill, stroke="none", sw=1):
        self.add(
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}"/>'
        )

    def polyline(self, points, stroke, sw=2.5, fill="none", dash=None):
        pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
        extra = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(
            f'<polyline points="{pts}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"{extra}/>'
        )

    def arrow(self, x1, y1, x2, y2, stroke=INK, sw=2):
        self.line(x1, y1, x2, y2, stroke, sw)
        angle = math.atan2(y2 - y1, x2 - x1)
        length = 10
        for delta in (2.55, -2.55):
            self.line(
                x2,
                y2,
                x2 + length * math.cos(angle + delta),
                y2 + length * math.sin(angle + delta),
                stroke,
                sw,
            )

    def save(self, name: str):
        self.items.append("</svg>")
        OUT.mkdir(parents=True, exist_ok=True)
        OUT_SITE.mkdir(parents=True, exist_ok=True)
        content = "\n".join(self.items) + "\n"
        (OUT / name).write_text(content)
        (OUT_SITE / name).write_text(content)


def header(svg: SVG, title: str, subtitle: str):
    svg.text(50, 48, title, "title")
    svg.text(50, 76, subtitle, "subtitle")


def raw_vs_symbolic():
    s = SVG(1200, 650, "Raw identifiers versus symbolic IR", "A raw UUID-heavy prompt compared with a compact typed symbolic prompt and an external mapping vault.")
    header(s, "Move transport identity out of the reasoning loop", "The model sees compact handles; trusted software retains literal identifiers.")
    s.rect(50, 120, 500, 350, fill="#fff8f8", stroke="#efc4ca")
    s.text(78, 154, "Raw application prompt", "label", fill=RED)
    raw_lines = [
        "Source 8ce71ad9-71f2-4a03-b7f2-26f64e0db302",
        "Account ACCT-GB-4490-9812 belongs to Maya Chen.",
        "Source b3a02e31-4f09-4d31-b90f-8a884315c28a",
        "Account ACCT-US-8177-2044 belongs to Luis Ortiz.",
        "Which account belongs to Maya? Cite the source UUID.",
    ]
    for i, line in enumerate(raw_lines):
        s.text(78, 205 + i * 47, line, "mono")
    s.rect(650, 120, 500, 350, fill="#f5fbfa", stroke="#acd8d1")
    s.text(678, 154, "Model-facing symbolic view", "label", fill=TEAL)
    symbolic_lines = [
        "<SOURCE_1>",
        "<ACCOUNT_1> belongs to Maya Chen.",
        "<SOURCE_2>",
        "<ACCOUNT_2> belongs to Luis Ortiz.",
        "Return the account and supporting source handle.",
    ]
    for i, line in enumerate(symbolic_lines):
        s.text(678, 205 + i * 47, line, "mono")
    s.arrow(565, 290, 635, 290, BLUE, 3)
    s.text(600, 275, "canonicalize", "small", "middle")
    s.rect(340, 520, 520, 90, fill=LIGHT_BLUE, stroke="#b8c5ff")
    s.text(365, 550, "Protected request-scoped mapping vault", "label", fill=BLUE)
    s.text(365, 580, "<SOURCE_1> <-> 8ce71ad9...   |   <ACCOUNT_1> <-> ACCT-GB-4490-9812", "mono")
    s.arrow(740, 470, 740, 515, BLUE, 2)
    s.text(765, 500, "rehydrate only after validation", "small")
    s.save("01_raw_vs_symbolic.svg")


def evidence_funnel():
    s = SVG(1400, 610, "Evidence program", "The sequence and scale of the behavioral, mechanistic, privacy, and systems experiments.")
    header(s, "One engineering question, progressively stronger tests", "Counts keep model generations, forward passes, interventions, and deterministic attacks distinct.")
    stages = [
        ("Behavior", "11,520 generations", "Citation MVE, cross-model controls,\nMuSiQue + held-out replication", BLUE, LIGHT_BLUE),
        ("Stress tests", "5,700 generations", "Reasoning-budget confirmation\nand LongProc traces", ORANGE, LIGHT_ORANGE),
        ("Mechanism", "960 + 1,122", "Paired forward passes, source-ID\nswaps, residual interventions", PURPLE, LIGHT_PURPLE),
        ("Generalize", "800 generations", "Typed entity binding and\nsynthetic exposure reduction", TEAL, LIGHT_TEAL),
        ("System", "500 + 5,000", "Valid round trips and\nadversarial boundary cases", GREEN, "#e8f5ed"),
    ]
    x = 45
    widths = [245, 245, 245, 245, 245]
    for i, (name, count, detail, color, fill) in enumerate(stages):
        w = widths[i]
        y = 150
        s.rect(x, y, w, 290, fill=fill, stroke=color, radius=16, sw=1.5)
        s.circle(x + 34, y + 38, 18, color)
        s.text(x + 34, y + 44, str(i + 1), "label", "middle", fill="#ffffff")
        s.text(x + 62, y + 44, name, "label", fill=color)
        s.text(x + 25, y + 105, count, "label")
        s.multiline(x + 25, y + 155, detail.split("\n"), "body", 25)
        if i < len(stages) - 1:
            s.arrow(x + w + 8, y + 145, x + w + 42, y + 145, MUTED, 2)
        x += w + 35
    s.text(50, 505, "Total behavioral model generations: 18,020, including the 20-record smoke test.", "label")
    s.text(50, 537, "Mechanistic and systems counts are reported separately to avoid inflating the generation total.", "subtitle")
    s.save("02_evidence_funnel.svg")


MODEL_SHORT = {
    "CohereLabs/tiny-aya-global-GGUF:q4_k_m": "Tiny Aya",
    "LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m": "LFM 1.2B",
    "Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m": "Qwen 1.5B",
    "google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0": "Gemma E2B",
    "google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0": "Gemma E4B",
}


def musique_confirmation():
    data = load("results/processed/musique_confirmatory.json")
    rows = []
    for model in data["models"]:
        label = MODEL_SHORT[model["model"]]
        for effect in model["effects"]:
            if effect["metric"] == "binding_recall":
                rows.append((label, effect["sources"], effect["b_minus_a"] * 100, [v * 100 for v in effect["bootstrap_95_ci"]]))
    s = SVG(1250, 720, "Held-out MuSiQue binding effects", "Forest plot of UUID minus numeric source-binding recall across five models and two source counts.")
    header(s, "UUID binding was lower in every held-out cell", "Effect is UUID minus numeric relaxed source-binding recall; 95% paired bootstrap intervals.")
    x0, x1 = 390, 1140
    lo, hi = -24, 6
    y0, gap = 130, 52
    for tick in (-20, -15, -10, -5, 0, 5):
        x = x0 + (tick - lo) / (hi - lo) * (x1 - x0)
        s.line(x, y0 - 18, x, y0 + gap * len(rows) - 18, INK if tick == 0 else GRID, 1.5 if tick == 0 else 1)
        s.text(x, y0 + gap * len(rows) + 8, f"{tick:+d} pp", "small", "middle")
    for i, (label, sources, est, ci) in enumerate(rows):
        y = y0 + i * gap
        if i % 2 == 0:
            s.add(f'<rect x="45" y="{y-26}" width="1150" height="45" fill="#f7f9fc"/>')
        s.text(58, y + 5, label, "body")
        s.text(230, y + 5, f"{sources} sources", "small")
        xa = x0 + (ci[0] - lo) / (hi - lo) * (x1 - x0)
        xb = x0 + (ci[1] - lo) / (hi - lo) * (x1 - x0)
        xe = x0 + (est - lo) / (hi - lo) * (x1 - x0)
        s.line(xa, y, xb, y, BLUE, 3)
        s.line(xa, y - 6, xa, y + 6, BLUE, 2)
        s.line(xb, y - 6, xb, y + 6, BLUE, 2)
        s.circle(xe, y, 6, BLUE)
        s.text(1155, y + 5, f"{est:+.1f}", "small")
    s.text(x0, 675, "← Favors numeric", "label")
    s.text(x1, 675, "Favors UUID →", "label", "end")
    s.save("03_musique_confirmation.svg")


def reasoning_budget():
    data = load("results/processed/stage5_confirmatory.json")
    names = [("Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m", "Qwen 1.5B"), ("google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0", "Gemma E2B"), ("CohereLabs/tiny-aya-global-GGUF:q4_k_m", "Tiny Aya")]
    budgets = [64, 128, 256, 512, 1024]
    s = SVG(1400, 600, "Reasoning-budget confirmation", "Three small multiples showing UUID minus numeric accuracy by visible scratchpad budget.")
    header(s, "More scratchpad did not produce a universal UUID recovery curve", "UUID minus numeric accuracy; paired 95% intervals. Positive values favor UUID.")
    panel_w, panel_gap = 370, 50
    y_top, y_bottom = 135, 480
    ylo, yhi = -60, 80
    for p, (key, label) in enumerate(names):
        left = 100 + p * (panel_w + panel_gap)
        right = left + panel_w
        s.text(left, 115, label, "label")
        for tick in (-60, -40, -20, 0, 20, 40, 60):
            y = y_bottom - (tick - ylo) / (yhi - ylo) * (y_bottom - y_top)
            s.line(left, y, right, y, INK if tick == 0 else GRID, 1.4 if tick == 0 else 1)
            if p == 0:
                s.text(left - 12, y + 4, f"{tick:+d}", "small", "end")
        points = []
        for i, budget in enumerate(budgets):
            cell = data["models"][key]["budgets"][str(budget)]["uuid_minus_numeric_accuracy"]
            est = cell["estimate"] * 100
            ci = [v * 100 for v in cell["bootstrap_95_ci"]]
            x = left + i * (panel_w / 4)
            y = y_bottom - (est - ylo) / (yhi - ylo) * (y_bottom - y_top)
            ya = y_bottom - (ci[0] - ylo) / (yhi - ylo) * (y_bottom - y_top)
            yb = y_bottom - (ci[1] - ylo) / (yhi - ylo) * (y_bottom - y_top)
            s.line(x, ya, x, yb, ORANGE, 2)
            s.line(x - 5, ya, x + 5, ya, ORANGE, 2)
            s.line(x - 5, yb, x + 5, yb, ORANGE, 2)
            s.circle(x, y, 5, ORANGE)
            s.text(x, 508, str(budget), "small", "middle")
            points.append((x, y))
        s.polyline(points, ORANGE, 2)
        s.text((left + right) / 2, 545, "Visible scratchpad cap (tokens)", "small", "middle")
    s.text(42, 310, "Accuracy delta (pp)", "small", "middle")
    s.save("04_reasoning_budget.svg")


def longproc():
    data = load("results/processed/longproc_gpu_summary.json")
    order = [("Qwen", "Qwen"), ("LFM", "LFM"), ("Gemma-E2B", "Gemma E2B"), ("Gemma-E4B", "Gemma E4B")]
    metrics = [("partial_accuracy_mean", "Correct prefix", BLUE), ("final_answer_accuracy", "Final answer", TEAL), ("strict_accuracy", "Exact full trace", ORANGE)]
    s = SVG(1200, 610, "LongProc results", "Grouped bars compare correct-prefix accuracy, final-answer accuracy, and exact full-trace accuracy for four models.")
    header(s, "A correct endpoint can hide a broken reasoning trace", "25 matched LongProc examples per model; all values are percentages.")
    left, right, top, bottom = 100, 1130, 130, 490
    for tick in (0, 20, 40, 60, 80):
        y = bottom - tick / 80 * (bottom - top)
        s.line(left, y, right, y, GRID, 1)
        s.text(left - 12, y + 4, f"{tick}%", "small", "end")
    group_w = (right - left) / len(order)
    bar_w = 46
    for gi, (key, label) in enumerate(order):
        center = left + group_w * (gi + 0.5)
        for mi, (metric, _, color) in enumerate(metrics):
            value = data[key][metric] * 100
            x = center + (mi - 1) * (bar_w + 10) - bar_w / 2
            y = bottom - value / 80 * (bottom - top)
            s.add(f'<rect x="{x}" y="{y}" width="{bar_w}" height="{bottom-y}" fill="{color}"/>')
            s.text(x + bar_w / 2, y - 8, f"{value:.1f}", "small", "middle")
        s.text(center, 523, label, "label", "middle")
        s.text(center, 548, f"mean output {data[key]['output_tokens']['mean']:.0f} tok", "small", "middle")
    lx = 370
    for metric, label, color in metrics:
        s.add(f'<rect x="{lx}" y="575" width="14" height="14" fill="{color}"/>')
        s.text(lx + 22, 587, label, "small")
        lx += 190
    s.save("05_longproc.svg")


def stage6_geometry():
    files = [
        ("results/processed/stage6_qwen25_15b.json", "Qwen"),
        ("results/processed/stage6_lfm25_12b.json", "LFM"),
        ("results/processed/stage6_gemma4_e2b.json", "Gemma E2B"),
        ("results/processed/stage6_gemma4_e4b.json", "Gemma E4B"),
    ]
    s = SVG(1400, 800, "Stage 6 representation geometry", "Four panels show source-content and source-label CKA between structured and UUID conditions across normalized model depth.")
    header(s, "Facts stay aligned while identifier labels converge through the stack", "Structured-versus-UUID linear CKA across 80 paired examples per model.")
    panel_w, panel_h = 600, 230
    positions = [(80, 130), (740, 130), (80, 470), (740, 470)]
    for (path, label), (left, top) in zip(files, positions):
        data = load(path)
        cc = data["cross_condition"]["structured_vs_uuid"]
        fact = cc["source_content_cka"]["mean"]
        lab = cc["source_label_cka"]["mean"]
        n = min(len(fact), len(lab))
        fact, lab = fact[:n], lab[:n]
        right, bottom = left + panel_w, top + panel_h
        s.text(left, top - 15, label, "label")
        for tick in (0.0, 0.5, 1.0):
            y = bottom - tick * panel_h
            s.line(left, y, right, y, GRID, 1)
            s.text(left - 8, y + 4, f"{tick:.1f}", "small", "end")
        fact_pts, lab_pts = [], []
        for i, (fv, lv) in enumerate(zip(fact, lab)):
            x = left + i / max(n - 1, 1) * panel_w
            fact_pts.append((x, bottom - fv * panel_h))
            lab_pts.append((x, bottom - lv * panel_h))
        s.polyline(fact_pts, TEAL, 2.5)
        s.polyline(lab_pts, PURPLE, 2.5)
        s.text(left, bottom + 25, "embedding", "small")
        s.text(right, bottom + 25, "final layer", "small", "end")
    s.line(540, 760, 575, 760, TEAL, 3)
    s.text(585, 765, "source-fact CKA", "small")
    s.line(745, 760, 780, 760, PURPLE, 3)
    s.text(790, 765, "source-label CKA", "small")
    s.save("06_stage6_geometry.svg")


def stage7_swaps():
    files = [
        ("results/analysis/stage7_qwen25_15b.json", "Qwen"),
        ("results/analysis/stage7_lfm25_12b.json", "LFM"),
        ("results/analysis/stage7_gemma4_e2b.json", "Gemma E2B"),
        ("results/analysis/stage7_gemma4_e4b.json", "Gemma E4B"),
    ]
    conditions = [("structured", "[S#]", BLUE), ("random_compact", "[XQ7M]", TEAL), ("uuid", "UUID", ORANGE)]
    s = SVG(1250, 680, "Stage 7 source-ID swap effects", "Counterfactual citation log-probability effect after swapping a relevant source identifier with a distractor.")
    header(s, "The same geometric signature produced different causal behavior", "Positive values follow the relevant source to its new ID; negative values retain the old association.")
    left, right, top, bottom = 175, 1160, 125, 490
    lo, hi = -22, 74
    for tick in (-20, 0, 20, 40, 60):
        x = left + (tick - lo) / (hi - lo) * (right - left)
        s.line(x, top, x, bottom, INK if tick == 0 else GRID, 1.5 if tick == 0 else 1)
        s.text(x, bottom + 28, f"{tick:+d}", "small", "middle")
    s.text((left + right) / 2, bottom + 55, "Source-ID swap effect (log-probability delta)", "small", "middle")
    row_gap = 88
    for i, (path, label) in enumerate(files):
        data = load(path)
        y_center = top + 48 + i * row_gap
        s.text(55, y_center + 5, label, "label")
        for ci, (key, _, color) in enumerate(conditions):
            stat = data["source_id_swap"][key]["total_logprob"]
            est, bounds = stat["mean"], stat["bootstrap_95_ci"]
            y = y_center + (ci - 1) * 21
            xa = left + (bounds[0] - lo) / (hi - lo) * (right - left)
            xb = left + (bounds[1] - lo) / (hi - lo) * (right - left)
            xe = left + (est - lo) / (hi - lo) * (right - left)
            s.line(xa, y, xb, y, color, 3)
            s.circle(xe, y, 5, color)
    lx = 390
    for _, label, color in conditions:
        s.circle(lx, 600, 6, color)
        s.text(lx + 14, 605, label, "small")
        lx += 145
    s.text(55, 645, "Cohorts: Qwen/LFM n=8, Gemma E2B n=4, Gemma E4B n=2 (pilot); positive values follow source to new ID.", "subtitle")
    s.save("07_stage7_swaps.svg")


def stage8_entities():
    files = [
        ("results/analysis/stage8_pii_qwen15b.json", "Qwen"),
        ("results/analysis/stage8_pii_lfm25_12b.json", "LFM"),
        ("results/analysis/stage8_pii_gemma4_e2b.json", "Gemma E2B"),
        ("results/analysis/stage8_pii_gemma4_e4b.json", "Gemma E4B"),
        ("results/analysis/stage8_pii_tiny_aya.json", "Tiny Aya"),
    ]
    conds = [("raw", "Raw", RED), ("random_masked", "Random", ORANGE), ("untyped", "Untyped", PURPLE), ("typed", "Typed", TEAL)]
    s = SVG(1350, 670, "Stage 8 typed entity canonicalization", "Grouped task accuracy bars for raw, random-masked, untyped, and typed entity representations across five models.")
    header(s, "Typed handles improve entity binding for some architectures", "40 synthetic account-resolution examples per model; citations disabled.")
    left, right, top, bottom = 100, 1280, 135, 505
    for tick in (0, 25, 50, 75, 100):
        y = bottom - tick / 100 * (bottom - top)
        s.line(left, y, right, y, GRID, 1)
        s.text(left - 12, y + 4, f"{tick}%", "small", "end")
    group_w = (right - left) / len(files)
    bar_w = 38
    for gi, (path, label) in enumerate(files):
        data = load(path)
        by_condition = {}
        for cell in data["cells"]:
            by_condition.setdefault(cell["condition"], []).append(cell)
        center = left + group_w * (gi + 0.5)
        for ci, (key, _, color) in enumerate(conds):
            cells = by_condition[key]
            acc = sum(c["task_accuracy"] * c["n"] for c in cells) / sum(c["n"] for c in cells) * 100
            x = center + (ci - 1.5) * (bar_w + 6) - bar_w / 2
            y = bottom - acc / 100 * (bottom - top)
            s.add(f'<rect x="{x}" y="{y}" width="{bar_w}" height="{bottom-y}" fill="{color}"/>')
        s.text(center, 540, label, "label", "middle")
        raw_leak = sum(c["any_raw_pii_leakage_rate"] * c["n"] for c in by_condition["raw"]) / sum(c["n"] for c in by_condition["raw"])
        s.text(center, 567, f"raw output exposure {raw_leak*100:.0f}%", "small", "middle")
        s.text(center, 590, "masked exposure 0%", "small", "middle")
    lx = 370
    for _, label, color in conds:
        s.add(f'<rect x="{lx}" y="625" width="14" height="14" fill="{color}"/>')
        s.text(lx + 22, 637, label, "small")
        lx += 150
    s.save("08_stage8_entities.svg")


def trust_boundary():
    data = load("results/processed/stage9_system_eval.json")
    s = SVG(1400, 760, "Symbolic IR trust boundary", "Architecture showing canonicalization, a protected mapping vault, model-facing typed handles, strict validation, rehydration, and the separate semantic verification boundary.")
    header(s, "A symbolic handle is a reference, not a capability", "Stage 9 makes representation integrity deterministic while leaving semantic correctness and authorization explicit.")
    boxes = [
        (55, 150, 210, 115, "Trusted state", ["records, sources, tools"], LIGHT_BLUE, BLUE),
        (330, 150, 220, 115, "Canonicalizer", ["trusted schema", "request-scoped handles"], LIGHT_TEAL, TEAL),
        (620, 150, 220, 115, "LLM view", ["typed handles", "symbolic JSON"], LIGHT_PURPLE, PURPLE),
        (910, 150, 220, 115, "Validator", ["schema + leakage", "registry + type + policy"], LIGHT_ORANGE, ORANGE),
        (1195, 150, 160, 115, "Rehydrate", ["accepted only"], "#e8f5ed", GREEN),
    ]
    for x, y, w, h, title, lines, fill, color in boxes:
        s.rect(x, y, w, h, fill=fill, stroke=color, radius=14, sw=1.5)
        s.text(x + 18, y + 34, title, "label", fill=color)
        s.multiline(x + 18, y + 68, lines, "small", 22)
    for a, b in zip(boxes, boxes[1:]):
        s.arrow(a[0] + a[2] + 8, 207, b[0] - 8, 207, MUTED, 2)
    s.rect(350, 330, 460, 110, fill="#f3f6fb", stroke="#aeb8c8", radius=14)
    s.text(372, 365, "Protected mapping vault", "label")
    s.text(372, 396, "Never enters model context; bound to request and tenant identity", "body")
    s.arrow(440, 272, 440, 322, BLUE, 2)
    s.arrow(720, 322, 720, 272, BLUE, 2)
    s.rect(55, 505, 620, 170, fill="#f2faf5", stroke="#acd8ba", radius=16)
    s.text(80, 540, "Deterministic boundary passed", "label", fill=GREEN)
    good = [
        f"{data['correct']['accepted']}/500 valid outputs accepted and rehydrated exactly",
        f"{data['total_attack_cases']:,} malformed, unknown, cross-type, and policy attacks rejected",
        f"{data['isolation']['cross_request_rehydration_blocked']}/{data['isolation']['cross_request_rehydration_attempts']} cross-request attempts blocked",
        f"{data['representation']['character_reduction_fraction']*100:.2f}% fewer serialized characters",
    ]
    s.multiline(80, 575, good, "body", 24)
    s.rect(725, 505, 630, 170, fill="#fff4f5", stroke="#e3a7ae", radius=16)
    s.text(750, 540, "Semantic boundary remains", "label", fill=RED)
    s.text(750, 580, "500/500 wrong-but-registered account handles passed structure checks.", "body")
    s.text(750, 615, "Correctness, authorization, freshness, and business rules still require", "body")
    s.text(750, 641, "deterministic checks, another verifier, confirmation, or human review.", "body")
    s.save("09_trust_boundary.svg")


def main():
    raw_vs_symbolic()
    evidence_funnel()
    musique_confirmation()
    reasoning_budget()
    longproc()
    stage6_geometry()
    stage7_swaps()
    stage8_entities()
    trust_boundary()


if __name__ == "__main__":
    main()
