import json

from symbolic_ir.config import ExperimentConfig
from symbolic_ir.runner import iter_requests, run_experiment


def test_runner_is_resumable_and_preserves_required_fields(tmp_path):
    config = ExperimentConfig.from_dict({
        "name": "test", "seed": 11,
        "dataset": {"family": "citation", "count": 3, "num_sources": 5, "task_type": "single_hop"},
        "identifiers": ["structured", "uuid"], "backend": {"type": "oracle"},
        "generation": {"temperature": 0, "max_output_tokens": 64}, "output_dir": str(tmp_path),
    })
    path, first = run_experiment(config)
    assert first == {"planned": 6, "completed": 6, "skipped": 0}
    _, second = run_experiment(config)
    assert second == {"planned": 6, "completed": 0, "skipped": 6}
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert len(rows) == 6
    required = {"example_id", "seed", "task_type", "model", "model_revision", "prompt", "identifier_condition", "identifier_mapping", "identifier_token_lengths", "source_order", "relevant_sources", "reasoning_budget", "generation_parameters", "raw_output", "parsed_answer", "parsed_citations", "token_counts", "latency"}
    assert required <= rows[0].keys()
    assert all(row["evaluation"]["answer_correct"] for row in rows)


def test_fixed_source_identifiers_isolate_pii_representation():
    config = ExperimentConfig.from_dict({
        "name": "pii-fixed-source-labels", "seed": 11,
        "dataset": {"family": "pii", "count": 1, "num_sources": 5,
                    "task_type": "account_resolution"},
        "identifiers": ["raw", "untyped", "typed"], "backend": {"type": "oracle"},
        "generation": {"fixed_source_identifiers": "structured", "require_citations": False},
    })
    rendered = [item[1] for item in iter_requests(config)]
    assert len(rendered) == 3
    assert all(set(item.mapping.display_by_source.values()) == {"[S1]", "[S2]", "[S3]", "[S4]", "[S5]"}
               for item in rendered)
    assert "<ENTITY_" in rendered[1].prompt
    assert "<PERSON_" in rendered[2].prompt
    assert rendered[1].mapping.condition == "untyped"
