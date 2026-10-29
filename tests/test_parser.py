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


def test_parser_handles_same_line_citations():
    parsed = parse_output("ANSWER: Caldris, CITATIONS: [S3]", ["[S1]", "[S2]", "[S3]"])
    assert parsed.answer == "Caldris"
    assert parsed.citations == ("[S3]",)
    assert parsed.has_citation_field is True
    assert parsed.strict_format is False


def test_parser_strict_two_line_compliance():
    two_line = parse_output("ANSWER: Caldris\nCITATIONS: [S3]", ["[S3]"])
    assert two_line.answer == "Caldris"
    assert two_line.citations == ("[S3]",)
    assert two_line.strict_format is True

    same_line = parse_output("ANSWER: Caldris, CITATIONS: [S3]", ["[S3]"])
    assert same_line.strict_format is False

