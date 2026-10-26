import json

from symbolic_ir.data.musique import load_musique_examples
from symbolic_ir.evaluation.answer import answer_f1, musique_answer_scores


def test_musique_loader_preserves_support_and_is_deterministic(tmp_path):
    record = {
        "id": "2hop__example",
        "paragraphs": [
            {"idx": 0, "title": "A", "paragraph_text": "alpha", "is_supporting": True},
            {"idx": 1, "title": "B", "paragraph_text": "beta", "is_supporting": False},
            {"idx": 2, "title": "C", "paragraph_text": "gamma", "is_supporting": True},
            {"idx": 3, "title": "D", "paragraph_text": "delta", "is_supporting": False},
        ],
        "question": "Who?", "answer": "Alpha Beta", "answer_aliases": ["A. Beta"],
        "answerable": True,
        "question_decomposition": [{"question": "one"}, {"question": "two"}],
    }
    data_path = tmp_path / "dev.jsonl"
    data_path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    config = {"data_path": str(data_path), "count": 1, "num_sources": 3}
    first = load_musique_examples(config, 7)[0]
    second = load_musique_examples(config, 7)[0]
    assert first == second
    assert len(first.sources) == 3
    assert set(first.relevant_sources) == {"paragraph-0", "paragraph-2"}
    assert first.metadata["hop_count"] == 2


def test_answer_f1_accepts_partial_overlap_and_aliases():
    assert answer_f1("Beta", ["Alpha Beta", "Gamma"]) == 2 / 3
    assert answer_f1("A. Beta", ["Alpha Beta", "A. Beta"]) == 1.0


def test_musique_answer_scoring_matches_official_normalization():
    exact, f1 = musique_answer_scores("The Eiffel Tower!", ["Eiffel Tower"])
    assert exact
    assert f1 == 1.0
