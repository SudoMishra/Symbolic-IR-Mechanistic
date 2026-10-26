from symbolic_ir.data.citation import generate_citation_examples
from symbolic_ir.evaluation.evaluate import evaluate_output
from symbolic_ir.identifiers import render_identifiers
from symbolic_ir.prompts import render_prompt
from symbolic_ir.tokenization import RegexTokenCounter


def _rendered():
    example = generate_citation_examples(seed=3, count=1, num_sources=5)[0]
    mapping = render_identifiers(example.sources, "structured", 3, RegexTokenCounter())
    return render_prompt(example, mapping)


def test_correct_output_scores_perfectly():
    rendered = _rendered()
    expected = rendered.mapping.citation_by_source[rendered.canonical.relevant_sources[0]]
    result = evaluate_output(rendered, f"ANSWER: {rendered.canonical.answer}\nCITATIONS: {expected}")
    assert result["answer_correct"]
    assert result["citation_exact_match"]
    assert result["failure_category"] == "correct"


def test_missing_citation_is_classified():
    rendered = _rendered()
    result = evaluate_output(rendered, f"ANSWER: {rendered.canonical.answer}")
    assert result["failure_category"] == "missing_citation"

