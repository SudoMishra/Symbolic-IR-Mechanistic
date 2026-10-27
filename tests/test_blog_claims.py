import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKDOWN = (ROOT / "blog/symbolic-ir-engineering-blog.md").read_text()
HTML = (ROOT / "blog/site/index.html").read_text()


def test_stage9_blog_claims_match_processed_result():
    result = json.loads((ROOT / "results/processed/stage9_system_eval.json").read_text())
    reduction = 100 * result["representation"]["character_reduction_fraction"]
    expected = f"{reduction:.2f}%"
    assert expected in MARKDOWN
    assert expected in HTML
    assert "41.8%" not in MARKDOWN
    assert "41.8%" not in HTML


def test_stage5_two_pass_counts_are_not_described_as_single_calls():
    for article in (MARKDOWN, HTML):
        assert "23,620" in article
        assert "5,600 two-pass generations" in article
        assert "11,200 model calls" in article
        assert "5,600 model calls" not in article
        assert "2,800 paired two-pass generations" not in article


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
