from symbolic_ir.data.pii import generate_pii_examples
from symbolic_ir.identifiers import render_identifiers
from symbolic_ir.prompts import render_prompt
from symbolic_ir.tokenization import RegexTokenCounter


def test_typed_prompt_masks_all_entity_values():
    example = generate_pii_examples(seed=2, count=1, num_sources=5)[0]
    mapping = render_identifiers(example.sources, "typed", 2, RegexTokenCounter())
    rendered = render_prompt(example, mapping)
    for fields in example.entities.values():
        for value in fields.values():
            assert value not in rendered.prompt
    assert rendered.expected_answer.startswith("<ACCOUNT_")


def test_raw_prompt_preserves_values():
    example = generate_pii_examples(seed=2, count=1, num_sources=5)[0]
    mapping = render_identifiers(example.sources, "raw", 2, RegexTokenCounter())
    rendered = render_prompt(example, mapping)
    assert example.answer in rendered.prompt


def test_long_context_pii_is_deterministic_and_keeps_task_fields():
    left = generate_pii_examples(
        seed=9, count=1, num_sources=15, long_context=True, filler_words=80
    )[0]
    right = generate_pii_examples(
        seed=9, count=1, num_sources=15, long_context=True, filler_words=80
    )[0]
    assert left == right
    assert left.answer in " ".join(source.text for source in left.sources)
    assert left.metadata["filler_words"] == 80
