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
        assert "26,205" in article
        assert "18,605" in article
        assert "20,605" in article
        assert "11,200 model calls" in article
        assert "23,620" not in article
    for article in (MARKDOWN, HTML):
        assert "5,600 two-pass generations" in article
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

    for article in (MARKDOWN, APPENDIX):
        assert "-10.58" in article
        assert "-4.00" in article
        assert "70.0" in article
    assert ("-10.58" in HTML or "&minus;10.58" in HTML)
    assert ("-4.00" in HTML or "&minus;4.00" in HTML)
    assert "70.0" in HTML


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
