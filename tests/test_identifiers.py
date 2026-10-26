from symbolic_ir.data.citation import generate_citation_examples
from symbolic_ir.identifiers import available_conditions, render_identifiers
from symbolic_ir.tokenization import RegexTokenCounter


def test_identifier_mappings_round_trip():
    for condition in available_conditions():
        example = generate_citation_examples(seed=3, count=1, num_sources=20)[0]
        mapping = render_identifiers(example.sources, condition, 3, RegexTokenCounter())
        assert len(mapping.display_by_source) == 20
        assert len(mapping.source_by_citation) == 20
        for source, citation in mapping.citation_by_source.items():
            assert mapping.source_by_citation[citation] == source
            assert mapping.token_lengths[source] > 0


def test_uuid_mapping_is_deterministic():
    example = generate_citation_examples(seed=3, count=1, num_sources=5)[0]
    first = render_identifiers(example.sources, "uuid", 11, RegexTokenCounter())
    second = render_identifiers(example.sources, "uuid", 11, RegexTokenCounter())
    assert first == second
