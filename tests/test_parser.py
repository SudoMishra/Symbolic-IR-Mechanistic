from symbolic_ir.evaluation.parser import parse_output


def test_parser_extracts_exact_citations():
    parsed = parse_output("ANSWER: Narin\nCITATIONS: [S2], [S1]", ["[S1]", "[S2]"])
    assert parsed.answer == "Narin"
    assert set(parsed.citations) == {"[S1]", "[S2]"}
    assert not parsed.invalid_ids


def test_parser_distinguishes_malformed_and_invalid():
    parsed = parse_output("ANSWER: Narin\nCITATIONS: [S11], [ZZ99]", ["[S1]", "[S2]"])
    assert "[S11]" in parsed.malformed_ids
    assert "[ZZ99]" in parsed.invalid_ids


def test_parser_handles_uuid_exactly():
    identifier = "[550e8400-e29b-41d4-a716-446655440000]"
    parsed = parse_output(f"ANSWER: x\nCITATIONS: {identifier}", [identifier])
    assert parsed.citations == (identifier,)


def test_parser_handles_missing_citation_field():
    parsed = parse_output("ANSWER: Narin", ["[S1]"])
    assert parsed.answer == "Narin"
    assert not parsed.has_citation_field

