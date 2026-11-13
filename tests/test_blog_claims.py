import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

import yaml


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "blog/site"
SITE_PAGES = sorted(SITE.rglob("*.html"))
SITE_HTML = "\n".join(page.read_text() for page in SITE_PAGES)


EXPECTED_ROUTES = {
    "00-harness-validation",
    "01-citation-baseline",
    "02-multihop-musique",
    "04-dual-labels",
    "05-reasoning-budget",
    "longproc",
    "06-representation-geometry",
    "07-causal-interventions",
    "07b-component-localization",
    "08-entity-canonicalization",
    "09-systems-boundary",
}


class LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "a" and values.get("href"):
            self.refs.append(values["href"])
        if tag in {"img", "script"} and values.get("src"):
            self.refs.append(values["src"])
        if tag == "link" and values.get("href"):
            self.refs.append(values["href"])


def test_experimental_log_has_complete_route_set_and_page_contract():
    routes = {page.parent.name for page in (SITE / "experiments").glob("*/index.html")}
    assert routes == EXPECTED_ROUTES
    required_ids = (
        'id="question"', 'id="design"', 'id="results"',
        'id="interpretation"', 'id="boundaries"',
        'id="provenance"', 'id="related"',
    )
    for page in (SITE / "experiments").glob("*/index.html"):
        html = page.read_text()
        assert 'id="main-content"' in html, page
        assert 'class="experiment-nav"' in html, page
        assert 'aria-current="page"' in html, page
        assert all(section in html for section in required_ids), page


def test_all_local_site_links_and_assets_resolve():
    for page in SITE_PAGES:
        parser = LinkCollector()
        parser.feed(page.read_text())
        for ref in parser.refs:
            parts = urlsplit(ref)
            if parts.scheme or parts.netloc or ref.startswith(("#", "mailto:")):
                continue
            target = (page.parent / parts.path).resolve()
            if parts.path.endswith("/"):
                target = target / "index.html"
            assert target.exists(), f"{page.relative_to(ROOT)} -> {ref}"


def test_study_accounting_and_frozen_cohort_are_public():
    accounting = json.loads((ROOT / "results/audit/study_accounting.json").read_text())
    assert accounting["local_completed_calls"] == 46_230
    assert accounting["frontier_completed_calls"] == 13_760
    assert accounting["mechanistic_completed_calls"] == 3_744
    assert accounting["systems_completed_executions"] == 6_000
    assert accounting["total_verified_calls"] == 63_734
    assert {m for m, v in accounting["by_model"].items() if v["type"] == "local"} == {
        "tiny_aya_global", "qwen25_15b", "gemma4_e2b", "gemma4_e4b",
        "qwen35_2b", "qwen35_4b",
    }
    landing = (SITE / "index.html").read_text()
    for value in ("63,734", "46,230", "13,760", "3,744", "6,000"):
        assert value in landing
    assert "2,592" in landing
    assert "Both LFM checkpoints are excluded" in landing


def test_stage7b_component_localization_is_public():
    landing = (SITE / "index.html").read_text()
    page = (SITE / "experiments/07b-component-localization/index.html").read_text()
    assert 'href="experiments/07b-component-localization/"' in landing
    for claim in (
        "2,592 interventions", "N=80 per model", "+0.621", "+14.460",
        "Gemma 4 E4B", "teacher-forced", "No universal",
    ):
        assert claim in page
    for figure in (
        "08a_component_dissociation.svg",
        "08b_circuit_wiring_diagram.svg",
        "08c_cross_model_circuit_comparison.svg",
    ):
        assert figure in page


def test_musique_pages_match_six_model_processed_outputs():
    held_out = json.loads((ROOT / "results/processed/musique_confirmatory.json").read_text())
    scaled = json.loads((ROOT / "results/processed/musique_500_confirmatory.json").read_text())
    assert held_out["records"] == 2_400
    assert held_out["summary"] == {
        "answer_f1_sig_neg": 1, "answer_f1_sig_pos": 2,
        "answer_f1_sig_total": 3, "binding_neg": 12,
        "binding_sig_neg": 6, "binding_sig_pos": 0,
        "binding_sig_total": 6, "total_cells": 12,
    }
    assert scaled["records"] == 12_000
    assert scaled["summary"]["binding_sig_neg"] == 12
    assert scaled["summary"]["answer_f1_sig_total"] == 4
    page = (SITE / "experiments/02-multihop-musique/index.html").read_text()
    for claim in ("2,400 generations", "12,000 generations", "12 / 12", "8,000 generations"):
        assert claim in page
    for model in ("Claude Haiku 5.5", "Claude Sonnet 5.5", "GPT-6 Luna", "GPT-6.1 Sol"):
        assert model in page


def test_reasoning_budget_matches_expanded_confirmation():
    result = json.loads((ROOT / "results/processed/stage5_confirmatory.json").read_text())
    assert result["records"] == 4_800
    assert result["complete_paired_examples"] == 240
    assert len(result["models"]) == 6
    positive = 0
    for model in result["models"].values():
        interval = model["uuid_penalty_low_to_high_budget_interaction"]["bootstrap_95_ci"]
        positive += interval[0] > 0
    assert positive == 5
    page = (SITE / "experiments/05-reasoning-budget/index.html").read_text()
    assert "4,800 generations" in page
    assert "5 / 6" in page
    assert "64 / 128 / 256 / 512 / 1024" in page
    assert "visible scratchpad" in page
    assert "not hidden chain-of-thought" in page


def test_longproc_stage6_and_stage7_counts_match_artifacts():
    longproc = json.loads((ROOT / "results/processed/longproc_gpu_summary.json").read_text())
    assert len(longproc) == 6
    assert sum(model["n"] for model in longproc.values()) == 150
    eligibility = json.loads((ROOT / "results/audit/mechanistic_eligibility_report.json").read_text())
    assert len(eligibility["eligible_cohort"]) == 6
    assert not eligibility["unsupported_cohort"]
    manifest = yaml.safe_load((ROOT / "study_manifest.yaml").read_text())
    stage7 = manifest["experiments"]["stage7_interventions"]
    assert set(stage7["expected_calls_by_model"].values()) == {384}
    assert stage7["expected_total_calls"] == 2_304
    for model, rel_path in stage7["raw_paths"].items():
        records = [line for line in (ROOT / rel_path).read_text().splitlines() if line.strip()]
        assert len(records) == 384, model
    geometry = (SITE / "experiments/06-representation-geometry/index.html").read_text()
    causal = (SITE / "experiments/07-causal-interventions/index.html").read_text()
    assert "1,440 BF16 passes" in geometry
    assert "5 / 6" in geometry
    assert "2,304 interventions" in causal
    assert "144" in causal and "2,160" in causal
    assert "6 × 384" in causal
    assert "07b_stage7_patching.svg" in causal


def test_stage8_classification_and_exposure_denominators_are_visible():
    result = json.loads((ROOT / "results/processed/stage8_pii_500_cross_model.json").read_text())
    assert result["n_models"] == 6
    assert result["denominators"] == {
        "all_four_conditions": 12_000,
        "three_masked_conditions": 9_000,
        "typed_and_untyped": 6_000,
    }
    assert result["classification_counts"]["supported"] == 4
    assert result["classification_counts"]["ceiling_limited"] == 2
    assert sum(result["classification_counts"].values()) == 6
    page = (SITE / "experiments/08-entity-canonicalization/index.html").read_text()
    assert "4 / 6" in page and "2 / 6" in page
    assert "0 / 9,000" in page
    assert "LFM 1.2B</td>" not in page
    assert "LFM 2.6B</td>" not in page


def test_frontier_and_stage9_completion_are_reported_separately():
    frontier = json.loads((ROOT / "results/processed/frontier_evaluation_summary.json").read_text())
    assert set(frontier["musique_500"]) == {
        "anthropic_haiku", "anthropic_sonnet", "openai_luna", "openai_sol"
    }
    assert sum(model["records"] for model in frontier["musique_500"].values()) == 8_000
    page = (SITE / "experiments/09-systems-boundary/index.html").read_text()
    result = json.loads((ROOT / "results/processed/stage9_system_eval.json").read_text())
    reduction = 100 * result["representation"]["character_reduction_fraction"]
    assert f"{reduction:.2f}%" in page
    assert "5,000" in page
    assert "wrong-but-registered" in page.lower()


def test_counter_results_and_scope_caveats_are_visible():
    baseline = (SITE / "experiments/01-citation-baseline/index.html").read_text()
    geometry = (SITE / "experiments/06-representation-geometry/index.html").read_text()
    assert "Gemma E2B" in baseline
    assert "parser" in baseline.lower()
    assert "no clear gate" in geometry.lower()
    assert "does not establish" in geometry.lower()
    assert "correlational" in geometry.lower()
    assert "07b_stage7_patching.svg" in SITE_HTML
