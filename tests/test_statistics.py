from symbolic_ir.analysis.statistics import paired_bootstrap


def test_paired_bootstrap_uses_matched_examples():
    records = []
    for index, (a, b) in enumerate(((0, 1), (1, 1), (0, 1))):
        for condition, value in (("a", a), ("b", b)):
            records.append({"example_id": str(index), "identifier_condition": condition, "evaluation": {"citation_exact_match": value}})
    effect = paired_bootstrap(records, "a", "b", samples=200, seed=3)
    assert effect.n_pairs == 3
    assert effect.mean_delta == 2 / 3

