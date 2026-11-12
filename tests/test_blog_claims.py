import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKDOWN = (ROOT / "blog/symbolic-ir-engineering-blog.md").read_text()
HTML = (ROOT / "blog/site/index.html").read_text()
APPENDIX = (ROOT / "blog/appendix.md").read_text()


def test_stage9_blog_claims_match_processed_result():
    result = json.loads((ROOT / "results/processed/stage9_system_eval.json").read_text())
    reduction = 100 * result["representation"]["character_reduction_fraction"]
    expected = f"{reduction:.2f}%"
    assert expected in MARKDOWN
    assert expected in HTML
    assert "41.8%" not in MARKDOWN
    assert "41.8%" not in HTML


def test_stage5_two_pass_counts_are_not_described_as_single_calls():
    for article in (MARKDOWN, HTML, APPENDIX):
        assert "46,230" in article
        assert "57,397" not in article
        assert "63,706" not in article
        assert "5,600 model calls" not in article
        assert "2,800 paired two-pass generations" not in article


def test_lfm26b_reported_metrics_match_artifacts():
    factorial = json.loads((ROOT / "results/processed/stage1_lfm25_26b_factorial.json").read_text())
    assert factorial["total_records"] == 1600
    for c in factorial["cells"]:
        if "prefill" in c["arm"]:
            assert c["truncation_rate"] == 0.0
        elif c["arm"] == "default_80":
            assert c["truncation_rate"] == 1.0

    musique_sens = json.loads((ROOT / "results/analysis/musique_lfm26b_budget_sensitivity.json").read_text())
    delta_15 = f"{musique_sens['run_512']['scenarios']['15_sources']['binding_recall_delta'] * 100:.2f}"
    delta_20 = f"{musique_sens['run_512']['scenarios']['20_sources']['binding_recall_delta'] * 100:.2f}"
    assert delta_15 == "-10.58"
    assert delta_20 == "-4.00"

    pii_26b = json.loads((ROOT / "results/analysis/stage8_pii_lfm25_26b.json").read_text())
    typed_delta = pii_26b["paired_effects"]["typed_vs_untyped_accuracy"]["mean"] * 100
    assert f"{typed_delta:.1f}" == "70.0"

    # Documented exclusion per Decision D-02 in technical appendix
    assert "Decision D-02" in APPENDIX
    assert "Model Exclusion Note" in APPENDIX

    # Completely absent from public blog
    for article in (MARKDOWN, HTML):
        assert "LFM" not in article
        assert "LiquidAI" not in article


def test_counter_result_and_scope_caveats_remain_visible():
    for article in (MARKDOWN, HTML):
        assert "Gemma E2B" in article
        assert "37 points" in article
        assert "25 points" in article
        assert "does not establish" in article


def test_manifest_points_to_checked_in_supporting_artifacts():
    with (ROOT / "blog/evidence_manifest.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        assert (ROOT / row["primary_artifact"]).is_file()
        for artifact in row["processed_artifact"].split(";"):
            path = artifact.strip()
            if path.startswith("results/raw/"):
                continue
            assert (ROOT / path).is_file(), path


def test_scaled_evidence_claims_are_consistent():
    for article in (MARKDOWN, HTML, APPENDIX):
        assert "46,230" in article
        assert "13,760" in article
        assert "57,397" not in article
        assert "63,706" not in article
        assert "757" not in article
        assert "76,515" not in article
        assert "83,555" not in article


def test_stage8_disclosure_is_visible_and_matches_reconciled_results():
    result = json.loads((ROOT / "results/processed/stage8_pii_500_cross_model.json").read_text())
    disclosure = HTML.split("Explore the complete scaled entity-resolution results", 1)[1].split("</details>", 1)[0]

    # This disclosure is on the light boundary section. The inverse text class
    # renders cream text on the cream background and makes the table appear empty.
    assert 'class="table-wrap"' in disclosure
    assert "table-wrap--inverse" not in disclosure
    assert disclosure.count("<tr>") == 7  # one header plus six model rows

    for model in result["models"]:
        for key in ("raw_accuracy", "random_masked_accuracy", "untyped_accuracy", "typed_accuracy"):
            expected = f'{model[key] * 100:.1f}%'
            assert expected in disclosure
        classification = model["classification"].replace("_", "-").capitalize()
        assert classification in disclosure


def test_anthropic_frontier_claims_match_compiled_results():
    result = json.loads((ROOT / "results/processed/frontier_anthropic_summary.json").read_text())
    for model in ("anthropic_haiku", "anthropic_sonnet"):
        assert result["musique_500"][model]["records"] == 2000
        for num_sources in (15, 20):
            delta = result["musique_500"][model]["deltas"][f"{num_sources}_sources"]["citation_recall_delta"]
            expected = f"{delta['mean_delta_pct']:.2f} pp"
            assert expected in MARKDOWN
            assert expected.replace("-", "&minus;") in HTML

    for article in (MARKDOWN, HTML):
        assert "13,760" in article
        assert "03b_frontier_musique.svg" in article
        assert "04b_anthropic_reasoning.svg" in article

    for asset, model_names in {
        "03b_frontier_musique.svg": ("Claude Haiku 5.5", "Claude Sonnet 5.5"),
        "04b_anthropic_reasoning.svg": ("Sonnet", "Adaptive-low"),
        "08_stage8_entities.svg": ("Sonnet 5.5",),
    }.items():
        svg = (ROOT / "blog/site/assets" / asset).read_text()
        assert all(name in svg for name in model_names)
