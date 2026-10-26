from symbolic_ir.data.citation import generate_citation_examples
from symbolic_ir.data.pii import generate_pii_examples
from symbolic_ir.data.reasoning import generate_reasoning_examples


def test_citation_generation_is_deterministic():
    first = generate_citation_examples(seed=7, count=3, num_sources=5, task_type="single_hop")
    second = generate_citation_examples(seed=7, count=3, num_sources=5, task_type="single_hop")
    assert first == second
    assert first != generate_citation_examples(seed=8, count=3, num_sources=5, task_type="single_hop")


def test_reasoning_answer_matches_formula():
    example = generate_reasoning_examples(seed=9, count=1, num_sources=8)[0]
    attrs = {source.key: source.text for source in example.sources}
    assert set(example.relevant_sources) == {"units", "price", "return-policy"}
    assert example.answer
    assert len(attrs) == 8
    if "." in example.answer:
        assert example.answer.rstrip("0").rstrip(".") in example.metadata["answer_aliases"]


def test_all_reasoning_families_are_deterministic_and_long_context():
    for task_type in ("arithmetic", "temporal", "constraint", "entity_resolution"):
        kwargs = dict(seed=91, count=2, num_sources=12, task_type=task_type,
                      long_context=True, filler_words=40)
        first = generate_reasoning_examples(**kwargs)
        assert first == generate_reasoning_examples(**kwargs)
        assert all(len(example.sources) == 12 for example in first)
        assert all(example.answer and len(example.relevant_sources) >= 3 for example in first)


def test_pii_is_synthetic_and_target_is_present():
    example = generate_pii_examples(seed=4, count=1, num_sources=5)[0]
    assert example.metadata["synthetic_only"] is True
    assert any(example.answer in source.text for source in example.sources)
