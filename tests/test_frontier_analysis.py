import json
from pathlib import Path

from scripts.analyze_frontier_musique import analyze_frontier_file


def _write_record(path: Path, example_id: str, condition: str, recall: float) -> None:
    record = {
        "example_id": example_id,
        "num_sources": 15,
        "condition": condition,
        "calculated_cost": 0.25,
        "stop_reason": "end_turn",
        "token_counts": {"input": 100, "output": 10, "reasoning": 0},
        "evaluation": {
            "answer_correct": True,
            "citation_exact_match": recall == 1.0,
            "citation_precision": recall,
            "citation_recall": recall,
            "strict_format": True,
        },
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


def test_musique_analysis_reports_paired_relaxed_recall_delta(tmp_path):
    raw = tmp_path / "frontier.jsonl"
    _write_record(raw, "a", "numeric", 1.0)
    _write_record(raw, "a", "uuid", 0.5)
    _write_record(raw, "b", "numeric", 0.5)
    _write_record(raw, "b", "uuid", 0.5)

    result = analyze_frontier_file(raw)

    assert result["records"] == 4
    assert result["calculated_cost"] == 1.0
    assert result["cells"]["15_numeric"]["strict_format_rate"] == 100.0
    delta = result["deltas"]["15_sources"]["citation_recall_delta"]
    assert delta["mean_delta_pct"] == -25.0
    assert delta["n_pairs"] == 2
