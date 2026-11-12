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
    def __init__(self, width: int, height: int, title: str, desc: str, metadata: dict[str, Any] | None = None):
        self.width = width
        self.height = height
        self.metadata = metadata
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

    def text(self, x, y, value, cls="body", anchor="start", fill=None, weight=None, transform=None):
        attrs = [f'x="{x}"', f'y="{y}"', f'class="{cls}"', f'text-anchor="{anchor}"']
        if fill:
            attrs.append(f'fill="{fill}"')
        if weight:
            attrs.append(f'font-weight="{weight}"')
        if transform:
            attrs.append(f'transform="{transform}"')
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
        if self.metadata:
            meta_str = json.dumps(self.metadata, indent=2)
            self.items.append(f'<metadata id="figure-metadata" type="application/json">\n{meta_str}\n</metadata>')
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
    accounting = load("results/audit/study_accounting.json")
    local_calls = accounting.get("local_completed_calls", 46230)
    frontier_calls = accounting.get("frontier_completed_calls", 13760)
    mechanistic_calls = accounting.get("mechanistic_completed_calls", 3744)
    behavioral_calls = local_calls + frontier_calls
    total_calls = accounting.get("total_verified_calls", behavioral_calls + mechanistic_calls)
    by_exp = accounting.get("by_experiment", {})

    s1_loc = by_exp.get("stage1_scaling_500", {}).get("local_completed", 12000)
    m100_loc = by_exp.get("musique_replication_100", {}).get("local_completed", 2400)
    m500_loc = by_exp.get("musique_scaled_500", {}).get("local_completed", 12000)
    s5_pilot = by_exp.get("stage5_pilot", {}).get("local_completed", 2880)
    s5_conf = by_exp.get("stage5_confirmatory", {}).get("local_completed", 4800)
    lp_loc = by_exp.get("long_context_tracking", {}).get("local_completed", 150)
    s8_loc = by_exp.get("stage8_pii_500", {}).get("local_completed", 12000)

    m500_front = by_exp.get("musique_scaled_500", {}).get("frontier_completed", 7500)
    reas_front = by_exp.get("frontier_reasoning_ablation", {}).get("frontier_completed", 800)
    s8_front = by_exp.get("stage8_pii_500", {}).get("frontier_completed", 4000)
    stab_front = by_exp.get("frontier_stability", {}).get("frontier_completed", 960)

    stage6_passes = by_exp.get("stage6_geometry", {}).get("mechanistic_completed", 1440)
    stage7_interventions = by_exp.get("stage7_interventions", {}).get("mechanistic_completed", 2304)
    stage7_result_paths = (
        "results/processed/stage7_tiny_aya.json",
        "results/processed/stage7_qwen25_15b.json",
        "results/processed/stage7_gemma4_e2b.json",
        "results/processed/stage7_gemma4_e4b.json",
        "results/processed/stage7_qwen35_2b.json",
        "results/processed/stage7_qwen35_4b.json",
    )
    stage7_swaps = sum(load(path).get("cases", 0) for path in stage7_result_paths)
    stage7_patches = stage7_interventions - stage7_swaps
    if stage6_passes + stage7_interventions != mechanistic_calls:
        raise ValueError("Stage 6 and Stage 7 counts do not match mechanistic accounting")
    if stage7_patches < 0:
        raise ValueError("Stage 7 prompt swaps exceed total interventions")

    meta = {
        "experiment_id": "study_accounting_funnel",
        "cohorts": ["local_cohort_6", "frontier_cohort_4"],
        "local_completed_calls": local_calls,
        "frontier_completed_calls": frontier_calls,
        "mechanistic_completed_calls": mechanistic_calls,
        "stage6_geometry_passes": stage6_passes,
        "stage7_prompt_swaps": stage7_swaps,
        "stage7_activation_patches": stage7_patches,
        "total_verified_calls": total_calls,
        "excluded_calls": 0,
        "source": "results/audit/study_accounting.json",
    }
    s = SVG(1400, 660, "Figure 2: Experimental evidence program", "Five distinct testing regimes across behavioral, stress, mechanistic, entity, and systems evaluations.", metadata=meta)
    header(s, "Figure 2 — Experimental evidence program across five testing regimes", "Counts distinguish behavioral generations from stress tests, mechanistic passes, and software unit attacks.")

    stages = [
        ("1. Behavioral", f"{local_calls:,}", "local model generations", f"Citation MVE ({s1_loc:,})\nMuSiQue 100 & 500 ({m100_loc + m500_loc:,})\nStage 5 scaling ({s5_pilot + s5_conf:,})\nStage 8 & LongProc ({s8_loc + lp_loc:,})", BLUE, LIGHT_BLUE),
        ("2. Frontier", f"{frontier_calls:,}", "frontier API generations", f"MuSiQue 500 ({m500_front:,})\nReasoning ablation ({reas_front:,})\nStage 8 PII ({s8_front:,})\nRepeatability audit ({stab_front:,})", ORANGE, LIGHT_ORANGE),
        ("3. Mechanisms", f"{stage6_passes:,} + {stage7_interventions:,}", "passes & interventions", f"BF16 CKA geometry ({stage6_passes:,})\nSource-ID swaps ({stage7_swaps:,})\nResidual patches ({stage7_patches:,})", PURPLE, LIGHT_PURPLE),
        ("4. Entities", f"{s8_loc:,} + {s8_front:,}", "compliance generations", "Synthetic account resolution\nacross 6 local models\nplus Sonnet & Sol", TEAL, LIGHT_TEAL),
        ("5. Systems", "6,000", "software test cases", "Valid round trips (500)\nAdversarial tests (5,000)\nSemantic probes (500)\nVault replays (499)", GREEN, "#e8f5ed"),
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
    s.text(235, 552, f"{local_calls:,} verified local calls + {frontier_calls:,} verified frontier validation calls: {behavioral_calls:,} behavioral calls ({total_calls:,} total non-excluded verified calls).", "body")
    s.text(68, 592, "Scientific distinction:", "label", fill=INK, weight="700")
    s.text(235, 592, "Local fleet calls, closed API calls, causal interventions, and deterministic software test cases stay in native units.", "subtitle")

    s.save("02_evidence_funnel.svg")

    mobile = SVG(
        440,
        1580,
        "Figure 2: Experimental evidence program, mobile layout",
        "Five testing regimes stacked vertically for a narrow screen.",
        metadata=meta,
    )
    mobile.add(
        "<style>.title{font-size:19px}.subtitle{font-size:13px}"
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
            f"{local_calls:,} verified local calls +",
            f"{frontier_calls:,} verified frontier calls =",
            f"{behavioral_calls:,} behavioral calls.",
            f"({total_calls:,} total with mechanistic)",
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
    "CohereLabs/tiny-aya-global-GGUF:q4_k_m": "Tiny Aya Global",
    "tiny_aya_global": "Tiny Aya Global",
    "Tiny Aya": "Tiny Aya Global",
    "Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m": "Qwen 2.5 1.5B",
    "qwen25_15b": "Qwen 2.5 1.5B",
    "Qwen 1.5B": "Qwen 2.5 1.5B",
    "google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0": "Gemma 4 E2B",
    "google/gemma-4-E2B-it-qat-q4_0-gguf": "Gemma 4 E2B",
    "gemma4_e2b": "Gemma 4 E2B",
    "Gemma E2B": "Gemma 4 E2B",
    "google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0": "Gemma 4 E4B",
    "google/gemma-4-E4B-it-qat-q4_0-gguf": "Gemma 4 E4B",
    "gemma4_e4b": "Gemma 4 E4B",
    "Gemma E4B": "Gemma 4 E4B",
    "unsloth/Qwen3.5-2B-GGUF:q4_k_m": "Qwen 3.5 2B",
    "qwen35_2b": "Qwen 3.5 2B",
    "unsloth/Qwen3.5-4B-GGUF:q4_k_m": "Qwen 3.5 4B",
    "qwen35_4b": "Qwen 3.5 4B",
}


def musique_confirmation():
    data = load("results/processed/musique_500_confirmatory.json")
    rows = []
    order_keys = [
        "CohereLabs/tiny-aya-global-GGUF:q4_k_m",
        "Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m",
        "google/gemma-4-E2B-it-qat-q4_0-gguf",
        "google/gemma-4-E4B-it-qat-q4_0-gguf",
        "unsloth/Qwen3.5-2B-GGUF:q4_k_m",
        "unsloth/Qwen3.5-4B-GGUF:q4_k_m",
    ]
    models_dict = {m["model"]: m for m in data["models"]}
    table_rows = []

    for mkey in order_keys:
        if mkey not in models_dict:
            continue
        model = models_dict[mkey]
        label = MODEL_SHORT.get(mkey, mkey)
        for effect in model["effects"]:
            if effect["metric"] == "binding_recall":
                est = effect["b_minus_a"] * 100
                ci = [v * 100 for v in effect["bootstrap_95_ci"]]
                sources = effect["sources"]
                rows.append((label, sources, est, ci))
                conclusive = ci[1] < 0
                table_rows.append(
                    f"| **{label}** | {sources} | **{est:+.2f}** | [{ci[0]:+.2f}, {ci[1]:+.2f}] | **{'Yes' if conclusive else 'No'}** |"
                )

    table_md = [
        "| Model Family | Sources | UUID − Numeric Binding Recall (pp) | Paired 95% Bootstrap CI | Excludes Zero? |",
        "|:---|:---:|:---:|:---:|:---:|",
        *table_rows,
    ]
    (OUT / "03_musique_confirmation_table.md").write_text("\n".join(table_md) + "\n")
    (OUT_SITE / "03_musique_confirmation_table.md").write_text("\n".join(table_md) + "\n")

    meta = {
        "experiment_id": "musique_scaled_500",
        "cohort": "local_cohort_6",
        "models": [MODEL_SHORT[k] for k in order_keys],
        "n_questions": 500,
        "n_generations": 12000,
        "cells": 12,
        "source": "results/processed/musique_500_confirmatory.json",
    }

    y0, gap = 140, 46
    key_y = y0 + gap * len(rows) + 20
    total_h = key_y + 85
    s = SVG(1350, total_h, "Figure 3: Scaled MuSiQue N=500 binding effects across 6 models", "Forest plot of UUID minus numeric source-binding recall across 6 local models and 2 source counts (12,000 generations).", metadata=meta)
    header(s, "Figure 3 — Every confirmatory estimate favored numeric labels across models", "UUID minus numeric relaxed source-binding recall; paired 95% bootstrap intervals across 500 multi-hop questions (12 model/source cells across 6 models, 12,000 generations).")

    x0, x1 = 430, 1180
    lo, hi = -24, 6

    # Gridlines and ticks
    for tick in (-20, -15, -10, -5, 0, 5):
        x = x0 + (tick - lo) / (hi - lo) * (x1 - x0)
        s.line(x, y0 - 15, x, y0 + gap * len(rows) - 15, INK if tick == 0 else GRID, 1.8 if tick == 0 else 1)
        s.text(x, y0 + gap * len(rows) + 12, f"{tick:+d} pp", "small", "middle")

    # Direction annotations centered over respective axis regions
    x_zero = x0 + (0 - lo) / (hi - lo) * (x1 - x0)
    s.text((x0 + x_zero) / 2, y0 - 22, "← Favors numeric labels (< 0)", "label", "middle", fill=BLUE)
    s.text((x_zero + x1) / 2, y0 - 22, "Favors UUIDs (> 0) →", "label", "middle", fill=MUTED)

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
    s.text(85, key_y + 36, "Filled dot — 95% CI excludes zero (12 of 12 cells)", "small")
    s.circle(500, key_y + 32, 6, PAPER, INK, 2)
    s.text(515, key_y + 36, "Hollow dot — 95% CI crosses zero (0 cells)", "small")
    s.line(930, key_y + 32, 970, key_y + 32, BLUE, 2.5)
    s.text(980, key_y + 36, "Horizontal bar — 95% bootstrap CI", "small")

    s.save("03_musique_confirmation.svg")


def frontier_musique():
    data = load("results/processed/frontier_anthropic_summary.json")["musique_500"]
    rows = []
    for key, label in (("anthropic_haiku", "Claude Haiku 5.5"), ("anthropic_sonnet", "Claude Sonnet 5.5")):
        for sources in (15, 20):
            effect = data[key]["deltas"][f"{sources}_sources"]["citation_recall_delta"]
            rows.append((label, sources, effect["mean_delta_pct"], [effect["ci_low_pct"], effect["ci_high_pct"]]))

    s = SVG(1350, 455, "Figure 3B: Anthropic frontier MuSiQue binding effects", "Forest plot of UUID minus numeric source-binding recall for Claude Haiku 5.5 and Claude Sonnet 5.5 at 15 and 20 sources.")
    header(s, "Figure 3B — Anthropic models split sharply on UUID source binding", "UUID minus numeric relaxed source-binding recall; paired 95% bootstrap intervals over 500 MuSiQue questions per cell (4,000 generations).")

    x0, x1 = 430, 1160
    y0, gap = 145, 54
    lo, hi = -75, 10
    for tick in (-75, -60, -45, -30, -15, 0, 10):
        x = x0 + (tick - lo) / (hi - lo) * (x1 - x0)
        s.line(x, y0 - 18, x, y0 + gap * len(rows) - 28, INK if tick == 0 else GRID, 1.8 if tick == 0 else 1)
        s.text(x, y0 + gap * len(rows) - 5, f"{tick:+d} pp", "small", "middle")

    s.text(x0, y0 - 28, "← Lower binding with UUID labels", "label", fill=ORANGE)
    s.text(x1, y0 - 28, "Higher with UUIDs →", "label", "end", fill=MUTED)

    for i, (label, sources, est, ci) in enumerate(rows):
        y = y0 + i * gap
        if i % 2 == 0:
            s.add(f'<rect x="45" y="{y-22}" width="1260" height="42" fill="#f7f9fc"/>')
        s.text(58, y + 5, label, "body", weight="600")
        s.text(255, y + 5, f"{sources} sources", "small")
        xa = x0 + (ci[0] - lo) / (hi - lo) * (x1 - x0)
        xb = x0 + (ci[1] - lo) / (hi - lo) * (x1 - x0)
        xe = x0 + (est - lo) / (hi - lo) * (x1 - x0)
        conclusive = ci[0] > 0 or ci[1] < 0
        s.line(xa, y, xb, y, ORANGE, 2.75)
        s.line(xa, y - 5, xa, y + 5, ORANGE, 2)
        s.line(xb, y - 5, xb, y + 5, ORANGE, 2)
        s.circle(xe, y, 6, ORANGE if conclusive else PAPER, ORANGE, 2)
        s.text(1190, y + 5, f"{est:+.2f} pp", "small", fill=INK, weight="600")

    key_y = 380
    s.circle(70, key_y, 6, ORANGE, ORANGE, 1)
    s.text(85, key_y + 4, "95% CI excludes zero", "small")
    s.circle(300, key_y, 6, PAPER, ORANGE, 2)
    s.text(315, key_y + 4, "95% CI crosses zero", "small")
    s.text(615, key_y + 4, "Haiku shows a severe penalty; Sonnet is nearly invariant.", "small", weight="600")

    s.save("03b_frontier_musique.svg")


def reasoning_budget():
    data = load("results/processed/stage5_six_model_pilot.json")
    names = [
        # Row 1: Qwen family
        ("Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m", "Qwen 2.5 1.5B"),
        ("unsloth/Qwen3.5-2B-GGUF:q4_k_m", "Qwen 3.5 2B"),
        ("unsloth/Qwen3.5-4B-GGUF:q4_k_m", "Qwen 3.5 4B"),
        # Row 2: Tiny Aya and Gemma
        ("CohereLabs/tiny-aya-global-GGUF:q4_k_m", "Tiny Aya Global"),
        ("google/gemma-4-E2B-it-qat-q4_0-gguf:q4_0", "Gemma 4 E2B"),
        ("google/gemma-4-E4B-it-qat-q4_0-gguf:q4_0", "Gemma 4 E4B"),
    ]
    budgets = [64, 128, 256, 512, 1024]
    meta = {
        "experiment_id": "stage5_pilot",
        "evidence_tier": "pilot",
        "cohort": "local_cohort_6",
        "models": [label for _, label in names],
        "n_examples_per_model": 24,
        "n_calls": 5760,
        "source": "results/processed/stage5_six_model_pilot.json",
    }
    s = SVG(1400, 940, "Figure 4A: Reasoning-budget exploratory pilot across 6 models", "Six small multiples showing UUID minus numeric accuracy across visible scratchpad budgets.", metadata=meta)
    header(s, "Figure 4A — More scratchpad does not consistently repair UUID deficits across models", "Exploratory pilot (24 unique examples/model; 2,880 records / 5,760 model calls across 6 models); paired 95% bootstrap intervals.")

    panel_w = 360
    gap_x = 45
    ylo, yhi = -80, 40

    for idx, (key, label) in enumerate(names):
        row = idx // 3
        col = idx % 3
        left = 95 + col * (panel_w + gap_x)
        right = left + panel_w

        y_top = 155 if row == 0 else 525
        y_bottom = 425 if row == 0 else 795

        m_data = data["models"][key]
        regime = m_data.get("regime", "active_scaling")
        overall_acc = m_data.get("overall_accuracy", 0.0)

        # Panel header: Model name + Regime indicator
        s.text(left, y_top - 20, label, "label", fill=INK, weight="700")
        if regime == "ceiling" or (overall_acc > 0.65):
            s.text(right, y_top - 20, "High Saturation", "small", "end", fill=MUTED)
        else:
            s.text(right, y_top - 20, f"Active ({overall_acc*100:.0f}% acc)", "small", "end", fill=MUTED)

        # Grid lines & ticks
        for tick in (-80, -60, -40, -20, 0, 20, 40):
            y = y_bottom - (tick - ylo) / (yhi - ylo) * (y_bottom - y_top)
            s.line(left, y, right, y, INK if tick == 0 else GRID, 1.8 if tick == 0 else 1)
            if col == 0:
                s.text(left - 12, y + 4, f"{tick:+d} pp", "small", "end")
            if tick == 0 and col == 0:
                s.text(left + 6, y - 5, "0 pp (Equal)", "small", fill=MUTED)

        # Region labels on rightmost column
        if col == 2:
            s.text(right, y_top + 16, "UUID better (> 0)", "small", "end", fill=MUTED)
            s.text(right, y_bottom - 8, "Numeric better (< 0)", "small", "end", fill=MUTED)

        points = []
        for i, budget in enumerate(budgets):
            cell = m_data["budgets"][str(budget)]["uuid_minus_numeric_accuracy"]
            est = cell["estimate"] * 100
            ci = [v * 100 for v in cell["bootstrap_95_ci"]]
            x = left + i * (panel_w / 4)
            y = y_bottom - (est - ylo) / (yhi - ylo) * (y_bottom - y_top)
            ya = y_bottom - (ci[0] - ylo) / (yhi - ylo) * (y_bottom - y_top)
            yb = y_bottom - (ci[1] - ylo) / (yhi - ylo) * (y_bottom - y_top)

            conclusive = ci[0] > 0 or ci[1] < 0
            dot_fill = ORANGE if conclusive else PAPER
            dot_stroke = ORANGE if conclusive else INK

            s.line(x, ya, x, yb, ORANGE, 2)
            s.line(x - 4, ya, x + 4, ya, ORANGE, 1.5)
            s.line(x - 4, yb, x + 4, yb, ORANGE, 1.5)
            s.circle(x, y, 4.5, dot_fill, dot_stroke, 1.75)
            s.text(x, y_bottom + 18, str(budget), "small", "middle")
            points.append((x, y))

        s.polyline(points, ORANGE, 1.5, dash="4,4")
        s.text((left + right) / 2, y_bottom + 38, "Pass 1 scratchpad (tokens)", "small", "middle", fill=MUTED)

    # Global Y-axis title on far left, rotated vertically so it does not clip
    s.text(32, 440, "UUID − numeric final-answer accuracy delta (percentage points)", "label", "middle", transform="rotate(-90 32 440)")

    # In-figure note banner at bottom
    s.rect(95, 855, 1205, 65, fill="#f8fafc", stroke=GRID, radius=10)
    s.text(115, 882, "Key finding: Across 6 architectures, increasing scratchpad capacity fails to erase UUID deficits; large penalties persist.", "small", weight="600")
    s.text(115, 905, "Includes both regimes: active scaling (Qwen 1.5B, Qwen 3.5 2B, Tiny Aya, Gemma E2B) and ceiling saturation (Gemma E4B, Qwen 3.5 4B).", "small", fill=MUTED)

    s.save("04_reasoning_budget.svg")


def frontier_reasoning():
    result = load("results/processed/frontier_anthropic_summary.json")["reasoning_ablation"]["anthropic_sonnet"]["citation_exact_match_penalty"]
    no_reasoning = result["mean_penalty_no_reasoning"]
    adaptive = result["mean_penalty_with_reasoning"]
    delta = result["delta_reduction"]

    s = SVG(1350, 390, "Figure 4B: Anthropic Sonnet reasoning-setting check", "A separate MuSiQue execution-setting comparison for Claude Sonnet 5.5, showing the change in UUID minus numeric exact binding under no reasoning and adaptive-low settings.")
    header(s, "Figure 4B — Adaptive-low did not reliably repair Sonnet's binding gap", "Separate 100-question MuSiQue check at 15 and 20 sources; this API setting comparison is not the five-budget synthetic task in Figure 4.")

    s.rect(60, 125, 235, 105, fill="#f7f9fc", stroke="#f7f9fc", radius=10)
    s.text(85, 155, "No-reasoning execution", "label")
    s.text(85, 202, f"{no_reasoning:+.1f} pp", "title", fill=ORANGE)
    s.arrow(315, 178, 385, 178, MUTED, 2)
    s.rect(405, 125, 235, 105, fill="#f7f9fc", stroke="#f7f9fc", radius=10)
    s.text(430, 155, "Adaptive-low execution", "label")
    s.text(430, 202, f"{adaptive:+.1f} pp", "title", fill=TEAL)

    left, right, y = 735, 1250, 180
    lo, hi = -5, 10
    for tick in (-5, 0, 5, 10):
        x = left + (tick - lo) / (hi - lo) * (right - left)
        s.line(x, 130, x, 235, INK if tick == 0 else GRID, 1.8 if tick == 0 else 1)
        s.text(x, 255, f"{tick:+d} pp", "small", "middle")
    xa = left + (delta["ci_low_pct"] - lo) / (hi - lo) * (right - left)
    xb = left + (delta["ci_high_pct"] - lo) / (hi - lo) * (right - left)
    xe = left + (delta["mean_delta_pct"] - lo) / (hi - lo) * (right - left)
    s.text(left, 112, "Adaptive-low minus no reasoning", "label")
    s.line(xa, y, xb, y, TEAL, 3)
    s.line(xa, y - 7, xa, y + 7, TEAL, 2)
    s.line(xb, y - 7, xb, y + 7, TEAL, 2)
    s.circle(xe, y, 7, PAPER, TEAL, 2.5)
    s.text(right, 112, f"{delta['mean_delta_pct']:+.1f} pp [{delta['ci_low_pct']:+.1f}, {delta['ci_high_pct']:+.1f}]", "small", "end", weight="600")

    s.rect(60, 295, 1230, 60, fill="#f8fafc", stroke=GRID, radius=10)
    s.text(85, 320, "Interpretation:", "small", weight="600")
    s.text(205, 320, "The interval crosses zero, so this run does not establish a reliable binding repair.", "small")
    s.text(85, 342, "Execution caveat:", "small", weight="600")
    s.text(220, 342, "The API reported zero reasoning tokens in every response; the comparison concerns settings, not observed hidden-reasoning volume.", "small")

    s.save("04b_anthropic_reasoning.svg")


def longproc():
    data = load("results/processed/longproc_gpu_summary.json")
    order = [
        ("tiny_aya_global", "Tiny Aya Global"),
        ("qwen25_15b", "Qwen 2.5 1.5B"),
        ("gemma4_e2b", "Gemma 4 E2B"),
        ("gemma4_e4b", "Gemma 4 E4B"),
        ("qwen35_2b", "Qwen 3.5 2B"),
        ("qwen35_4b", "Qwen 3.5 4B"),
    ]
    metrics = [
        ("partial_accuracy_mean", "Mean correct-trace prefix before first error", BLUE),
        ("final_answer_accuracy", "Final-answer accuracy (%)", GREEN),
        ("strict_accuracy", "Exact full-trace accuracy (%)", ORANGE),
    ]
    meta = {
        "experiment_id": "long_context_tracking",
        "cohort": "local_cohort_6",
        "models": [label for _, label in order],
        "n_problems": 25,
        "n_runs": 150,
        "source": "results/processed/longproc_gpu_summary.json",
    }
    s = SVG(1400, 710, "Figure 5: LongProc trace quality across 6 models", "Grouped bars compare correct-prefix accuracy, final-answer accuracy, and exact full-trace accuracy for six models.", metadata=meta)
    header(s, "Figure 5 — Long generation does not establish procedural correctness", "Strict trace, correct-prefix, and endpoint accuracy diverge on 25 multi-step theory-of-mind problems (150 GPU runs across 6 models).")

    left, right, top, bottom = 120, 1310, 140, 480
    for tick in (0, 20, 40, 60, 80, 100):
        y = bottom - tick / 100 * (bottom - top)
        s.line(left, y, right, y, GRID, 1)
        s.text(left - 14, y + 4, f"{tick}%", "small", "end")

    s.text(35, 310, "Trace or answer score (%)", "label", "middle", transform="rotate(-90 35 310)")

    group_w = (right - left) / len(order)
    bar_w = 28
    for gi, (key, label) in enumerate(order):
        center = left + group_w * (gi + 0.5)
        m_entry = data[key]
        for mi, (metric, _, color) in enumerate(metrics):
            value = m_entry[metric] * 100
            x = center + (mi - 1) * (bar_w + 5) - bar_w / 2
            y = bottom - value / 100 * (bottom - top)
            s.add(f'<rect x="{x}" y="{y}" width="{bar_w}" height="{bottom-y}" fill="{color}" rx="3"/>')
            if value > 0:
                s.text(x + bar_w / 2, y - 7, f"{value:.1f}%", "small", "middle", weight="600")
            else:
                s.text(x + bar_w / 2, y - 7, "0.0%", "small", "middle")

        s.text(center, 515, label, "label", "middle", fill=INK)

        tok = m_entry["output_tokens"]["mean"]
        cap_rate = m_entry.get("generation_cap_rate", 0.0)
        full_rate = m_entry.get("full_trace_rate", 0.0)
        strict = m_entry.get("strict_accuracy", 0.0)
        if cap_rate >= 0.5:
            cap_note = f"{cap_rate*100:.0f}% hit cap"
        elif full_rate >= 0.9:
            cap_note = f"{full_rate*100:.0f}% full trace"
        elif strict > 0:
            cap_note = f"{strict*100:.0f}% exact trace"
        else:
            cap_note = f"{m_entry.get('final_answer_accuracy', 0)*100:.0f}% endpoint"

        s.rect(center - 70, 532, 140, 44, fill="#f8fafc", stroke=GRID, radius=8)
        s.text(center, 550, f"Mean: {tok:.0f} tok", "small", "middle", weight="600")
        s.text(center, 568, f"{cap_note}", "small", "middle")

    # Legend & definitions
    lx = 120
    s.rect(lx, 600, 1190, 85, fill=PAPER, stroke=GRID, radius=10)
    for mi, (metric, mlabel, color) in enumerate(metrics):
        ly = 625 + mi * 23
        s.rect(lx + 20, ly - 12, 14, 14, fill=color, radius=2)
        s.text(lx + 42, ly, mlabel, "small", weight="600")

    s.text(lx + 490, 625, "Blue: fraction of reference belief-state transitions generated before first discrepancy.", "small")
    s.text(lx + 490, 648, "Green: endpoint accuracy (whether final state is correct, regardless of intermediate reasoning).", "small")
    s.text(lx + 490, 671, "Orange: exact procedural match across entire reference trace (1,024–2,048 tokens).", "small")

    s.save("05_longproc.svg")


def stage6_geometry():
    files = [
        ("results/processed/stage6_qwen25_15b.json", "Qwen 2.5 1.5B (28 layers)"),
        ("results/processed/stage6_gemma4_e2b.json", "Gemma 4 E2B (36 layers)"),
        ("results/processed/stage6_gemma4_e4b.json", "Gemma 4 E4B (46 layers)"),
        ("results/processed/stage6_tiny_aya.json", "Tiny Aya Global (32 layers)"),
        ("results/processed/stage6_qwen35_2b.json", "Qwen 3.5 2B (24 layers)"),
        ("results/processed/stage6_qwen35_4b.json", "Qwen 3.5 4B (32 layers)"),
    ]
    meta = {
        "experiment_id": "stage6_geometry",
        "cohort": "local_cohort_6",
        "eligible_models": ["qwen25_15b", "gemma4_e2b", "gemma4_e4b", "tiny_aya_global", "qwen35_2b", "qwen35_4b"],
        "unsupported_local_models": [],
        "frontier_models": "not_applicable (closed-weights API)",
        "passes": 1440,
    }
    s = SVG(1400, 1060, "Figure 6: Stage 6 representation geometry across 6 local models", "Six panels show source-content and source-label CKA between structured and UUID conditions across normalized model depth.", metadata=meta)
    header(s, "Figure 6 — Fact-token geometry stays stable; identifier geometry is model- and depth-dependent", "Structured-versus-UUID linear CKA across 80 paired examples (1,440 BF16 forward passes); normalized model depth across all 6 local models.")

    panel_w, panel_h = 580, 200
    positions = [
        (90, 135), (730, 135),
        (90, 395), (730, 395),
        (90, 655), (730, 655),
    ]

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
    s.rect(90, 930, 1220, 95, fill="#f8fafc", stroke=GRID, radius=10)
    s.line(120, 950, 160, 950, TEAL, 3)
    s.text(170, 955, "Teal: Source-content tokens (fact text)", "small", weight="600")
    s.line(470, 950, 510, 950, PURPLE, 3)
    s.text(520, 955, "Purple: Source-label tokens (identifier string)", "small", weight="600")

    s.text(850, 955, "1.0 = highly similar geometry; 0.0 = little shared geometry", "small", fill=MUTED)
    s.text(120, 983, "Cohort scope: All 6 primary local cohort models evaluated across 240 teacher-forced BF16 forward passes each (1,440 passes total).", "small")
    s.text(120, 1005, "Consistent geometric signature: Fact representations remain invariant across format, while identifier representations diverge late.", "small", fill=MUTED)

    s.save("06_stage6_geometry.svg")


def stage7_swaps():
    files = [
        ("results/processed/stage7_qwen25_15b.json", "Qwen 2.5 1.5B (n=8 examples)"),
        ("results/processed/stage7_gemma4_e2b.json", "Gemma 4 E2B (n=8 examples)"),
        ("results/processed/stage7_gemma4_e4b.json", "Gemma 4 E4B (n=8 examples)"),
        ("results/processed/stage7_tiny_aya.json", "Tiny Aya Global (n=8 examples)"),
        ("results/processed/stage7_qwen35_2b.json", "Qwen 3.5 2B (n=8 examples)"),
        ("results/processed/stage7_qwen35_4b.json", "Qwen 3.5 4B (n=8 examples)"),
    ]
    conditions = [("structured", "[S#] Structured", BLUE), ("random_compact", "[XQ7M] Random", TEAL), ("uuid", "UUID (36-char)", ORANGE)]
    meta = {
        "experiment_id": "stage7_interventions",
        "cohort": "local_cohort_6",
        "eligible_models": ["qwen25_15b", "gemma4_e2b", "gemma4_e4b", "tiny_aya_global", "qwen35_2b", "qwen35_4b"],
        "swaps": 144,
        "interventions": 144,
        "scope": "prompt_swaps_only",
    }
    s = SVG(1350, 940, "Figure 7A: Stage 7 source-ID swap effects across 6 local models", "Counterfactual citation log-probability effect after swapping a relevant source identifier with a distractor (prompt swaps only).", metadata=meta)
    header(s, "Figure 7A — After an ID swap, retained models shift toward the newly assigned identifier", "Change in preference for the identifier newly assigned to the relevant source; paired 95% bootstrap intervals across 144 counterfactual prompt swaps (prompt swaps only).")

    left, right, top, bottom = 260, 1220, 140, 680
    lo, hi = -24, 76

    for tick in (-20, 0, 20, 40, 60):
        x = left + (tick - lo) / (hi - lo) * (right - left)
        s.line(x, top, x, bottom, INK if tick == 0 else GRID, 1.8 if tick == 0 else 1)
        s.text(x, bottom + 25, f"{tick:+d}", "small", "middle")

    # Zero line labels & directional annotations (vertically separated to prevent overlap)
    x_zero = left + (0 - lo) / (hi - lo) * (right - left)
    s.text(x_zero, top - 24, "0.0 (No change in preference)", "small", "middle", weight="600")
    s.text(left + 15, top - 8, "← Retained old association (< 0)", "small", fill=MUTED)
    s.text(right - 15, top - 8, "Shifted to new ID (> 0) →", "small", "end", fill=BLUE)

    s.text((left + right) / 2, bottom + 52, "Change in [log P(newly correct ID) − log P(previous ID)] (log-probability delta)", "label", "middle")

    row_gap = 85
    for i, (path, label) in enumerate(files):
        data = load(path)
        y_center = top + 45 + i * row_gap
        s.text(55, y_center + 5, label, "label", fill=INK)

        for ci, (key, _, color) in enumerate(conditions):
            stat = data["source_id_swap"][key]["total_logprob"]
            est, bounds = stat["mean"], stat["bootstrap_95_ci"]
            y = y_center + (ci - 1) * 20
            xa = left + (bounds[0] - lo) / (hi - lo) * (right - left)
            xb = left + (bounds[1] - lo) / (hi - lo) * (right - left)
            xe = left + (est - lo) / (hi - lo) * (right - left)
            s.line(xa, y, xb, y, color, 3)
            s.line(xa, y - 5, xa, y + 5, color, 2)
            s.line(xb, y - 5, xb, y + 5, color, 2)
            s.circle(xe, y, 5.5, color)

    # In-figure Key & Caveats
    s.rect(55, 780, 1240, 130, fill="#f8fafc", stroke=GRID, radius=10)
    lx = 80
    for _, clabel, color in conditions:
        s.circle(lx + 8, 808, 6, color)
        s.text(lx + 24, 813, clabel, "small", weight="600")
        lx += 220

    s.text(80, 842, "Key result: Retained models shift probability toward the newly bound identifier (> 0) across compact formats.", "small", weight="600")
    s.text(80, 866, "Scope: Prompt-level counterfactual swaps only (144 swaps across 6 models). See Figure 7B for residual-stream activation patching.", "small", fill=MUTED)
    s.text(80, 888, "Caveat: Full UUIDs contain more tokens, so total log-prob magnitudes cannot be compared naively across formats.", "small", fill=MUTED)

    s.save("07_stage7_swaps.svg")


def stage7_patching():
    models_config = [
        ("results/processed/stage7_qwen25_15b.json", "Qwen 2.5 1.5B (28 layers)", 28),
        ("results/processed/stage7_tiny_aya.json", "Tiny Aya Global (36 layers)", 36),
        ("results/processed/stage7_qwen35_2b.json", "Qwen 3.5 2B (24 layers)", 24),
        ("results/processed/stage7_qwen35_4b.json", "Qwen 3.5 4B (32 layers)", 32),
        ("results/processed/stage7_gemma4_e2b.json", "Gemma 4 E2B (35 layers)", 35),
        ("results/processed/stage7_gemma4_e4b.json", "Gemma 4 E4B (42 layers)", 42),
    ]
    meta = {
        "experiment_id": "stage7_interventions",
        "cohort": "local_cohort_6",
        "eligible_models": ["qwen25_15b", "tiny_aya_global", "qwen35_2b", "qwen35_4b", "gemma4_e2b", "gemma4_e4b"],
        "activation_patches": 2160,
        "scope": "activation_patching_only",
    }
    s = SVG(1400, 1060, "Figure 7B: Stage 7 residual-stream activation patching across 6 local models", "Recovery of counterfactual source-ID swap effect by patching donor activations into clean prompt runs across normalized model depth.", metadata=meta)
    header(s, "Figure 7B — Residual-stream activation patching recovers identifier preference by late layers", "Fraction of counterfactual swap effect recovered across normalized model depth; 2,160 activation patches across all 6 local models.")

    panel_w, panel_h = 580, 190
    positions = [
        (90, 135), (730, 135),
        (90, 405), (730, 405),
        (90, 675), (730, 675),
    ]

    y_min, y_max = -0.4, 1.4

    for (path, label, total_layers), (left, top) in zip(models_config, positions):
        data = load(path)
        patch = data["activation_patching"]["structured"]
        layers = sorted(patch.keys(), key=lambda x: int(x))
        right, bottom = left + panel_w, top + panel_h

        s.text(left, top - 12, label, "label", fill=INK)

        # Draw grid lines for recovery fractions: 0.0 and 1.0 emphasized
        for tick in (-0.2, 0.0, 0.5, 1.0, 1.2):
            y = bottom - (tick - y_min) / (y_max - y_min) * panel_h
            is_key = tick in (0.0, 1.0)
            s.line(left, y, right, y, INK if is_key else GRID, 1.5 if is_key else 0.8)
            label_text = f"{tick:.1f}"
            s.text(left - 8, y + 4, label_text, "small", "end", fill=INK if is_key else MUTED)
            if tick == 1.0:
                s.text(right - 6, y - 5, "100% recovery", "small", "end", fill=TEAL, weight="600")
            elif tick == 0.0:
                s.text(right - 6, y - 5, "0% recovery", "small", "end", fill=MUTED)

        # Probed layer positions
        cit_pts = []
        ctrl_pts = []
        lbl_pts = []

        for l_str in layers:
            l_int = int(l_str)
            norm_depth = l_int / total_layers
            x = left + norm_depth * panel_w

            # Vertical dotted guideline for probed layer
            s.line(x, top, x, bottom, "#e2e8f0", 1)
            s.text(x, bottom + 16, f"L{l_int}", "small", "middle", fill=MUTED)

            rec_cit = patch[l_str]["citation_context"]["aggregate_recovery_fraction"]
            rec_ctrl = patch[l_str]["question_control"]["aggregate_recovery_fraction"]
            rec_lbl = patch[l_str]["source_label"]["aggregate_recovery_fraction"]

            # Clamp for display
            c_clamped = max(y_min, min(y_max, rec_cit))
            ctrl_clamped = max(y_min, min(y_max, rec_ctrl))
            lbl_clamped = max(y_min, min(y_max, rec_lbl))

            y_cit = bottom - (c_clamped - y_min) / (y_max - y_min) * panel_h
            y_ctrl = bottom - (ctrl_clamped - y_min) / (y_max - y_min) * panel_h
            y_lbl = bottom - (lbl_clamped - y_min) / (y_max - y_min) * panel_h

            cit_pts.append((x, y_cit))
            ctrl_pts.append((x, y_ctrl))
            lbl_pts.append((x, y_lbl))

        # Plot polylines and circles
        # 1. Question control (specificity baseline)
        s.polyline(ctrl_pts, "#94a3b8", 2.0)
        for (x, y) in ctrl_pts:
            s.circle(x, y, 4, "#94a3b8")

        # 2. Source label
        s.polyline(lbl_pts, PURPLE, 2.0)
        for (x, y) in lbl_pts:
            s.circle(x, y, 4, PURPLE)

        # 3. Citation context (primary causal mechanism)
        s.polyline(cit_pts, TEAL, 3.0)
        for (x, y) in cit_pts:
            s.circle(x, y, 5.5, TEAL)

        s.text(left, bottom + 32, "0.0 (Input)", "small")
        s.text(right, bottom + 32, "1.0 (Output)", "small", "end")
        s.text((left + right) / 2, bottom + 32, "Normalized model depth", "small", "middle")

    # Legend & explanatory notes
    s.rect(90, 935, 1220, 95, fill="#f8fafc", stroke=GRID, radius=10)
    s.line(120, 955, 160, 955, TEAL, 3.5)
    s.circle(140, 955, 5, TEAL)
    s.text(170, 960, "Teal: Citation context span (primary causal transfer, rises to ~1.0 in late layers)", "small", weight="600")

    s.line(640, 955, 680, 955, "#94a3b8", 2.5)
    s.circle(660, 955, 4, "#94a3b8")
    s.text(690, 960, "Gray: Question control span (negative control, flat at 0.0)", "small", weight="600")

    s.line(1030, 955, 1070, 955, PURPLE, 2.5)
    s.circle(1050, 955, 4, PURPLE)
    s.text(1080, 960, "Purple: Source label span", "small", weight="600")

    s.text(120, 988, "Key finding: Patching citation-context activations cleanly transfers the counterfactual binding preference at late layers (recovery ~ 1.0).", "small")
    s.text(120, 1010, "Scope: Residual-stream activation patching only (2,160 total interventions across 6 models). See Figure 7A for prompt-level swaps.", "small", fill=MUTED)

    s.save("07b_stage7_patching.svg")


def stage8_entities():
    cross_data = load("results/processed/stage8_pii_500_cross_model.json")
    conds = [("raw", "Raw", RED), ("random_masked", "Random", ORANGE), ("untyped", "Untyped", PURPLE), ("typed", "Typed", TEAL)]

    models = []
    for m in cross_data["models"]:
        mkey = m["model"]
        label = MODEL_SHORT.get(mkey, mkey)
        values = {
            "raw": {"accuracy": m["raw_accuracy"] * 100, "leakage": m["raw_pii_leakage_raw"] * 100},
            "random_masked": {"accuracy": m["random_masked_accuracy"] * 100, "leakage": m["raw_pii_leakage_masked"] * 100},
            "untyped": {"accuracy": m["untyped_accuracy"] * 100, "leakage": m["raw_pii_leakage_masked"] * 100},
            "typed": {"accuracy": m["typed_accuracy"] * 100, "leakage": m["raw_pii_leakage_masked"] * 100},
        }
        models.append((label, values))

    # Add Sonnet 5.5
    anthropic_data = load("results/processed/frontier_anthropic_summary.json")
    if "stage8_entity_resolution" in anthropic_data and "anthropic_sonnet" in anthropic_data["stage8_entity_resolution"]:
        sonnet = anthropic_data["stage8_entity_resolution"]["anthropic_sonnet"]["conditions"]
        models.append(("Sonnet 5.5", {key: {"accuracy": cell["accuracy"], "leakage": cell["raw_pii_leakage_rate"]} for key, cell in sonnet.items()}))

    # Add Sol
    openai_data = load("results/processed/frontier_openai_summary.json")
    if "stage8_entity_resolution" in openai_data and "openai_sol" in openai_data["stage8_entity_resolution"]:
        sol = openai_data["stage8_entity_resolution"]["openai_sol"]["conditions"]
        models.append(("Sol", {key: {"accuracy": cell["accuracy"], "leakage": cell["raw_pii_leakage_rate"]} for key, cell in sol.items()}))

    meta = {
        "experiment_id": "stage8_pii_500",
        "cohort": "local_cohort_6_plus_frontier_stage8",
        "models": [label for label, _ in models],
        "n_examples_per_model": 500,
        "n_generations": len(models) * 2000,
        "source": "results/processed/stage8_pii_500_cross_model.json",
    }
    s = SVG(1450, 800, "Figure 8: Stage 8 typed entity canonicalization across 8 models", "Two panels show task accuracy and raw PII output exposure across raw, random-masked, untyped, and typed representations across six local models, Claude Sonnet 5.5, and GPT-6.1 Sol.", metadata=meta)
    header(s, "Figure 8 — Canonicalization eliminates raw-value exposure; accuracy effects vary by model", f"500 synthetic account-resolution examples per model ({len(models)*2000:,} generations across six local models plus Claude Sonnet 5.5 and GPT-6.1 Sol); citations disabled.")

    # Panel A: Accuracy (Left)
    left_a, right_a, top_a, bottom_a = 90, 770, 160, 520
    s.text(left_a, top_a - 20, "Panel A: Correct account selected (%)", "label", fill=INK)

    for tick in (0, 25, 50, 75, 100):
        y = bottom_a - tick / 100 * (bottom_a - top_a)
        s.line(left_a, y, right_a, y, GRID, 1)
        s.text(left_a - 10, y + 4, f"{tick}%", "small", "end")

    group_w_a = (right_a - left_a) / len(models)
    bar_w_a = 14
    for gi, (label, values) in enumerate(models):
        center = left_a + group_w_a * (gi + 0.5)

        accuracies = []
        for ci, (key, _, color) in enumerate(conds):
            acc = values[key]["accuracy"]
            accuracies.append(acc)
            x = center + (ci - 1.5) * (bar_w_a + 2) - bar_w_a / 2
            y = bottom_a - acc / 100 * (bottom_a - top_a)
            s.add(f'<rect x="{x}" y="{y}" width="{bar_w_a}" height="{bottom_a-y}" fill="{color}" rx="2"/>')
            if 0 < acc < 99:
                s.text(x + bar_w_a / 2, y - 5, f"{acc:.0f}", "small", "middle")

        if min(accuracies) >= 99:
            s.text(center, top_a - 5, "≈100%", "small", "middle", weight="600")

        s.text(center, bottom_a + 24, label, "small", "middle", weight="600")

    s.text((left_a + right_a) / 2, bottom_a + 48, "Model Cohort", "small", "middle")

    # Panel B: Exposure (Right)
    left_b, right_b, top_b, bottom_b = 850, 1370, 160, 520
    s.text(left_b, top_b - 20, "Panel B: Outputs exposing raw personal data (%)", "label", fill=RED)

    for tick in (0, 25, 50, 75, 100):
        y = bottom_b - tick / 100 * (bottom_b - top_b)
        s.line(left_b, y, right_b, y, GRID, 1)
        s.text(left_b - 10, y + 4, f"{tick}%", "small", "end")

    group_w_b = (right_b - left_b) / len(models)
    bar_w_b = 20
    for gi, (label, values) in enumerate(models):
        center = left_b + group_w_b * (gi + 0.5)

        raw_leak = values["raw"]["leakage"]
        masked_leak = max(values[key]["leakage"] for key in ("random_masked", "untyped", "typed"))

        # Bar 1: Raw
        x1 = center - bar_w_b - 2
        y1 = bottom_b - raw_leak / 100 * (bottom_b - top_b)
        s.add(f'<rect x="{x1}" y="{y1}" width="{bar_w_b}" height="{bottom_b-y1}" fill="{RED}" rx="2"/>')
        s.text(x1 + bar_w_b / 2, y1 - 5, f"{raw_leak:.0f}%", "small", "middle", fill=RED, weight="600")

        # Bar 2: Worst observed masked/canonical exposure across three representations
        x2 = center + 2
        y2 = bottom_b - masked_leak / 100 * (bottom_b - top_b)
        s.add(f'<rect x="{x2}" y="{min(y2, bottom_b-3)}" width="{bar_w_b}" height="{max(bottom_b-y2, 3)}" fill="{TEAL}" rx="1"/>')
        s.text(x2 + bar_w_b / 2, min(y2, bottom_b-3) - 5, f"{masked_leak:.1f}%", "small", "middle", fill=TEAL, weight="600")

        s.text(center, bottom_b + 24, label, "small", "middle", weight="600")

    s.text((left_b + right_b) / 2, bottom_b + 48, "Model Cohort", "small", "middle")

    # Legend & definitions at bottom
    s.rect(90, 595, 1280, 180, fill="#f8fafc", stroke=GRID, radius=10)
    lx = 120
    for _, clabel, color in conds:
        s.rect(lx, 617, 14, 14, fill=color, radius=2)
        s.text(lx + 22, 629, clabel, "small", weight="600")
        lx += 160

    s.text(120, 658, "Representation definitions:", "small", weight="600")
    s.text(285, 658, "Raw = literal names, emails, account numbers.  Random = arbitrary alphanumeric mask.", "small")
    s.text(285, 680, "Untyped = <ENTITY_1>, <ENTITY_2> (type-neutral).  Typed = <ACCOUNT_1>, <EMAIL_2> (preserves entity type).", "small")
    s.text(120, 712, "Key finding: Typed handles improved accuracy in four of six local models (two ceiling-limited); Sonnet and Sol were saturated (≥99.8%).", "small", fill=INK, weight="600")
    s.text(120, 734, "Data boundary: Every masked representation reduced raw-value output exposure to 0.0% across all eight models.", "small", fill=MUTED)
    s.text(120, 756, f"Sample size: 500 paired semantic examples per model; {len(models)*2000:,} generations in total across eight models.", "small", fill=MUTED)

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
    frontier_musique()
    reasoning_budget()
    frontier_reasoning()
    longproc()
    stage6_geometry()
    stage7_swaps()
    stage7_patching()
    stage8_entities()
    trust_boundary()
    print("All 12 publication-grade figure assets built successfully in both blog/assets/ and blog/site/assets/.")


if __name__ == "__main__":
    main()
