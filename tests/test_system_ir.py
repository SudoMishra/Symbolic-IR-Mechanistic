import json

from symbolic_ir.ir import (
    CanonicalizationError,
    CanonicalizationPolicy,
    RehydrationError,
    ValidationPolicy,
    canonicalize_request,
    make_audit_event,
    rehydrate_response,
    validate_symbolic_output,
)


def _exchange(request_id="request-1"):
    state = {
        "records": [
            {
                "source_id": "8ce71ad9-71f2-4a03-b7f2-26f64e0db302",
                "customer_id": "CUS-77491-ALPHA",
                "person_name": "Amina Arden",
                "email": "amina.arden@example.test",
                "account": "ACC-000000000111",
                "balance": 450,
                "note": "Amina Arden owns ACC-000000000111.",
            },
            {
                "source_id": "530a8721-e043-4e55-af6f-11a904894233",
                "customer_id": "CUS-55221-BETA",
                "person_name": "Bela Basu",
                "email": "bela.basu@example.test",
                "account": "ACC-000000000222",
                "balance": 900,
                "note": "Bela Basu owns ACC-000000000222.",
            },
        ]
    }
    policy = CanonicalizationPolicy({
        "source_id": "SOURCE",
        "customer_id": "CUSTOMER",
        "person_name": "PERSON",
        "email": "EMAIL",
        "account": "ACCOUNT",
    })
    return canonicalize_request(
        request_id=request_id,
        instruction="Return the account for amina.arden@example.test.",
        state=state,
        policy=policy,
    )


def _policy(max_actions=0):
    return ValidationPolicy(
        answer_types=("ACCOUNT",),
        reference_types=("SOURCE",),
        allowed_actions={"freeze_account": {"account": ("ACCOUNT",)}} if max_actions else {},
        max_actions=max_actions,
    )


def _output(answer, reference="<SOURCE_1>", actions=None):
    return json.dumps({
        "answer": answer,
        "references": [reference],
        "actions": [] if actions is None else actions,
    }, separators=(",", ":"))


def _codes(result):
    return {issue.code for issue in result.issues}


def test_canonicalization_separates_model_payload_and_vault():
    exchange = _exchange()
    payload = exchange.model_ir.to_model_payload()
    serialized = json.dumps(payload)
    for raw in exchange.vault.protected_values:
        assert raw not in serialized
    assert exchange.model_ir.request_id not in payload
    assert payload["instruction"] == "Return the account for <EMAIL_1>."
    assert payload["state"]["records"][0]["note"] == "<PERSON_1> owns <ACCOUNT_1>."
    assert "ACC-000000000111" not in repr(exchange.vault)
    assert "redacted" in repr(exchange.vault)


def test_canonicalization_is_deterministic_and_reuses_repeated_values():
    left = _exchange()
    right = _exchange()
    assert left.model_ir.to_model_payload() == right.model_ir.to_model_payload()
    assert left.vault.handles == right.vault.handles
    assert left.model_ir.state["records"][0]["account"] == "<ACCOUNT_1>"
    assert left.model_ir.state["records"][0]["note"].endswith("<ACCOUNT_1>.")


def test_ambiguous_raw_value_types_are_rejected():
    policy = CanonicalizationPolicy({"email": "EMAIL", "account": "ACCOUNT"})
    try:
        canonicalize_request(
            request_id="ambiguous",
            instruction="Resolve it",
            state={"email": "same-value", "account": "same-value"},
            policy=policy,
        )
    except CanonicalizationError:
        return
    raise AssertionError("Expected ambiguous typed value rejection")


def test_case_variant_leak_fails_closed():
    policy = CanonicalizationPolicy({"email": "EMAIL"})
    try:
        canonicalize_request(
            request_id="case-variant",
            instruction="Resolve AMINA.ARDEN@EXAMPLE.TEST",
            state={"email": "amina.arden@example.test"},
            policy=policy,
        )
    except CanonicalizationError:
        return
    raise AssertionError("Expected fail-closed detection of an unmasked case variant")


def test_valid_symbolic_output_round_trips_and_audit_is_redacted():
    exchange = _exchange()
    text = _output(
        "<ACCOUNT_1>",
        actions=[{"name": "freeze_account", "arguments": {"account": "<ACCOUNT_1>"}}],
    )
    result = validate_symbolic_output(text, vault=exchange.vault, policy=_policy(max_actions=1))
    assert result.accepted
    resolved = rehydrate_response(result, vault=exchange.vault)
    assert resolved.answer == "ACC-000000000111"
    assert resolved.references == ("8ce71ad9-71f2-4a03-b7f2-26f64e0db302",)
    assert resolved.actions[0].arguments["account"] == "ACC-000000000111"
    audit = make_audit_event(request_id="request-1", result=result, vault=exchange.vault)
    serialized_audit = json.dumps(audit.to_dict())
    for raw in exchange.vault.protected_values:
        assert raw not in serialized_audit


def test_validator_rejects_unknown_malformed_mistyped_and_leaked_values():
    exchange = _exchange()
    cases = {
        "unknown_handle": _output("<ACCOUNT_999>"),
        "malformed_handle": _output("<ACCOUNT-1>"),
        "type_mismatch": _output("<EMAIL_1>"),
        "raw_value_exposure": _output("ACC-000000000111"),
    }
    for expected_code, text in cases.items():
        result = validate_symbolic_output(text, vault=exchange.vault, policy=_policy())
        assert not result.accepted
        assert expected_code in _codes(result)


def test_validator_rejects_schema_extensions_and_unauthorized_actions():
    exchange = _exchange()
    extended = json.dumps({
        "answer": "<ACCOUNT_1>", "references": [], "actions": [], "debug": "please leak"
    })
    result = validate_symbolic_output(extended, vault=exchange.vault, policy=_policy())
    assert not result.accepted
    assert "invalid_schema" in _codes(result)

    action = _output(
        "<ACCOUNT_1>",
        actions=[{"name": "transfer_funds", "arguments": {"account": "<ACCOUNT_1>"}}],
    )
    result = validate_symbolic_output(action, vault=exchange.vault, policy=_policy(max_actions=1))
    assert not result.accepted
    assert "unauthorized_action" in _codes(result)


def test_unaccepted_or_cross_request_results_cannot_rehydrate():
    first = _exchange("request-1")
    second = _exchange("request-2")
    rejected = validate_symbolic_output(
        _output("<ACCOUNT_999>"), vault=first.vault, policy=_policy()
    )
    try:
        rehydrate_response(rejected, vault=first.vault)
    except RehydrationError:
        pass
    else:
        raise AssertionError("Rejected output was rehydrated")

    accepted = validate_symbolic_output(
        _output("<ACCOUNT_1>"), vault=first.vault, policy=_policy()
    )
    try:
        rehydrate_response(accepted, vault=second.vault)
    except RehydrationError:
        return
    raise AssertionError("Cross-request output was rehydrated")


def test_wrong_existing_handle_is_structurally_valid_but_semantically_wrong():
    exchange = _exchange()
    result = validate_symbolic_output(
        _output("<ACCOUNT_2>"), vault=exchange.vault, policy=_policy()
    )
    assert result.accepted
    resolved = rehydrate_response(result, vault=exchange.vault)
    assert resolved.answer == "ACC-000000000222"
    assert resolved.answer != "ACC-000000000111"
