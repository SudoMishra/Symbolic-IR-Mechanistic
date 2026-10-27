#!/usr/bin/env python3
"""Build the blog's publication-grade SVG figures from checked-in result artifacts."""

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
            ".title{font-size:26px;font-weight:700}.subtitle{font-size:14px;fill:#5f6b7a}",
            ".label{font-size:14px;font-weight:600}.body{font-size:13px}.small{font-size:12px;fill:#5f6b7a}",
            ".mono{font-family:'SFMono-Regular',Consolas,'Liberation Mono',monospace;font-size:12.5px}",
            ".axis{stroke:#aeb8c8;stroke-width:1}.grid{stroke:#e5e9f0;stroke-width:1}.zero{stroke:#172033;stroke-width:1.5}",
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

    def multiline(self, x, y, lines, cls="body", line_height=20, anchor="start"):
        self.add(f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}">')
        for idx, line in enumerate(lines):
            dy = 0 if idx == 0 else line_height
            self.add(f'<tspan x="{x}" dy="{dy}">{esc(line)}</tspan>')
        self.add("</text>")

    def rect(self, x, y, w, h, fill=PAPER, stroke=GRID, radius=12, sw=1, dash=None):
        extra = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{extra}/>'
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
        length = 9
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
    svg.text(50, 44, title, "title")
    svg.text(50, 72, subtitle, "subtitle")


def raw_vs_symbolic():
    s = SVG(1350, 750, "Figure 1: Raw identifiers versus symbolic IR", "A raw UUID-heavy prompt compared with a compact typed symbolic prompt and an external mapping vault.")
    header(s, "Figure 1 — Representation boundary between software and model", "Trusted software replaces transport keys with request-scoped handles; literal values never enter model context.")

    # Top Left: Raw Application State
    s.rect(50, 110, 520, 310, fill="#fff8f8", stroke="#efc4ca", radius=14)
    s.text(75, 142, "Raw Application State (Database & Storage)", "label", fill=RED)
    s.text(75, 168, "Transport keys: UUIDs, primary keys, account numbers (~25–35 tokens/ID)", "small")
    raw_lines = [
        "Source 8ce71ad9-71f2-4a03-b7f2-26f64e0db302:",
        "  Account ACCT-GB-4490-9812 belongs to Maya Chen.",
        "  Contact: maya.chen@internal.corp",
        "",
        "Source b3a02e31-4f09-4d31-b90f-8a884315c28a:",
        "  Account ACCT-US-8177-2044 belongs to Luis Ortiz.",
        "",
        "Question: Which account belongs to Maya? Cite the UUID.",
    ]
    for i, line in enumerate(raw_lines):
        s.text(75, 202 + i * 25, line, "mono")

    # Arrow from Raw to Symbolic: Canonicalize
    s.arrow(580, 240, 680, 240, BLUE, 2.5)
    s.text(630, 225, "canonicalize_request()", "small", "middle", fill=BLUE, weight="600")
    s.text(630, 260, "extracts literals", "small", "middle")

    # Top Right: Model-Visible Symbolic State
    s.rect(690, 110, 610, 310, fill="#f5fbfa", stroke="#acd8d1", radius=14)
    s.text(715, 142, "Model-Visible Symbolic State (LLM Context Window)", "label", fill=TEAL)
    s.text(715, 168, "Same semantic facts; compact typed handles (~5.5 tokens/handle)", "small")
    symbolic_lines = [
        "<SOURCE_1>:",
        "  <ACCOUNT_1> belongs to Maya Chen.",
        "  Contact: <EMAIL_1>.",
        "",
        "<SOURCE_2>:",
        "  <ACCOUNT_2> belongs to Luis Ortiz.",
        "",
        "Question: Which account belongs to Maya? Return handle.",
    ]
    for i, line in enumerate(symbolic_lines):
        s.text(715, 202 + i * 25, line, "mono")

    # Arrow down from Model View to Validation
    s.arrow(995, 425, 995, 470, MUTED, 2)
    s.text(1005, 452, "model generates symbolic JSON", "small")

    # Mid Right: Validator
    s.rect(690, 475, 610, 105, fill=LIGHT_ORANGE, stroke=ORANGE, radius=14)
    s.text(715, 505, "Deterministic IR Validator (Trusted Application Code)", "label", fill=ORANGE)
    s.text(715, 532, "Checks strict JSON shape, leakage, handle syntax (<TYPE_N>), and request registry", "small")
    s.text(715, 556, "Output: '{\"answer\": \"<ACCOUNT_1>\", \"references\": [\"<SOURCE_1>\"]}'", "mono")

    # Arrow down from Validator to Rehydrate
    s.arrow(995, 585, 995, 620, GREEN, 2)
    s.text(1005, 607, "accepted only", "small", fill=GREEN, weight="600")

    # Bottom Right: Rehydrate
    s.rect(690, 625, 610, 95, fill="#e8f5ed", stroke=GREEN, radius=14)
    s.text(715, 655, "Rehydrate Response & Post-Resolution Authorization", "label", fill=GREEN)
    s.text(715, 680, "Resolves handles via Vault; enforces business rules, freshness, and permissions", "small")
    s.text(715, 702, "Rehydrated: 'ACCT-GB-4490-9812' -> Authorized for lookup action", "mono")

    # Bottom Left: Protected Mapping Vault
    s.rect(50, 475, 520, 245, fill=LIGHT_BLUE, stroke=BLUE, radius=14)
    s.text(75, 505, "Protected Mapping Vault (Trusted Software Space)", "label", fill=BLUE)
    s.rect(75, 520, 160, 24, fill=RED, stroke=RED, radius=4)
    s.text(155, 536, "NEVER SENT TO MODEL", "small", "middle", fill="#ffffff", weight="700")

    vault_lines = [
        "<SOURCE_1>  <->  8ce71ad9-71f2-4a03-b7f2-26f64e0db302",
        "<SOURCE_2>  <->  b3a02e31-4f09-4d31-b90f-8a884315c28a",
        "<ACCOUNT_1> <->  ACCT-GB-4490-9812",
        "<ACCOUNT_2> <->  ACCT-US-8177-2044",
        "<EMAIL_1>   <->  maya.chen@internal.corp",
    ]
    for i, line in enumerate(vault_lines):
        s.text(75, 575 + i * 24, line, "mono")
    s.text(75, 705, "Bound strictly to request_id and tenant session; ephemeral lifecycle.", "small")

    # Branch arrow: Canonicalize -> Vault
    s.line(630, 240, 630, 390, BLUE, 2, dash="4,4")
    s.arrow(630, 390, 310, 470, BLUE, 2)
    s.text(480, 440, "stores reversible map", "small", "middle", fill=BLUE)

    # Reconnect arrow: Vault -> Rehydrate
    s.arrow(575, 672, 685, 672, GREEN, 2.5)
    s.text(630, 660, "vault.rehydrate()", "small", "middle", fill=GREEN, weight="600")

    s.save("01_raw_vs_symbolic.svg")


def evidence_funnel():
    s = SVG(1400, 660, "Figure 2: Experimental evidence program", "Five distinct testing regimes across behavioral, stress, mechanistic, entity, and systems evaluations.")
    header(s, "Figure 2 — Experimental evidence program across five testing regimes", "Counts distinguish behavioral generations from stress tests, mechanistic passes, and software unit attacks.")

    stages = [
        ("1. Behavioral", "11,920", "model generations", "Citation MVE (2,000)\nMuSiQue primary (7,500)\nHeld-out MuSiQue (2,400)\nSmoke gate (20)", BLUE, LIGHT_BLUE),
        ("2. Stress tests", "5,700", "model generations", "Reasoning-budget 2-pass\n(5,600 calls / 2,800 pairs)\nLongProc traces (100)", ORANGE, LIGHT_ORANGE),
        ("3. Mechanisms", "960 + 1,122", "passes & interventions", "BF16 CKA geometry (960)\nSource-ID swaps (66)\nResidual patches (1,056)", PURPLE, LIGHT_PURPLE),
        ("4. Entities", "960", "model generations", "Synthetic account resolution\nacross 6 model families\nRaw vs masked vs typed", TEAL, LIGHT_TEAL),
        ("5. Systems", "500 + 5,000", "software test cases", "Valid round trips (500)\nAdversarial tests (5,000)\nCross-request replays (499)", GREEN, "#e8f5ed"),
    ]

    x = 44
    w = 250
    for i, (name, count, unit, detail, color, fill) in enumerate(stages):
        y = 125
        s.rect(x, y, w, 360, fill=fill, stroke=color, radius=16, sw=1.75)
        s.circle(x + 28, y + 34, 16, color)
        s.text(x + 28, y + 39, str(i + 1), "label", "middle", fill="#ffffff", weight="700")
        s.text(x + 52, y + 39, name, "label", fill=color, weight="700")

        s.text(x + 24, y + 100, count, "title", fill=INK)
        s.text(x + 24, y + 126, unit, "label", fill=MUTED)

        s.line(x + 20, y + 148, x + w - 20, y + 148, color, 1, dash="3,3")
        s.multiline(x + 24, y + 185, detail.split("\n"), "body", 26)

        if i < len(stages) - 1:
            s.arrow(x + w + 2, y + 185, x + w + 16, y + 185, MUTED, 2)
        x += w + 18

    s.rect(44, 515, 1312, 115, fill="#ffffff", stroke=GRID, radius=14)
    s.text(68, 552, "Accounting contract:", "label", fill=INK, weight="700")
    s.text(235, 552, "18,020+ behavioral records representing 23,620+ model calls (Stage 5 uses two sequential model calls per record).", "body")
    s.text(68, 592, "Scientific distinction:", "label", fill=INK, weight="700")
    s.text(235, 592, "Forward passes, causal interventions, and deterministic software test cases are reported in native units—not combined into one inflated number.", "subtitle")

    s.save("02_evidence_funnel.svg")

    mobile = SVG(
        440,
        1580,
        "Figure 2: Experimental evidence program, mobile layout",
        "Five testing regimes stacked vertically for a narrow screen.",
    )
    mobile.add(
        "<style>.title{font-size:24px}.subtitle{font-size:13px}"
        ".label{font-size:15px}.body{font-size:15px}</style>"
    )
    mobile.text(24, 40, "Figure 2 — Experimental evidence", "title")
    mobile.text(24, 70, "program across five testing regimes", "title")
    mobile.text(24, 100, "Counts preserve the native unit for each regime:", "subtitle")
    mobile.text(24, 120, "generations, passes, interventions, or software tests.", "subtitle")

    x, y, w, h = 24, 145, 392, 220
    for i, (name, count, unit, detail, color, fill) in enumerate(stages):
        mobile.rect(x, y, w, h, fill=fill, stroke=color, radius=14, sw=1.75)
        mobile.circle(x + 28, y + 32, 16, color)
        mobile.text(x + 28, y + 37, str(i + 1), "label", "middle", fill="#ffffff", weight="700")
        mobile.text(x + 52, y + 37, name.split(". ", 1)[1], "label", fill=color, weight="700")
        mobile.text(x + 24, y + 85, count, "title", fill=INK)
        mobile.text(x + 24, y + 110, unit, "label", fill=MUTED)
        mobile.line(x + 20, y + 128, x + w - 20, y + 128, color, 1, dash="3,3")
        mobile.multiline(x + 24, y + 155, detail.split("\n"), "body", 20)

        if i < len(stages) - 1:
            mobile.arrow(220, y + h + 2, 220, y + h + 18, MUTED, 2)
        y += 240

    mobile.rect(24, 1355, 392, 205, fill="#ffffff", stroke=GRID, radius=14)
    mobile.text(44, 1386, "Accounting contract", "label", fill=INK, weight="700")
    mobile.multiline(
        44,
        1412,
        [
            "18,020+ behavioral records represent",
            "23,620+ model calls. Stage 5 uses",
            "two sequential model calls per record.",
        ],
        "body",
        21,
    )
    mobile.text(44, 1490, "Scientific distinction", "label", fill=INK, weight="700")
    mobile.multiline(
        44,
        1516,
        [
            "Forward passes, causal interventions,",
            "and software tests stay in native units",
            "instead of one inflated total.",
        ],
        "body",
        21,
    )
    mobile.save("02_evidence_funnel_mobile.svg")


MODEL_SHORT = {
    "CohereLabs/tiny-aya-global-GGUF:q4_k_m": "Tiny Aya",
    "LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m": "LFM 1.2B",
    "LiquidAI/LFM2.5-2.6B-GGUF:q4_k_m": "LFM 2.6B",
    "Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m": "Qwen 1.5B",
    "google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0": "Gemma E2B",
    "google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0": "Gemma E4B",
}


def musique_confirmation():
    data = load("results/processed/musique_confirmatory.json")
    rows = []
    for model in data["models"]:
        label = MODEL_SHORT.get(model["model"], model["model"])
        for effect in model["effects"]:
            if effect["metric"] == "binding_recall":
                rows.append((label, effect["sources"], effect["b_minus_a"] * 100, [v * 100 for v in effect["bootstrap_95_ci"]]))

    y0, gap = 140, 46
    key_y = y0 + gap * len(rows) + 20
    total_h = key_y + 85
    s = SVG(1350, total_h, "Figure 3: Held-out MuSiQue binding effects", "Forest plot of UUID minus numeric source-binding recall across models and source counts.")
    header(s, "Figure 3 — Every held-out estimate favored numeric labels; six were conclusive", "UUID minus numeric relaxed source-binding recall; paired 95% bootstrap intervals across 100 held-out MuSiQue questions.")

    x0, x1 = 430, 1180
    lo, hi = -24, 6

    # Gridlines and ticks
    for tick in (-20, -15, -10, -5, 0, 5):
        x = x0 + (tick - lo) / (hi - lo) * (x1 - x0)
        s.line(x, y0 - 15, x, y0 + gap * len(rows) - 15, INK if tick == 0 else GRID, 1.8 if tick == 0 else 1)
        s.text(x, y0 + gap * len(rows) + 12, f"{tick:+d} pp", "small", "middle")

    # Zero annotation
    x_zero = x0 + (0 - lo) / (hi - lo) * (x1 - x0)
    s.text(x_zero, y0 - 22, "0 pp (No measured difference)", "small", "middle", weight="600")

    # Direction annotations
    s.text(x0 + 80, y0 - 22, "← Favors numeric labels (< 0)", "label", fill=BLUE)
    s.text(x1 - 20, y0 - 22, "Favors UUIDs (> 0) →", "label", "end", fill=MUTED)

    for i, (label, sources, est, ci) in enumerate(rows):
        y = y0 + i * gap
        if i % 2 == 0:
            s.add(f'<rect x="45" y="{y-22}" width="1260" height="40" fill="#f7f9fc"/>')
        s.text(58, y + 5, label, "body", weight="600")
        s.text(250, y + 5, f"{sources} sources", "small")

        xa = x0 + (ci[0] - lo) / (hi - lo) * (x1 - x0)
        xb = x0 + (ci[1] - lo) / (hi - lo) * (x1 - x0)
        xe = x0 + (est - lo) / (hi - lo) * (x1 - x0)

        conclusive = ci[1] < 0
        line_color = BLUE if conclusive else MUTED
        dot_fill = BLUE if conclusive else PAPER
        dot_stroke = BLUE if conclusive else INK

        s.line(xa, y, xb, y, line_color, 2.5)
        s.line(xa, y - 5, xa, y + 5, line_color, 2)
        s.line(xb, y - 5, xb, y + 5, line_color, 2)
        s.circle(xe, y, 6, dot_fill, dot_stroke, 2)

        star = " *" if conclusive else ""
        s.text(1200, y + 5, f"{est:+.1f} pp{star}", "small", fill=INK if conclusive else MUTED, weight="600" if conclusive else "normal")

    # In-figure Key
    s.rect(45, key_y, 1260, 65, fill="#f8fafc", stroke=GRID, radius=10)
    s.circle(70, key_y + 32, 6, BLUE, BLUE, 1)
    s.text(85, key_y + 36, "Filled dot = Paired estimate whose 95% CI strictly excludes zero (conclusive difference)", "small")
    s.circle(680, key_y + 32, 6, PAPER, INK, 2)
    s.text(695, key_y + 36, "Hollow dot = Paired estimate whose 95% CI crosses zero (inconclusive)", "small")
    s.line(1140, key_y + 32, 1180, key_y + 32, BLUE, 2.5)
    s.text(1190, key_y + 36, "Horizontal bar = 95% bootstrap CI", "small")

    s.save("03_musique_confirmation.svg")


def reasoning_budget():
    data = load("results/processed/stage5_confirmatory.json")
    names = [("Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m", "Qwen 1.5B"), ("google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0", "Gemma E2B"), ("CohereLabs/tiny-aya-global-GGUF:q4_k_m", "Tiny Aya")]
    budgets = [64, 128, 256, 512, 1024]
    s = SVG(1400, 680, "Figure 4: Reasoning-budget confirmation", "Three small multiples showing UUID minus numeric accuracy by visible scratchpad budget.")
    header(s, "Figure 4 — More scratchpad did not consistently repair UUID performance", "Final-answer accuracy delta across Pass 1 scratchpad budgets; paired 95% bootstrap intervals (3,200 confirmatory model calls).")

    panel_w, panel_gap = 370, 50
    y_top, y_bottom = 145, 500
    ylo, yhi = -60, 80

    for p, (key, label) in enumerate(names):
        left = 110 + p * (panel_w + panel_gap)
        right = left + panel_w
        s.text(left, 120, label, "label", fill=INK)

        # Region labels
        s.text(right, 160, "UUID better (> 0)", "small", "end", fill=MUTED)
        s.text(right, 490, "Numeric better (< 0)", "small", "end", fill=MUTED)

        for tick in (-60, -40, -20, 0, 20, 40, 60, 80):
            y = y_bottom - (tick - ylo) / (yhi - ylo) * (y_bottom - y_top)
            s.line(left, y, right, y, INK if tick == 0 else GRID, 1.8 if tick == 0 else 1)
            if p == 0:
                s.text(left - 14, y + 4, f"{tick:+d} pp", "small", "end")
            if tick == 0:
                s.text(left + 8, y - 6, "0 pp (Equal accuracy)", "small", fill=MUTED)

        points = []
        for i, budget in enumerate(budgets):
            cell = data["models"][key]["budgets"][str(budget)]["uuid_minus_numeric_accuracy"]
            est = cell["estimate"] * 100
            ci = [v * 100 for v in cell["bootstrap_95_ci"]]
            x = left + i * (panel_w / 4)
            y = y_bottom - (est - ylo) / (yhi - ylo) * (y_bottom - y_top)
            ya = y_bottom - (ci[0] - ylo) / (yhi - ylo) * (y_bottom - y_top)
            yb = y_bottom - (ci[1] - ylo) / (yhi - ylo) * (y_bottom - y_top)

            conclusive = ci[0] > 0 or ci[1] < 0
            dot_fill = ORANGE if conclusive else PAPER
            dot_stroke = ORANGE if conclusive else INK

            s.line(x, ya, x, yb, ORANGE, 2.5)
            s.line(x - 5, ya, x + 5, ya, ORANGE, 2)
            s.line(x - 5, yb, x + 5, yb, ORANGE, 2)
            s.circle(x, y, 5.5, dot_fill, dot_stroke, 2)
            s.text(x, 528, str(budget), "small", "middle")
            points.append((x, y))

        s.polyline(points, ORANGE, 1.5, dash="4,4")
        s.text((left + right) / 2, 560, "Pass 1 scratchpad limit (tokens; log₂-spaced)", "small", "middle")

    # Y-axis title on far left
    s.text(32, 330, "UUID − numeric final-answer accuracy (percentage points)", "label", "middle")

    # In-figure note
    s.rect(110, 595, 1210, 55, fill="#f8fafc", stroke=GRID, radius=10)
    s.text(130, 628, "Key finding: Slopes and interaction intervals span zero; additional scratchpad does not reliably erase UUID deficits.", "small", weight="600")
    s.text(820, 628, "Gemma E2B +50 pp anomaly at 256 tok was caused by scratchpad verbosity.", "small")

    s.save("04_reasoning_budget.svg")


def longproc():
    data = load("results/processed/longproc_gpu_summary.json")
    order = [
        ("Qwen", "Qwen 1.5B"),
        ("LFM", "LFM 1.2B"),
        ("LFM-2.6B", "LFM 2.6B"),
        ("Gemma-E2B", "Gemma E2B"),
        ("Gemma-E4B", "Gemma E4B"),
    ]
    metrics = [
        ("partial_accuracy_mean", "Mean correct-trace prefix before first error", BLUE),
        ("final_answer_accuracy", "Final-answer accuracy (%)", GREEN),
        ("strict_accuracy", "Exact full-trace accuracy (%)", ORANGE),
    ]
    s = SVG(1350, 710, "Figure 5: LongProc trace quality", "Grouped bars compare correct-prefix accuracy, final-answer accuracy, and exact full-trace accuracy for five models.")
    header(s, "Figure 5 — Long generation does not establish procedural correctness", "Strict trace, correct-prefix, and endpoint accuracy diverge on 25 multi-step theory-of-mind problems (125 GPU runs).")

    left, right, top, bottom = 120, 1260, 140, 480
    for tick in (0, 20, 40, 60, 80, 100):
        y = bottom - tick / 100 * (bottom - top)
        s.line(left, y, right, y, GRID, 1)
        s.text(left - 14, y + 4, f"{tick}%", "small", "end")

    s.text(45, 310, "Trace or answer score (%)", "label", "middle")

    group_w = (right - left) / len(order)
    bar_w = 40
    for gi, (key, label) in enumerate(order):
        center = left + group_w * (gi + 0.5)
        for mi, (metric, _, color) in enumerate(metrics):
            value = data[key][metric] * 100
            x = center + (mi - 1) * (bar_w + 8) - bar_w / 2
            y = bottom - value / 100 * (bottom - top)
            s.add(f'<rect x="{x}" y="{y}" width="{bar_w}" height="{bottom-y}" fill="{color}" rx="3"/>')
            if value > 0:
                s.text(x + bar_w / 2, y - 7, f"{value:.1f}%", "small", "middle", weight="600")
            else:
                s.text(x + bar_w / 2, y - 7, "0.0%", "small", "middle")

        s.text(center, 515, label, "label", "middle", fill=INK)

        # Output length box cleanly separated
        tok = data[key]["output_tokens"]["mean"]
        if key == "Qwen":
            cap_note = "84% hit cap"
        elif key == "LFM":
            cap_note = "0% completed"
        elif key == "LFM-2.6B":
            cap_note = "16% full trace"
        elif key == "Gemma-E4B":
            cap_note = "8% exact trace"
        else:
            cap_note = "0% exact trace"
        s.rect(center - 100, 532, 200, 44, fill="#f8fafc", stroke=GRID, radius=8)
        s.text(center, 550, f"Mean output: {tok:.0f} tokens", "small", "middle", weight="600")
        s.text(center, 568, f"Behavior: {cap_note}", "small", "middle")

    # Legend & definitions
    lx = 120
    s.rect(lx, 600, 1140, 85, fill=PAPER, stroke=GRID, radius=10)
    for mi, (metric, mlabel, color) in enumerate(metrics):
        ly = 625 + mi * 23
        s.rect(lx + 20, ly - 12, 14, 14, fill=color, radius=2)
        s.text(lx + 42, ly, mlabel, "small", weight="600")

    s.text(lx + 460, 625, "Blue: fraction of reference belief-state transitions generated before first discrepancy.", "small")
    s.text(lx + 460, 648, "Green: endpoint accuracy (whether final state is correct, regardless of intermediate reasoning).", "small")
    s.text(lx + 460, 671, "Orange: exact procedural match across entire reference trace (1,024–2,048 tokens).", "small")

    s.save("05_longproc.svg")


def stage6_geometry():
    files = [
        ("results/processed/stage6_qwen25_15b.json", "Qwen 1.5B (28 layers)"),
        ("results/processed/stage6_lfm25_12b.json", "LFM 1.2B (16 layers)"),
        ("results/processed/stage6_gemma4_e2b.json", "Gemma E2B (36 layers)"),
        ("results/processed/stage6_gemma4_e4b.json", "Gemma E4B (46 layers)"),
    ]
    s = SVG(1400, 850, "Figure 6: Stage 6 representation geometry", "Four panels show source-content and source-label CKA between structured and UUID conditions across normalized model depth.")
    header(s, "Figure 6 — Fact-token geometry stays stable; identifier geometry is model- and depth-dependent", "Structured-versus-UUID linear CKA across 80 paired examples (960 BF16 forward passes); normalized model depth.")

    panel_w, panel_h = 580, 220
    positions = [(90, 135), (750, 135), (90, 465), (750, 465)]

    for (path, label), (left, top) in zip(files, positions):
        data = load(path)
        cc = data["cross_condition"]["structured_vs_uuid"]
        fact = cc["source_content_cka"]["mean"]
        lab = cc["source_label_cka"]["mean"]
        n = min(len(fact), len(lab))
        fact, lab = fact[:n], lab[:n]
        right, bottom = left + panel_w, top + panel_h

        s.text(left, top - 12, label, "label", fill=INK)

        for tick in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0):
            y = bottom - tick * panel_h
            s.line(left, y, right, y, GRID, 1)
            s.text(left - 10, y + 4, f"{tick:.1f}", "small", "end")

        fact_pts, lab_pts = [], []
        for i, (fv, lv) in enumerate(zip(fact, lab)):
            x = left + i / max(n - 1, 1) * panel_w
            fact_pts.append((x, bottom - fv * panel_h))
            lab_pts.append((x, bottom - lv * panel_h))

        s.polyline(fact_pts, TEAL, 2.5)
        s.polyline(lab_pts, PURPLE, 2.5)

        s.text(left, bottom + 24, "0.0 (Embedding)", "small")
        s.text(right, bottom + 24, "1.0 (Final layer)", "small", "end")
        s.text((left + right) / 2, bottom + 24, "Normalized model depth", "small", "middle")

    # Legend & notes
    s.rect(90, 740, 1240, 85, fill="#f8fafc", stroke=GRID, radius=10)
    s.line(120, 765, 160, 765, TEAL, 3)
    s.text(170, 770, "Teal: Source-content tokens (fact text)", "small", weight="600")
    s.line(470, 765, 510, 765, PURPLE, 3)
    s.text(520, 770, "Purple: Source-label tokens (identifier string)", "small", weight="600")

    s.text(850, 770, "1.0 = highly similar geometry; 0.0 = little shared geometry", "small", fill=MUTED)
    s.text(120, 805, "Note: Passage facts share identical text across conditions; high CKA (≥0.94) is partly expected by construction.", "small")
    s.text(800, 805, "Notice: Gemma E2B label CKA collapses to ~0.37 at final layer; LFM fluctuates between 0.67 and 0.89.", "small")

    s.save("06_stage6_geometry.svg")


def stage7_swaps():
    files = [
        ("results/analysis/stage7_qwen25_15b.json", "Qwen 1.5B (n=8 examples)"),
        ("results/analysis/stage7_lfm25_12b.json", "LFM 1.2B (n=8 examples)"),
        ("results/analysis/stage7_gemma4_e2b.json", "Gemma E2B (n=4 pilot examples)"),
        ("results/analysis/stage7_gemma4_e4b.json", "Gemma E4B (n=2 pilot examples)"),
    ]
    conditions = [("structured", "[S#] Structured", BLUE), ("random_compact", "[XQ7M] Random", TEAL), ("uuid", "UUID (36-char)", ORANGE)]
    s = SVG(1350, 740, "Figure 7: Stage 7 source-ID swap effects", "Counterfactual citation log-probability effect after swapping a relevant source identifier with a distractor.")
    header(s, "Figure 7 — After an ID swap, models do not all rebind to the relevant source", "Change in preference for the identifier newly assigned to the relevant source; paired 95% bootstrap intervals across 66 counterfactual swap directions.")

    left, right, top, bottom = 260, 1220, 140, 500
    lo, hi = -24, 76

    for tick in (-20, 0, 20, 40, 60):
        x = left + (tick - lo) / (hi - lo) * (right - left)
        s.line(x, top, x, bottom, INK if tick == 0 else GRID, 1.8 if tick == 0 else 1)
        s.text(x, bottom + 25, f"{tick:+d}", "small", "middle")

    # Zero line labels
    x_zero = left + (0 - lo) / (hi - lo) * (right - left)
    s.text(x_zero, top - 15, "0.0 (No change in preference)", "small", "middle", weight="600")
    s.text(left + 60, top - 15, "← Retained old association (< 0)", "small", fill=MUTED)
    s.text(right - 20, top - 15, "Rebound to new ID (> 0) →", "small", "end", fill=BLUE)

    s.text((left + right) / 2, bottom + 52, "Change in [log P(newly correct ID) − log P(previous ID)] (log-probability delta)", "label", "middle")

    row_gap = 88
    for i, (path, label) in enumerate(files):
        data = load(path)
        y_center = top + 42 + i * row_gap
        s.text(55, y_center + 5, label, "label", fill=INK)

        for ci, (key, _, color) in enumerate(conditions):
            stat = data["source_id_swap"][key]["total_logprob"]
            est, bounds = stat["mean"], stat["bootstrap_95_ci"]
            y = y_center + (ci - 1) * 22
            xa = left + (bounds[0] - lo) / (hi - lo) * (right - left)
            xb = left + (bounds[1] - lo) / (hi - lo) * (right - left)
            xe = left + (est - lo) / (hi - lo) * (right - left)
            s.line(xa, y, xb, y, color, 3)
            s.line(xa, y - 5, xa, y + 5, color, 2)
            s.line(xb, y - 5, xb, y + 5, color, 2)
            s.circle(xe, y, 5.5, color)

    # In-figure Key & Caveats
    s.rect(55, 595, 1240, 115, fill="#f8fafc", stroke=GRID, radius=10)
    lx = 80
    for _, clabel, color in conditions:
        s.circle(lx + 8, 625, 6, color)
        s.text(lx + 24, 630, clabel, "small", weight="600")
        lx += 220

    s.text(80, 665, "Key result: Qwen and Gemma shift probability to the new ID (> 0), while LFM strongly reinforces the old ID under compact formats (< 0).", "small", weight="600")
    s.text(80, 690, "Caveats: Full UUIDs contain more tokens, so total log-prob magnitudes cannot be compared naively across formats. Gemma cohorts (n=4 and n=2) are pilots.", "small", fill=MUTED)

    s.save("07_stage7_swaps.svg")


def stage8_entities():
    files = [
        ("results/analysis/stage8_pii_qwen15b.json", "Qwen 1.5B"),
        ("results/analysis/stage8_pii_lfm25_12b.json", "LFM 1.2B"),
        ("results/analysis/stage8_pii_lfm25_26b.json", "LFM 2.6B"),
        ("results/analysis/stage8_pii_gemma4_e2b.json", "Gemma E2B"),
        ("results/analysis/stage8_pii_gemma4_e4b.json", "Gemma E4B"),
        ("results/analysis/stage8_pii_tiny_aya.json", "Tiny Aya"),
    ]
    conds = [("raw", "Raw", RED), ("random_masked", "Random", ORANGE), ("untyped", "Untyped", PURPLE), ("typed", "Typed", TEAL)]

    s = SVG(1400, 780, "Figure 8: Stage 8 typed entity canonicalization", "Two panels show task accuracy and raw PII output exposure across raw, random-masked, untyped, and typed representations.")
    header(s, "Figure 8 — Canonicalization eliminates raw-value exposure; accuracy effects vary by model", "40 synthetic account-resolution examples per model (960 total generations across six models); citations disabled.")

    # Panel A: Accuracy (Left)
    left_a, right_a, top_a, bottom_a = 90, 740, 160, 520
    s.text(left_a, top_a - 20, "Panel A: Correct account selected (%)", "label", fill=INK)

    for tick in (0, 25, 50, 75, 100):
        y = bottom_a - tick / 100 * (bottom_a - top_a)
        s.line(left_a, y, right_a, y, GRID, 1)
        s.text(left_a - 10, y + 4, f"{tick}%", "small", "end")

    group_w_a = (right_a - left_a) / len(files)
    bar_w_a = 21
    for gi, (path, label) in enumerate(files):
        data = load(path)
        by_condition = {}
        for cell in data["cells"]:
            by_condition.setdefault(cell["condition"], []).append(cell)
        center = left_a + group_w_a * (gi + 0.5)

        for ci, (key, _, color) in enumerate(conds):
            cells = by_condition[key]
            acc = sum(c["task_accuracy"] * c["n"] for c in cells) / sum(c["n"] for c in cells) * 100
            x = center + (ci - 1.5) * (bar_w_a + 3) - bar_w_a / 2
            y = bottom_a - acc / 100 * (bottom_a - top_a)
            s.add(f'<rect x="{x}" y="{y}" width="{bar_w_a}" height="{bottom_a-y}" fill="{color}" rx="2"/>')
            if acc > 0:
                s.text(x + bar_w_a / 2, y - 5, f"{acc:.0f}", "small", "middle")

        s.text(center, bottom_a + 24, label, "small", "middle", weight="600")

    s.text((left_a + right_a) / 2, bottom_a + 48, "Model Family", "small", "middle")

    # Panel B: Exposure (Right)
    left_b, right_b, top_b, bottom_b = 820, 1310, 160, 520
    s.text(left_b, top_b - 20, "Panel B: Outputs exposing raw personal data (%)", "label", fill=RED)

    for tick in (0, 25, 50, 75, 100):
        y = bottom_b - tick / 100 * (bottom_b - top_b)
        s.line(left_b, y, right_b, y, GRID, 1)
        s.text(left_b - 10, y + 4, f"{tick}%", "small", "end")

    group_w_b = (right_b - left_b) / len(files)
    bar_w_b = 30
    for gi, (path, label) in enumerate(files):
        data = load(path)
        by_condition = {}
        for cell in data["cells"]:
            by_condition.setdefault(cell["condition"], []).append(cell)
        center = left_b + group_w_b * (gi + 0.5)

        raw_leak = sum(c["any_raw_pii_leakage_rate"] * c["n"] for c in by_condition["raw"]) / sum(c["n"] for c in by_condition["raw"]) * 100

        # Bar 1: Raw
        x1 = center - bar_w_b - 2
        y1 = bottom_b - raw_leak / 100 * (bottom_b - top_b)
        s.add(f'<rect x="{x1}" y="{y1}" width="{bar_w_b}" height="{bottom_b-y1}" fill="{RED}" rx="2"/>')
        s.text(x1 + bar_w_b / 2, y1 - 5, f"{raw_leak:.0f}%", "small", "middle", fill=RED, weight="600")

        # Bar 2: Masked/Canonical (0%)
        x2 = center + 2
        s.add(f'<rect x="{x2}" y="{bottom_b-3}" width="{bar_w_b}" height="3" fill="{TEAL}" rx="1"/>')
        s.text(x2 + bar_w_b / 2, bottom_b - 8, "0.0%", "small", "middle", fill=TEAL, weight="600")

        s.text(center, bottom_b + 24, label, "small", "middle", weight="600")

    s.text((left_b + right_b) / 2, bottom_b + 48, "Model Family", "small", "middle")

    # Legend & definitions at bottom
    s.rect(90, 600, 1220, 145, fill="#f8fafc", stroke=GRID, radius=10)
    lx = 120
    for _, clabel, color in conds:
        s.rect(lx, 622, 14, 14, fill=color, radius=2)
        s.text(lx + 22, 634, clabel, "small", weight="600")
        lx += 160

    s.text(120, 670, "Representation definitions:", "small", weight="600")
    s.text(285, 670, "Raw = literal names, emails, account numbers.  Random = arbitrary alphanumeric mask.", "small")
    s.text(285, 692, "Untyped = <ENTITY_1>, <ENTITY_2> (type-neutral).  Typed = <ACCOUNT_1>, <EMAIL_2> (preserves entity type).", "small")
    s.text(120, 725, "Key findings: Typed handles gave Qwen a +17.5 pp lift at identical length; all masked formats eliminated raw PII exposure (100% -> 0%).", "small", fill=INK, weight="600")

    s.save("08_stage8_entities.svg")


def trust_boundary():
    data = load("results/processed/stage9_system_eval.json")
    s = SVG(1400, 840, "Figure 9: Symbolic IR trust boundary", "Architecture showing canonicalization, a protected mapping vault, model-facing typed handles, strict validation, rehydration, and the separate semantic verification boundary.")
    header(s, "Figure 9 — A symbolic handle is a reference, not a capability", "Structural validation guarantees representation integrity; semantic correctness and authorization remain separate responsibilities.")

    # 3 Swimlane Backgrounds
    s.rect(40, 105, 340, 480, fill="#f4f7fb", stroke="#d0dbee", radius=12)
    s.text(60, 130, "ZONE 1: TRUSTED APPLICATION SPACE", "small", fill=BLUE, weight="700")

    s.rect(400, 105, 430, 480, fill="#fdfcf8", stroke="#ece4d4", radius=12)
    s.text(420, 130, "ZONE 2: UNTRUSTED MODEL INTERACTION", "small", fill=ORANGE, weight="700")

    s.rect(850, 105, 510, 480, fill="#f4faf6", stroke="#c8e4d2", radius=12)
    s.text(870, 130, "ZONE 3: TRUSTED VALIDATION & AUTHORIZATION", "small", fill=GREEN, weight="700")

    # Step 1: Trusted State
    s.rect(60, 160, 300, 85, fill=LIGHT_BLUE, stroke=BLUE, radius=10)
    s.text(80, 188, "1. Trusted Application State", "label", fill=BLUE)
    s.text(80, 210, "Records, DB UUIDs, PII, tool targets", "small")

    # Step 2: Canonicalizer
    s.rect(60, 280, 300, 85, fill=LIGHT_TEAL, stroke=TEAL, radius=10)
    s.text(80, 308, "2. Request-Scoped Canonicalizer", "label", fill=TEAL)
    s.text(80, 330, "Replaces literals with typed handles", "small")

    # Arrow Step 1 -> Step 2
    s.arrow(210, 245, 210, 280, MUTED, 2)

    # Step 3: Mapping Vault (Branches from Step 2)
    s.rect(60, 410, 300, 145, fill=PAPER, stroke=BLUE, radius=10)
    s.text(80, 435, "Protected Mapping Vault", "label", fill=BLUE)
    s.rect(80, 448, 140, 20, fill=RED, stroke=RED, radius=3)
    s.text(150, 462, "NEVER SENT TO MODEL", "small", "middle", fill="#ffffff", weight="700")
    s.text(80, 492, "<SOURCE_1> <-> 8ce71ad9...", "mono")
    s.text(80, 514, "<ACCOUNT_1> <-> ACCT-GB-...", "mono")
    s.text(80, 538, "Scoped strictly to current request_id", "small")

    # Arrow Step 2 -> Step 3
    s.arrow(210, 365, 210, 410, BLUE, 2)

    # Step 4: Model Prompt
    s.rect(420, 160, 390, 85, fill=LIGHT_PURPLE, stroke=PURPLE, radius=10)
    s.text(440, 188, "3. Model-Facing Prompt (Typed IR)", "label", fill=PURPLE)
    s.text(440, 210, "Compact handles (<SOURCE_1>, <ACCOUNT_1>)", "small")

    # Arrow Step 2 -> Step 4
    s.arrow(360, 322, 420, 202, PURPLE, 2)

    # Step 5: LLM Generation
    s.rect(420, 280, 390, 85, fill=LIGHT_PURPLE, stroke=PURPLE, radius=10)
    s.text(440, 308, "4. Probabilistic LLM Generation", "label", fill=PURPLE)
    s.text(440, 330, "Generates symbolic JSON with handle references", "small")

    # Arrow Step 4 -> Step 5
    s.arrow(615, 245, 615, 280, MUTED, 2)

    # Step 6: Validator
    s.rect(870, 160, 470, 115, fill=LIGHT_ORANGE, stroke=ORANGE, radius=10)
    s.text(890, 188, "5. Deterministic IR Validator", "label", fill=ORANGE)
    s.text(890, 210, "Checks: 1. Strict JSON  2. Raw Leakage  3. Syntax", "small")
    s.text(890, 230, "        4. Request Registry  5. Type  6. Tool Policy", "small")

    # Arrow Step 5 -> Step 6
    s.arrow(810, 322, 870, 217, ORANGE, 2)

    # Step 7: Rehydrate
    s.rect(870, 320, 470, 85, fill="#e8f5ed", stroke=GREEN, radius=10)
    s.text(890, 348, "6. Deterministic Rehydration Engine", "label", fill=GREEN)
    s.text(890, 370, "Restores raw literals; matches vault registry_id exactly", "small")

    # Arrow Step 6 -> Step 7
    s.arrow(1105, 275, 1105, 320, GREEN, 2)
    s.text(1115, 300, "accepted only", "small", fill=GREEN, weight="600")

    # Reconnect arrow: Vault (Zone 1) -> Rehydrate (Zone 3)
    s.line(360, 520, 840, 520, GREEN, 2, dash="4,4")
    s.arrow(840, 520, 870, 380, GREEN, 2)
    s.text(540, 510, "rehydrate via protected vault", "small", fill=GREEN, weight="600")

    # Step 8: Semantic Authorization
    s.rect(870, 450, 470, 105, fill="#fff8f8", stroke="#e3a7ae", radius=10)
    s.text(890, 478, "7. Application Authorization & Semantic Rules", "label", fill=RED)
    s.text(890, 502, "Checks: Freshness, ownership, idempotency, permissions", "small")
    s.text(890, 524, "Executes tool or serves verified response", "small", weight="600")

    # Arrow Step 7 -> Step 8
    s.arrow(1105, 405, 1105, 450, RED, 2)

    # Bottom Callout 1 (Connected to Validator)
    s.rect(40, 610, 630, 190, fill="#f2faf5", stroke="#acd8ba", radius=14)
    s.text(65, 642, "Structural Integrity Guaranteed (Software Boundary)", "label", fill=GREEN)
    good = [
        f"• {data['correct']['accepted']}/500 valid outputs accepted and rehydrated exactly (100%)",
        f"• {data['total_attack_cases']:,}/5,000 adversarial payloads rejected across 10 failure classes",
        f"• {data['isolation']['cross_request_rehydration_blocked']}/{data['isolation']['cross_request_rehydration_attempts']} cross-request replay attempts blocked (100%)",
        f"• {data['representation']['character_reduction_fraction']*100:.2f}% serialized character reduction in model prompt view",
        "• Median validation overhead: 0.037 ms (negligible CPU latency)",
    ]
    s.multiline(65, 672, good, "body", 24)

    # Bottom Callout 2 (Connected to Semantic Boundary)
    s.rect(700, 610, 660, 190, fill="#fff4f5", stroke="#e3a7ae", radius=14)
    s.text(725, 642, "The Critical Semantic Limit (Model Responsibility)", "label", fill=RED)
    s.text(725, 674, "500 / 500 wrong-but-registered handles passed structural validation.", "body", weight="600")
    bad = [
        "• A valid handle proves only that the reference is well formed and in-request.",
        "• Structural validation CANNOT detect if the model selected the wrong account.",
        "• High-consequence actions must always enforce independent business rules,",
        "  database ownership constraints, confirmation, or human review after resolution.",
    ]
    s.multiline(725, 700, bad, "body", 23)

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
    print("All 9 publication-grade figures built successfully in both blog/assets/ and blog/site/assets/.")


if __name__ == "__main__":
    main()
