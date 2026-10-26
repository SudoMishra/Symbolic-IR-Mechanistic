from symbolic_ir.evaluation.longproc import evaluate_tom_trace, normalize_tom


REFERENCE = """Ada's belief on the key:
- Step 0: (initial state) {Ada location: hall; key location: desk}
- Step 1: (Ada location changed) {Ada location: office; key location: desk}
Final Answer: the desk
"""


def test_longproc_exact_trace_and_final_answer():
    result = evaluate_tom_trace(REFERENCE, REFERENCE)
    assert result["accuracy"] == 1.0
    assert result["partial_accuracy"] == 1.0
    assert result["final_answer_accuracy"] == 1.0
    assert result["predicted_steps"] == 2


def test_longproc_partial_accuracy_stops_at_first_wrong_step():
    prediction = REFERENCE.replace("Ada location: office", "Ada location: garden")
    result = evaluate_tom_trace(prediction, REFERENCE)
    assert result["accuracy"] == 0.0
    assert result["partial_accuracy"] == 0.5
    assert result["error_report"]["line"] == 1


def test_longproc_missing_suffix_receives_prefix_credit():
    prediction = REFERENCE.split("- Step 1:", 1)[0]
    result = evaluate_tom_trace(prediction, REFERENCE)
    assert result["accuracy"] == 0.0
    assert result["partial_accuracy"] == 0.5


def test_longproc_normalization_matches_official_behavior():
    assert normalize_tom("The key is on the desk.") == "key desk"
