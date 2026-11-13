"""Unit tests for Stage 7B component localization infrastructure."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def test_component_hook_audit_report_valid():
    audit_file = ROOT / "results/audit/component_hook_audit.json"
    assert audit_file.exists(), "component_hook_audit.json must exist"

    data = json.loads(audit_file.read_text(encoding="utf-8"))
    canonical_models = ["qwen25_15b", "qwen35_2b", "tiny_aya", "qwen35_4b", "gemma4_e2b", "gemma4_e4b"]
    for m_key in canonical_models:
        assert m_key in data, f"{m_key} must be audited in component_hook_audit.json"

    # Assert candidate layers from preregistration are audited
    prereg_p = ROOT / "results/circuit/circuit_preregistration.json"
    if prereg_p.exists():
        prereg = json.loads(prereg_p.read_text(encoding="utf-8"))["candidate_circuits"]
        key_map = {
            "qwen25_15b": "qwen2.5-1.5b-instruct",
            "qwen35_2b": "qwen3.5-2b",
            "tiny_aya": "tiny-aya-global",
            "qwen35_4b": "qwen3.5-4b",
            "gemma4_e2b": "gemma-4-e2b-it",
            "gemma4_e4b": "gemma-4-e4b-it",
        }
        for m_key, prereg_id in key_map.items():
            cand_layers = prereg.get(prereg_id, {}).get("candidate_layers", [])
            audited = [int(l) for l in data[m_key]["layers_audited"].keys()]
            for l_cand in cand_layers:
                assert l_cand in audited, f"Candidate layer {l_cand} for {m_key} must be audited"

    for model_name, summary in data.items():
        assert summary["gate_passed"] is True, f"Gate failed for {model_name}"
        for layer_str, layer_data in summary["layers_audited"].items():
            assert layer_data["identity_hook_mixer_max_diff"] < 1e-4, f"Mixer identity hook drift at layer {layer_str}"
            assert layer_data["identity_hook_mlp_max_diff"] < 1e-4, f"MLP identity hook drift at layer {layer_str}"
            assert layer_data["perturbation_mixer_diff"] > 0.1, f"Perturbation hook ineffective at layer {layer_str}"


def test_circuit_dataset_splits_disjoint_and_balanced():
    data_dir = ROOT / "data/circuit"
    disc_file = data_dir / "discovery_n32.jsonl"
    val_file = data_dir / "validation_n32.jsonl"
    conf_file = data_dir / "confirmation_n80.jsonl"

    assert disc_file.exists(), "Discovery split must exist"
    assert val_file.exists(), "Validation split must exist"
    assert conf_file.exists(), "Confirmation split must exist"

    disc_cases = [json.loads(line) for line in disc_file.read_text().splitlines() if line.strip()]
    val_cases = [json.loads(line) for line in val_file.read_text().splitlines() if line.strip()]
    conf_cases = [json.loads(line) for line in conf_file.read_text().splitlines() if line.strip()]

    assert len(disc_cases) == 96, "Discovery split must have 96 cases (32 examples x 3 conditions)"
    assert len(val_cases) == 96, "Validation split must have 96 cases (32 examples x 3 conditions)"
    assert len(conf_cases) == 240, "Confirmation split must have 240 cases (80 examples x 3 conditions)"

    # Assert example IDs are strictly disjoint
    disc_ids = set(c["example_id"] for c in disc_cases)
    val_ids = set(c["example_id"] for c in val_cases)
    conf_ids = set(c["example_id"] for c in conf_cases)

    assert len(disc_ids) == 32
    assert len(val_ids) == 32
    assert len(conf_ids) == 80

    assert disc_ids.isdisjoint(val_ids), "Discovery and Validation splits must be disjoint"
    assert disc_ids.isdisjoint(conf_ids), "Discovery and Confirmation splits must be disjoint"
    assert val_ids.isdisjoint(conf_ids), "Validation and Confirmation splits must be disjoint"


def test_cluster_bootstrap_resampling():
    from scripts.analyze_circuit_results import cluster_bootstrap_mean_ci

    # 10 clusters, each with 3 correlated observations
    items = []
    for i in range(10):
        base_val = float(i)
        items.append((f"ex_{i}", base_val - 0.1))
        items.append((f"ex_{i}", base_val))
        items.append((f"ex_{i}", base_val + 0.1))

    mean_v, low, high = cluster_bootstrap_mean_ci(items, n_boot=500)
    assert abs(mean_v - 4.5) < 1e-4, f"Expected mean 4.5, got {mean_v}"
    assert low < mean_v < high, "Confidence interval must bracket mean"
    assert 2.0 < low < 4.0, f"Lower bound {low} outside expected range"
    assert 5.0 < high < 7.0, f"Upper bound {high} outside expected range"


def test_token_parsing_and_continuation_indices():
    from transformers import AutoTokenizer
    from scripts.run_circuit_decomposition import find_first_distinguishing_index

    tok = AutoTokenizer.from_pretrained("models/qwen2.5-1.5b-instruct-hf")

    # Structured condition: [S7] vs [S1]
    t_clean = tok.encode("[S7]", add_special_tokens=False)
    t_swap = tok.encode("[S1]", add_special_tokens=False)
    d_idx = find_first_distinguishing_index(t_clean, t_swap)
    assert d_idx == 1, "First distinguishing token should be digit at index 1"
    clean_cont = t_clean[d_idx + 1 : -1]
    assert len(clean_cont) == 0, "Structured labels should have NO continuation tokens before delimiter"

    # UUID condition
    u_clean = tok.encode("[f1b72100-79db-7ffb-c06b-7e95aabffe54]", add_special_tokens=False)
    u_swap = tok.encode("[1399fd0a-86af-c1c0-ce3f-a63b40bd9382]", add_special_tokens=False)
    du_idx = find_first_distinguishing_index(u_clean, u_swap)
    u_cont = u_clean[du_idx + 1 : -1]
    assert len(u_cont) > 20, "UUID labels must have >20 continuation tokens"


def test_gemma4_e4b_ple_offload_contract():
    """Verify that Gemma 4 E4B offload configuration is valid and routes PLE to CPU."""
    import torch
    from transformers import AutoConfig, AutoModelForMultimodalLM
    from accelerate import infer_auto_device_map
    from symbolic_ir.config import load_config

    cfg_p = ROOT / "configs/circuit/circuit_gemma4_e4b.yaml"
    assert cfg_p.exists(), "circuit_gemma4_e4b.yaml must exist"
    cfg = load_config(cfg_p)

    assert cfg.backend["auto_class"] == "multimodal_lm"
    assert cfg.backend.get("text_only") is True
    assert "cpu" in str(cfg.backend.get("max_memory", {})).lower()

    hf_config = AutoConfig.from_pretrained(cfg.backend["model_path"])
    with torch.device("meta"):
        meta_model = AutoModelForMultimodalLM.from_config(hf_config)
    meta_model.model.language_model.embed_tokens_per_layer.weight = torch.nn.Parameter(torch.empty(1, device="meta"))

    d_map = infer_auto_device_map(
        meta_model,
        max_memory={0: "5.2GiB", "cpu": "24GiB"},
        no_split_module_classes=["Gemma4TextDecoderLayer"],
        dtype=torch.bfloat16,
    )
    d_map["model.language_model.embed_tokens_per_layer"] = "cpu"
    assert d_map["model.language_model.embed_tokens_per_layer"] == "cpu", "PLE must map to CPU"


def test_dataset_manifest_hashes_and_relative_paths():
    """Verify that dataset_manifest.json uses relative paths and valid SHA-256 hashes."""
    import hashlib

    manifest_p = ROOT / "data/circuit/dataset_manifest.json"
    assert manifest_p.exists(), "dataset_manifest.json must exist"

    manifest = json.loads(manifest_p.read_text(encoding="utf-8"))
    for split_key in ["discovery", "validation", "confirmation"]:
        assert split_key in manifest, f"Missing split {split_key} in manifest"
        split_data = manifest[split_key]
        rel_file = split_data["file"]
        assert not rel_file.startswith("/"), f"Path {rel_file} must be relative"
        assert "home" not in rel_file, f"Path {rel_file} must not contain user directories"

        file_p = ROOT / rel_file
        assert file_p.exists(), f"Target file {file_p} must exist"

        actual_sha = hashlib.sha256(file_p.read_bytes()).hexdigest()
        assert actual_sha == split_data["sha256"], f"SHA256 mismatch for {rel_file}"

    # Verify preregistration hash
    assert "preregistration" in manifest, "Manifest must track preregistration"
    prereg_file = manifest["preregistration"]["file"]
    assert not prereg_file.startswith("/"), "Preregistration path must be relative"
    prereg_p = ROOT / prereg_file
    assert prereg_p.exists(), f"Preregistration file {prereg_p} must exist"
    actual_prereg_sha = hashlib.sha256(prereg_p.read_bytes()).hexdigest()
    assert actual_prereg_sha == manifest["preregistration"]["sha256"], "SHA256 mismatch for preregistration"


def test_analyze_head_results_execution(tmp_path):
    """Verify that head results analysis imports and runs correctly with cluster bootstrap."""
    from scripts.analyze_head_results import analyze_heads

    input_p = ROOT / "results/circuit/qwen25_head_scores_l24.jsonl"
    assert input_p.exists(), "Head scores fixture must exist"

    out_p = tmp_path / "test_ranking.json"
    analyze_heads(input_p, out_p)
    assert out_p.exists(), "Output ranking file should be written"

    data = json.loads(out_p.read_text(encoding="utf-8"))
    assert "ranked_heads" in data
    assert len(data["ranked_heads"]) == 12
    # Check that bootstrap interval was computed
    first_head = data["ranked_heads"][0]
    assert "shift_ci_95" in first_head
    assert len(first_head["shift_ci_95"]) == 2



