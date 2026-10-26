# Stage 9 systems synthesis: an LLM-facing symbolic IR

## Decision

**Checkpoint 9 passes as a research and reference-implementation gate.** The
behavioral, mechanistic, and privacy results support a systems rule narrower
than “aliases are always better”:

> Keep a literal surface value in model context only when its exact content is
> needed for the task. Otherwise, expose a compact request-scoped typed handle,
> validate the symbolic response, and resolve it only in trusted software.

This is not a claim of production certification. The reference boundary has not
been integrated with a real identity system, database, retriever, or tool
executor, and the mapping vault is an interface—not an encryption or access-
control implementation.

## Evidence synthesized from Stages 1–8

| Evidence | Systems implication |
|---|---|
| At 20 sources, UUIDs added 70–94% input tokens and 77–129% latency in Stage 1. | Do not expose backend identifiers merely because they already exist. |
| UUID relaxed binding was worse in every model/source-count cell in the held-out MuSiQue confirmation. | Keep evidence selection separate from literal backend-ID reproduction. |
| Removing UUID reproduction sometimes recovered answer quality; UUIDs increased total output in 14/15 confirmed budget cells. | Ask the model for short handles and rehydrate outside generation. |
| Stage 6 found format-invariant source-fact geometry but format-specific late citation states. | Surface reconstruction is a separable interface burden, not necessarily part of semantic reasoning. |
| Stage 7 found correct rebinding in Qwen/Gemma but inverted binding in LFM. | Do not assume one alias syntax or causal mechanism works across model families. |
| Stage 8 found a token-matched +17.5-point typed-over-untyped gain on Qwen, but ceiling/floor limits elsewhere. | Typed handles can improve non-citation binding, but should be evaluated per model and task. |

The Stage 5 monotonic identifier-complexity × reasoning-budget hypothesis did
not replicate broadly. Stage 9 therefore treats token and reconstruction costs
as established, while treating reasoning-budget competition as conditional.

## Reference architecture

```text
trusted application state
        ↓  normalize and detect fields from an application schema
request-scoped canonicalizer ───────────→ protected mapping vault
        ↓                                  (never enters model context)
typed model view: <SOURCE_1>, <EMAIL_1>, <ACCOUNT_1>, ...
        ↓
LLM reasoning and strict symbolic JSON
        ↓
schema → leakage → registry → type → action-policy validation
        ↓ accepted only
deterministic same-request rehydration
        ↓
application authorization and side-effect layer
```

The implementation is in [`src/symbolic_ir/ir`](src/symbolic_ir/ir). It provides:

- trusted-schema field canonicalization rather than heuristic PII guessing;
- separate `ModelIR` and redacted `MappingVault` objects;
- deterministic typed handles scoped to one request;
- strict JSON parsing with no extra top-level fields;
- raw-value exposure, malformed-handle, unknown-handle, and type checks;
- per-request tool-name, argument-schema, argument-type, and action-count policy;
- refusal to rehydrate rejected or cross-request outputs;
- audit events containing hashes and handles but not mapped raw values.

Example symbolic response:

```json
{
  "answer": "<ACCOUNT_3>",
  "references": ["<SOURCE_7>"],
  "actions": [
    {"name": "lookup_account", "arguments": {"account": "<ACCOUNT_3>"}}
  ]
}
```

Handles are references, not capabilities. Rehydration does not authorize an
operation; the application must perform ordinary identity, permission,
freshness, idempotency, and business-rule checks after resolution.

## Operational evaluation

`scripts/evaluate_stage9_system.py` exercised 500 deterministic synthetic
requests containing 20 records each: 10,000 records total. It evaluated 500
valid round trips and 5,000 adversarial outputs across ten failure classes.
This is a deterministic boundary test, not another LLM-generation experiment.

| Check | Result |
|---|---:|
| Valid symbolic outputs accepted | 500 / 500 |
| Accepted outputs exactly rehydrated | 500 / 500 |
| Model payloads with no configured raw values | 500 / 500 |
| Audit records with no configured raw values | 500 / 500 |
| Deterministic canonicalization replays | 500 / 500 |
| Cross-request rehydration attempts blocked | 499 / 499 |
| Unknown handles rejected | 500 / 500 |
| Malformed handles rejected | 500 / 500 |
| Type-confused answers rejected | 500 / 500 |
| Raw protected answers rejected | 500 / 500 |
| Schema extensions rejected | 500 / 500 |
| Unauthorized actions rejected | 500 / 500 |
| Invalid tool argument schemas rejected | 500 / 500 |
| Tool argument type confusion rejected | 500 / 500 |
| Action-count violations rejected | 500 / 500 |
| Duplicate references rejected | 500 / 500 |

The canonical model view used 52.26% fewer serialized characters than the raw
state and instruction (2,886,213 versus 6,045,938). On this host, median
canonicalization time was 3.51 ms and median validation time was 0.037 ms. These
CPU timings describe this synthetic Python workload and are not deployment
service-level objectives.

The processed result is
`results/processed/stage9_system_eval.json` (SHA-256
`21ef9484a2dbcadf52c186dbfbdf0d950af93576fec8deaf78a19660a4d3abf4`).

## The critical semantic boundary

All 500 deliberately wrong existing-account handles passed structural
validation and rehydrated to the wrong account. This is expected and important:

```text
unknown or malformed handle  → deterministic validator can reject
known but semantically wrong handle → requires task verification or human review
```

For high-impact actions, a valid handle should trigger an additional verifier:
a deterministic business rule, database constraint, second model, user
confirmation, or human approval depending on risk. Grammar and registry checks
must never be reported as factual correctness.

## When aliasing helps

Use canonical handles when:

- the literal value is a transport key, database ID, UUID, URL, tool-call ID,
  transaction ID, email address, or account number whose spelling is irrelevant;
- values repeat across a long context or must be reproduced exactly;
- the model must bind facts to objects, select sources, or propose tool targets;
- raw values are privacy-sensitive and are unnecessary for the reasoning task;
- deterministic software can retain a request-scoped reversible mapping.

## When not to alias

Keep or selectively expose literals when:

- their characters carry meaning needed by the task, such as classifying an
  email domain, comparing URL paths, validating a checksum, editing code, or
  quoting source text;
- the model must reason about spelling, morphology, formatting, or substrings;
- an alias would erase a distinction the model needs;
- no trustworthy entity/object detector or lifecycle-managed mapping store is
  available;
- model/task evaluation shows no benefit and the added systems state is not
  justified.

A mixed representation is often correct: preserve semantically relevant fields
and alias only transport identity. Do not place both a raw UUID and its alias in
the prompt by default; Stage 4 showed that dual labels are not equivalent to
removing the raw identifier.

## Failure modes and trade-offs

- **Wrong existing binding:** structurally valid and invisible to registry-only validation.
- **Incomplete detection:** an unmasked occurrence can expose raw data. The reference canonicalizer fails closed when a configured value remains, including a case variant.
- **Ambiguous typing:** one raw value assigned multiple types is rejected rather than guessed.
- **Stale maps:** expired objects or changed authorization can make a once-valid handle unsafe.
- **Cross-request confusion:** mappings must be request-scoped; the reference rehydrator checks registry identity.
- **Prompt injection in data:** canonicalization does not make retrieved content trustworthy.
- **Vault compromise:** the reversible map is sensitive data and needs encryption, access control, retention limits, and log redaction.
- **Lost semantic cues:** replacing meaningful literals can reduce accuracy.
- **Operational complexity:** mapping lifecycle, observability, retries, cache behavior, and debugging become application responsibilities.
- **Architecture dependence:** compact or typed syntax is not uniformly best across models.

## Privacy implications

Canonicalization reduces model exposure; it does not anonymize the workflow.
Handles may remain linkable inside a request, surrounding facts may re-identify
people, model providers still observe the canonicalized context, and the vault
can reconstruct every value. Production deployments should minimize fields,
encrypt and isolate the vault, bind it to tenant/request identity, set short
retention, redact traces, and apply the same data-governance controls used for
the original records.

## Recommendations

### RAG systems

1. Give the model short request-local source handles, not storage UUIDs or full URLs.
2. Keep retriever/document IDs in the mapping vault and validate every returned source handle.
3. Score source selection separately from formatting and answer accuracy.
4. Rehydrate citations only after validation; escape and render them as data.
5. Preserve literal text when the question genuinely depends on its surface form.

### Agent and tool systems

1. Represent customers, transactions, URLs, calls, and tool outputs with typed handles.
2. Use strict structured output and reject extra fields, unregistered handles, type confusion, and unauthorized action schemas.
3. Treat handles as references—not bearer tokens, permissions, or proof of correctness.
4. Re-check authorization, object freshness, amount/range constraints, and idempotency after rehydration and before execution.
5. Require confirmation or an independent verifier for consequential actions and wrong-target risk.
6. Never expose tool secrets, credentials, or the reversible mapping to the model.

## Reproduction

```bash
.venv/bin/python experiments/09_system_ir.py \
  --requests 500 --records-per-request 20
.venv/bin/python scripts/run_tests.py
```

The current suite contains 43 tests, including fail-closed canonicalization,
adversarial validation, exact round trips, redacted auditing, and cross-request
rehydration refusal.
