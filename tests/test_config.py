from pathlib import Path

from symbolic_ir.config import expand_grid, load_config


def test_all_experiment_configs_load():
    paths = sorted(Path("configs/experiments").glob("*.yaml"))
    assert len(paths) >= 10
    for path in paths:
        config = load_config(path)
        assert config.digest
        assert list(expand_grid(config))


def test_stage_one_has_400_requests():
    from symbolic_ir.runner import iter_requests
    config = load_config("configs/experiments/citation_mve.yaml")
    assert sum(1 for _ in iter_requests(config)) == 400


def test_all_musique_model_configs_define_complete_stage_matrix():
    paths = sorted(Path("configs/musique").glob("stages_2_4_*.yaml"))
    assert len(paths) >= 5
    for path in paths:
        config = load_config(path)
        scenarios = config.dataset["scenarios"]
        assert [scenario["stage"] for scenario in scenarios] == [2, 2, 3, 4]
        requests = 0
        for scenario in scenarios:
            controls = scenario.get("controls") or scenario["identifiers"]
            requests += config.dataset["count"] * len(controls)
        assert requests == 1500
        assert config.backend["n_gpu_layers"] == -1
