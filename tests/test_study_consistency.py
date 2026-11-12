"""Data-integrity and consistency tests for the Symbolic IR Mechanistic study.

Enforces P8-01 through P8-15 of STUDY_CONSISTENCY_REPAIR_CHECKLIST.md:
- P8-01: Manifest totals equal raw and processed record totals.
- P8-02: Every published local behavioral experiment has all six expected models.
- P8-03: Every published cell has the expected number of examples.
- P8-04: Paired conditions share the same semantic-example IDs.
- P8-05: No LFM record enters a public artifact.
- P8-06: Figure 3 contains six local models and uses N=500 confirmation data.
- P8-07: Figure 5 contains six local models.
- P8-08: Stage 5 pilot and confirmation sources never mix.
- P8-09: Table values equal processed JSON values.
- P8-10: Prose significance counts equal generated analysis counts.
- P8-11: Stage 8 denominators (12,000 / 9,000 / 6,000 local; 4,000 frontier).
- P8-12: Partial frontier batches cannot be marked publishable.
- P8-13: Frontier models never appear in mechanistic totals.
- P8-14: Figure 7 captions match the plotted evidence type.
- P8-15: Generated figures are not older than their input artifacts.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
LFM_MODELS = {"lfm25_12b", "lfm25_26b"}
LOCAL_6_MODELS = {
    "tiny_aya_global",
    "qwen25_15b",
    "gemma4_e2b",
    "gemma4_e4b",
    "qwen35_2b",
    "qwen35_4b",
}
FRONTIER_MODELS = {
    "claude-haiku-5-5",
    "claude-sonnet-5-5",
    "gpt-6-1-sol",
    "gpt-6-luna",
}


@pytest.fixture(scope="module")
def manifest() -> dict:
    return yaml.safe_load((ROOT / "study_manifest.yaml").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def accounting() -> dict:
    return json.loads((ROOT / "results/audit/study_accounting.json").read_text(encoding="utf-8"))


def test_p8_01_manifest_totals_equal_raw_counts(manifest):
    """P8-01: Verify that completed experiments in the manifest match raw line counts."""
    for exp_id, exp in manifest.get("experiments", {}).items():
        if exp.get("publication_status") != "publishable":
            continue
        raw_paths = exp.get("raw_paths", {})
        if not isinstance(raw_paths, dict) or not raw_paths:
            continue
        total_raw_lines = 0
        for model_id, rel_path in raw_paths.items():
            path = ROOT / rel_path
            assert path.is_file(), f"Missing raw file {path} for {exp_id} / {model_id}"
            lines = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
            expected_per_model = exp.get("expected_calls_per_model")
            if expected_per_model:
                assert lines == expected_per_model, f"{exp_id} {model_id} line count {lines} != expected {expected_per_model}"
            total_raw_lines += lines
        expected_total = exp.get("expected_total_calls")
        if expected_total:
            assert total_raw_lines == expected_total, f"{exp_id} total lines {total_raw_lines} != {expected_total}"


def test_p8_02_every_published_local_behavioral_has_six_models(manifest):
    """P8-02: Every published local behavioral experiment must use all six local models."""
    local_behavioral_ids = [
        "stage1_scaling_500",
        "musique_replication_100",
        "musique_scaled_500",
        "long_context_tracking",
        "stage8_pii_500",
    ]
    for exp_id in local_behavioral_ids:
        exp = manifest["experiments"][exp_id]
        exp_models = set(exp["models"])
        missing = LOCAL_6_MODELS - exp_models
        assert not missing, f"Experiment {exp_id} is missing primary local models: {missing}"


def test_p8_03_every_published_cell_has_expected_examples():
    """P8-03: Test that every published cell has the expected number of examples."""
    # MuSiQue 500 confirmatory
    m500 = json.loads((ROOT / "results/processed/musique_500_confirmatory.json").read_text(encoding="utf-8"))
    models = m500.get("models", [])
    assert len(models) == 6, f"Expected 6 models in MuSiQue 500, got {len(models)}"
    for model_data in models:
        model_id = model_data.get("model_id") or model_data.get("model", "")
        for lfm in LFM_MODELS:
            assert lfm not in model_id
        cell_dict = {(c["sources"], c["condition"]): c["n"] for c in model_data.get("cells", [])}
        for ns in [15, 20]:
            for cond in ["numeric", "uuid"]:
                assert cell_dict.get((ns, cond)) == 500, f"MuSiQue cell {model_id} ({ns}, {cond}) != 500"

    # Stage 8 cross-model
    s8 = json.loads((ROOT / "results/processed/stage8_pii_500_cross_model.json").read_text(encoding="utf-8"))
    assert s8.get("n_examples_per_model") == 500
    s8_models = s8.get("models", [])
    assert len(s8_models) == 6, f"Expected 6 local models in Stage 8, got {len(s8_models)}"
    for model_data in s8_models:
        model_id = model_data.get("model_id") or model_data.get("model", "")
        for lfm in LFM_MODELS:
            assert lfm not in model_id


def test_p8_04_paired_conditions_share_same_semantic_ids():
    """P8-04: Test that paired conditions share the same semantic-example IDs."""
    # Check MuSiQue 500 for a representative primary model
    raw_path = ROOT / "results/raw/musique_500_tiny_aya/34c2b77aedd4.jsonl"
    records = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    ids_by_cond = {}
    for r in records:
        ns = r.get("num_sources") or (r.get("dataset_cell") or {}).get("num_sources")
        cond = r.get("condition") or r.get("identifier_condition")
        cond_key = (ns, cond)
        ids_by_cond.setdefault(cond_key, set()).add(r["example_id"])
    assert ids_by_cond[(15, "numeric")] == ids_by_cond[(15, "uuid")]
    assert ids_by_cond[(20, "numeric")] == ids_by_cond[(20, "uuid")]
    assert len(ids_by_cond[(15, "numeric")]) == 500


def test_p8_05_no_lfm_record_in_public_artifacts(accounting):
    """P8-05: Test that no LFM record enters public artifacts."""
    # Evidence manifest CSV
    evidence_csv = (ROOT / "blog/evidence_manifest.csv").read_text(encoding="utf-8")
    for lfm in LFM_MODELS:
        assert lfm not in evidence_csv, f"Found {lfm} in blog/evidence_manifest.csv"

    # study_accounting.json: LFM models have 0 published completed calls
    for lfm in LFM_MODELS:
        lfm_acc = accounting.get("by_model", {}).get(lfm)
        if lfm_acc:
            assert lfm_acc.get("completed_calls", 0) == 0, f"LFM model {lfm} has non-zero calls: {lfm_acc}"
            assert lfm_acc.get("type") == "excluded"

    # Public SVGs
    for svg_path in (ROOT / "blog/assets").glob("*.svg"):
        content = svg_path.read_text(encoding="utf-8")
        for lfm in ["lfm25_12b", "lfm25_26b", "LFM 2.5 1.2B", "LFM 2.5 2.6B"]:
            assert lfm not in content, f"Found {lfm} in public SVG {svg_path.name}"


def test_p8_06_figure3_contains_six_local_models_and_n500():
    """P8-06: Test that Figure 3 contains six local models and uses N=500 confirmation data."""
    for path in [ROOT / "blog/assets/03_musique_confirmation.svg", ROOT / "blog/site/assets/03_musique_confirmation.svg"]:
        content = path.read_text(encoding="utf-8")
        for name in ["Tiny Aya", "Qwen 2.5 1.5B", "Gemma 4 E2B", "Gemma 4 E4B", "Qwen 3.5 2B", "Qwen 3.5 4B"]:
            assert name in content, f"Missing {name} in {path.name}"
        assert "N=500" in content
        assert "12,000 generations" in content


def test_p8_07_figure5_contains_six_local_models():
    """P8-07: Test that Figure 5 contains six local models."""
    for path in [ROOT / "blog/assets/05_longproc.svg", ROOT / "blog/site/assets/05_longproc.svg"]:
        content = path.read_text(encoding="utf-8")
        for name in ["Tiny Aya", "Qwen 2.5 1.5B", "Gemma 4 E2B", "Gemma 4 E4B", "Qwen 3.5 2B", "Qwen 3.5 4B"]:
            assert name in content, f"Missing {name} in {path.name}"


def test_p8_08_stage5_pilot_and_confirmation_sources_never_mix(manifest):
    """P8-08: Test that Stage 5 pilot and confirmation sources never mix."""
    pilot = manifest["experiments"]["stage5_pilot"]
    confirm = manifest["experiments"]["stage5_confirmatory"]
    assert pilot["evidence_tier"] == "pilot"
    assert confirm["evidence_tier"] == "confirmatory"
    for m in LOCAL_6_MODELS:
        p_raw = pilot["raw_paths"].get(m)
        c_raw = confirm["raw_paths"].get(m)
        if p_raw and c_raw:
            assert p_raw != c_raw
            assert "pilot" in p_raw
            assert "confirm" in c_raw


def test_p8_09_table_values_equal_processed_json_values():
    """P8-09: Test that table values equal processed JSON values."""
    table_path = ROOT / "blog/assets/03_musique_confirmation_table.md"
    assert table_path.is_file()
    lines = [line.strip() for line in table_path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("|:")]
    # Header is line 0, data starts line 1
    data_rows = lines[1:]
    assert len(data_rows) == 12, f"Expected 12 table rows, got {len(data_rows)}"

    m500 = json.loads((ROOT / "results/processed/musique_500_confirmatory.json").read_text(encoding="utf-8"))
    model_name_map = {
        "Tiny Aya Global": "CohereLabs/tiny-aya-global-GGUF:q4_k_m",
        "Qwen 2.5 1.5B": "Qwen/Qwen2.5-1.5B-Instruct-GGUF:q4_k_m",
        "Gemma 4 E2B": "google/gemma-4-E2B-it-qat-q4_0-gguf",
        "Gemma 4 E4B": "google/gemma-4-E4B-it-qat-q4_0-gguf",
        "Qwen 3.5 2B": "unsloth/Qwen3.5-2B-GGUF:q4_k_m",
        "Qwen 3.5 4B": "unsloth/Qwen3.5-4B-GGUF:q4_k_m",
    }
    # Index m500 effects by (model, sources)
    effects_by_key = {}
    for m in m500["models"]:
        for eff in m.get("effects", []):
            if eff.get("metric") == "binding_recall":
                effects_by_key[(m["model"], int(eff["sources"]))] = eff

    for row in data_rows:
        parts = [p.strip() for p in row.split("|")[1:-1]]
        clean_model = parts[0].replace("**", "")
        sources = int(parts[1])
        delta_str = parts[2].replace("**", "")
        ci_str = parts[3]
        model_name = model_name_map[clean_model]
        expected_eff = effects_by_key[(model_name, sources)]
        expected_delta = expected_eff["b_minus_a"] * 100.0
        assert float(delta_str) == pytest.approx(expected_delta, abs=0.02)


def test_p8_10_prose_significance_counts_match_generated_analysis():
    """P8-10: Test that prose significance counts equal generated analysis counts."""
    m500 = json.loads((ROOT / "results/processed/musique_500_confirmatory.json").read_text(encoding="utf-8"))
    sig_count = 0
    total_cells = 0
    for model_data in m500["models"]:
        for eff in model_data.get("effects", []):
            if eff.get("metric") == "binding_recall":
                total_cells += 1
                if eff["bootstrap_95_ci"][1] < 0:
                    sig_count += 1
    assert total_cells == 12
    assert sig_count == 12, "All 12 MuSiQue N=500 cells must strictly exclude zero in citation recall delta"

    # Stage 8 significance classifications
    s8 = json.loads((ROOT / "results/processed/stage8_pii_500_cross_model.json").read_text(encoding="utf-8"))
    counts = s8.get("classification_counts", {})
    assert counts.get("supported") == 4
    assert counts.get("ceiling_limited") == 2
    assert counts.get("positive_nonsignificant") == 0


def test_p8_11_stage8_denominators():
    """P8-11: Test the 12,000 / 9,000 / 6,000 Stage 8 denominators."""
    s8 = json.loads((ROOT / "results/processed/stage8_pii_500_cross_model.json").read_text(encoding="utf-8"))
    denoms = s8.get("denominators", {})
    assert denoms.get("all_four_conditions") == 12_000
    assert denoms.get("three_masked_conditions") == 9_000
    assert denoms.get("typed_and_untyped") == 6_000

    # The displayed cross-model accuracies must aggregate both the 15- and
    # 20-source strata and agree arithmetically with the paired effect.
    for model in s8["models"]:
        observed_delta = model["typed_accuracy"] - model["untyped_accuracy"]
        assert observed_delta == pytest.approx(model["typed_minus_untyped_mean"], abs=1e-12)

    # Frontier Stage 8 (2 models x 2000 items = 4000)
    frontier_stage8_dir = ROOT / "results/raw/stage8"
    if frontier_stage8_dir.exists():
        frontier_gens = sum(
            sum(1 for line in p.read_text(encoding="utf-8").splitlines() if line.strip())
            for p in frontier_stage8_dir.glob("*.jsonl")
        )
        assert frontier_gens == 4_000, f"Expected 4,000 frontier Stage 8 generations, got {frontier_gens}"


def test_p8_12_partial_frontier_batches_cannot_be_marked_publishable(manifest):
    """P8-12: Test that partial frontier batches cannot be marked publishable."""
    for exp_id, exp in manifest.get("experiments", {}).items():
        if exp.get("publication_status") == "publishable":
            raw_paths = exp.get("raw_paths", {})
            for model_id, rel_path in raw_paths.items():
                path = ROOT / rel_path
                assert path.is_file(), f"Publishable experiment {exp_id} is missing raw path {rel_path}"
                lines = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
                expected = exp.get("expected_calls_per_model")
                if expected:
                    assert lines == expected, f"Publishable {exp_id} model {model_id} has {lines} != {expected}"


def test_p8_13_frontier_models_never_in_mechanistic_totals(manifest):
    """P8-13: Test that frontier models never appear in mechanistic totals."""
    for exp_id in ["stage6_geometry", "stage7_interventions"]:
        exp = manifest["experiments"][exp_id]
        assert exp["evidence_tier"] == "mechanistic"
        exp_models = set(exp["models"])
        assert exp_models.isdisjoint(FRONTIER_MODELS), f"Frontier model in mechanistic {exp_id}"
        assert len(exp_models) == 6, f"Expected exactly 6 eligible models in {exp_id}"


def test_p8_14_figure7_captions_match_plotted_evidence_type():
    """P8-14: Test that Figure 7 captions distinguish prompt swaps from activation patching."""
    f7_path = ROOT / "blog/assets/07_stage7_swaps.svg"
    content = f7_path.read_text(encoding="utf-8")
    assert "Figure 7A" in content
    assert "swap" in content.lower()
    assert "prompt swaps only" in content.lower()

    # Figure 7B must exist and plot activation patching separately
    f7b_path = ROOT / "blog/assets/07b_stage7_patching.svg"
    assert f7b_path.is_file(), "Missing Figure 7B (07b_stage7_patching.svg)"
    content_b = f7b_path.read_text(encoding="utf-8")
    assert "Figure 7B" in content_b
    assert "activation patching" in content_b.lower()
    assert "2,160 activation patches" in content_b


def test_p8_15_generated_figures_not_older_than_input_artifacts():
    """P8-15: Test that generated figures are not older than their input artifacts."""
    fig3 = ROOT / "blog/assets/03_musique_confirmation.svg"
    art3 = ROOT / "results/processed/musique_500_confirmatory.json"
    assert fig3.stat().st_mtime >= art3.stat().st_mtime - 1.0

    fig5 = ROOT / "blog/assets/05_longproc.svg"
    art5 = ROOT / "results/processed/longproc_gpu_summary.json"
    assert fig5.stat().st_mtime >= art5.stat().st_mtime - 1.0


def test_p8_16_figure2_mechanistic_counts_match_stage7_accounting():
    """P8-16: Figure 2 must not retain pre-parity Stage 7 intervention totals."""
    for rel_path in [
        "blog/assets/02_evidence_funnel.svg",
        "blog/assets/02_evidence_funnel_mobile.svg",
        "blog/site/assets/02_evidence_funnel.svg",
        "blog/site/assets/02_evidence_funnel_mobile.svg",
    ]:
        content = (ROOT / rel_path).read_text(encoding="utf-8")
        assert "1,440 + 2,304" in content
        assert "Source-ID swaps (144)" in content
        assert "Residual patches (2,160)" in content
        assert "1,440 + 1,824" not in content
        assert "Source-ID swaps (114)" not in content
        assert "Residual patches (1,710)" not in content


def test_p8_17_study_accounting_mechanistic_integrity(accounting):
    """P8-17: Test that study_accounting.json contains non-zero verified mechanistic calls."""
    assert accounting["local_completed_calls"] == 46_230
    assert accounting["frontier_completed_calls"] == 13_760
    assert accounting["mechanistic_completed_calls"] == 3_744
    assert accounting["total_verified_calls"] == 63_734

    s6 = accounting["by_experiment"]["stage6_geometry"]
    assert s6["mechanistic_completed"] == 1_440
    assert s6["evidence_tier"] == "mechanistic"

    s7 = accounting["by_experiment"]["stage7_interventions"]
    assert s7["mechanistic_completed"] == 2_304
    assert s7["evidence_tier"] == "mechanistic"


def test_p8_18_mechanistic_eligibility_report_freshness():
    """P8-18: Test that mechanistic_eligibility_report.json classifies all 6 local models as eligible."""
    rep_path = ROOT / "results/audit/mechanistic_eligibility_report.json"
    assert rep_path.is_file()
    rep = json.loads(rep_path.read_text(encoding="utf-8"))

    local_cohort = rep.get("local_models", {})
    assert set(local_cohort.keys()) == LOCAL_6_MODELS
    for m_key, m_info in local_cohort.items():
        assert m_info["eligible"] is True, f"Model {m_key} is not eligible: {m_info}"
        assert m_info["status"] == "eligible"
        assert m_info["failure_reason"] is None
        assert m_info["hook_framework_compatible"] is True
        assert m_info["residual_capture_verified"] is True

    assert rep.get("eligible_cohort") == sorted(list(LOCAL_6_MODELS), key=lambda x: [
        "tiny_aya_global", "qwen25_15b", "gemma4_e2b", "gemma4_e4b", "qwen35_2b", "qwen35_4b"
    ].index(x))
    assert rep.get("unsupported_cohort") == []

    # Frontier models must remain not_applicable
    for f_key in FRONTIER_MODELS:
        f_info = rep["frontier_models"][f_key]
        assert f_info["status"] == "not_applicable"
        assert f_info["eligible"] is False


def test_p8_19_headline_totals_uniform_across_all_surfaces():
    """P8-19: Test that headline totals across blog, site, and appendix match manifest totals."""
    blog_text = (ROOT / "blog/symbolic-ir-engineering-blog.md").read_text(encoding="utf-8")
    site_text = (ROOT / "blog/site/index.html").read_text(encoding="utf-8")
    appendix_text = (ROOT / "blog/appendix.md").read_text(encoding="utf-8")

    forbidden = [
        "57,397",
        "63,706",
        "21,397",
        "6,400 Anthropic",
        "6,400 completed Anthropic",
    ]
    for text, name in [(blog_text, "blog"), (site_text, "site"), (appendix_text, "appendix")]:
        for f in forbidden:
            assert f not in text, f"Found legacy/inconsistent count '{f}' in {name}"

    # Required authoritative counts must be present
    for text, name in [(blog_text, "blog"), (site_text, "site"), (appendix_text, "appendix")]:
        assert "46,230" in text, f"Missing 46,230 local calls in {name}"
        assert "13,760" in text, f"Missing 13,760 frontier calls in {name}"
        assert "1,440" in text, f"Missing 1,440 geometry passes in {name}"
        assert "2,304" in text, f"Missing 2,304 causal interventions in {name}"


def test_p8_20_figure7_panels_distinct_and_complete():
    """P8-20: Test that both Figure 7A and Figure 7B exist in assets and site assets."""
    for dirname in ["blog/assets", "blog/site/assets"]:
        p_7a = ROOT / dirname / "07_stage7_swaps.svg"
        p_7b = ROOT / dirname / "07b_stage7_patching.svg"
        assert p_7a.is_file(), f"Missing {p_7a}"
        assert p_7b.is_file(), f"Missing {p_7b}"

    blog_text = (ROOT / "blog/symbolic-ir-engineering-blog.md").read_text(encoding="utf-8")
    site_text = (ROOT / "blog/site/index.html").read_text(encoding="utf-8")

    assert "assets/07_stage7_swaps.svg" in blog_text
    assert "assets/07b_stage7_patching.svg" in blog_text
    assert "assets/07_stage7_swaps.svg" in site_text
    assert "assets/07b_stage7_patching.svg" in site_text


def test_p8_21_frontier_no_architectural_or_scratchpad_inferences():
    """P8-21: Test that frontier models are never labeled with architectural or scratchpad inferences."""
    rep_text = (ROOT / "results/reports/frontier_evaluation_final.md").read_text(encoding="utf-8")
    evidence_csv = (ROOT / "blog/evidence_manifest.csv").read_text(encoding="utf-8")

    # Forbidden phrases for black-box frontier APIs
    assert "direct next-token" not in rep_text.lower()
    assert "scratchpad" not in rep_text.lower()
    assert "direct next-token" not in evidence_csv.lower()


def test_p8_22_stage9_systems_boundary_integrity(manifest, accounting):
    """P8-22: Test Stage 9 deterministic software execution accounting and result integrity."""
    assert "stage9_systems_boundary" in manifest["experiments"]
    exp = manifest["experiments"]["stage9_systems_boundary"]
    assert exp["evidence_tier"] == "systems"
    assert exp["deterministic_software_executions"] == 6_000
    assert exp["cross_request_isolation_checks"] == 499

    s9 = accounting["by_experiment"]["stage9_systems_boundary"]
    assert s9["systems_completed"] == 6_000
    assert accounting["systems_completed_executions"] == 6_000

    s9_res_path = ROOT / "results/processed/stage9_system_eval.json"
    assert s9_res_path.is_file()
    data = json.loads(s9_res_path.read_text(encoding="utf-8"))
    assert data["requests"] == 500
    assert data["correct"]["accepted"] == 500
    assert data["total_attack_cases"] == 5_000
    assert data["adversarial"]["overall_rejection_rate"] == 1.0
    assert data["semantic_boundary"]["wrong_existing_handle_cases"] == 500
    assert data["isolation"]["cross_request_rehydration_blocked"] == 499


def test_p8_23_visual_qa_programmatic_certification():
    """P8-23: Test that visual QA programmatically measures 0 horizontal overflow and 0 clipped labels/legends."""
    cdp_path = ROOT / "results/qa/cdp_audit_summary.json"
    assert cdp_path.is_file(), "CDP audit summary must exist"
    cdp_data = json.loads(cdp_path.read_text(encoding="utf-8"))

    # Responsive viewports: 0px overflow
    assert len(cdp_data.get("viewports", [])) == 3
    for vp in cdp_data["viewports"]:
        assert vp["metrics"]["overflowDiff"] == 0, f"Viewport {vp['name']} has horizontal overflow!"

    # Programmatic SVG bounding box measurements
    svg_audits = cdp_data.get("svgAudits", {})
    assert len(svg_audits) == 13, f"Expected 13 audited SVGs, got {len(svg_audits)}"

    total_texts = 0
    total_rects = 0
    for fig_name, audit in svg_audits.items():
        assert audit["clippedTexts"] == 0, f"Figure {fig_name} has {audit['clippedTexts']} clipped text elements!"
        assert audit["clippedRects"] == 0, f"Figure {fig_name} has {audit['clippedRects']} clipped rect elements!"
        total_texts += audit["totalTexts"]
        total_rects += audit["totalRects"]

    assert total_texts >= 500, f"Expected at least 500 text elements measured, got {total_texts}"
    assert total_rects >= 100, f"Expected at least 100 rect elements measured, got {total_rects}"

    # Visual QA report certification
    report_path = ROOT / "results/qa/visual_qa_report.md"
    assert report_path.is_file()
    report_text = report_path.read_text(encoding="utf-8")
    assert "Current visual QA audit PASSED with 100% compliance" in report_text
    assert "0 clipped" in report_text
