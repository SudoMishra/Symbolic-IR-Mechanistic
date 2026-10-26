"""Synthetic-only entity canonicalization benchmark."""

from __future__ import annotations

from symbolic_ir.randomness import rng_for
from symbolic_ir.schema import CanonicalExample, Source


_FIRST = ("Amina", "Bela", "Chen", "Dario", "Elena", "Farah", "Gita", "Hugo", "Imani", "Jonas")
_LAST = ("Arden", "Basu", "Costa", "Diaz", "Evans", "Fischer", "Gupta", "Hale", "Ibrahim", "Jensen")
_FILLER_SENTENCES = (
    "The record was reviewed during the routine quarterly compliance audit.",
    "Its storage tier and retention schedule are administrative metadata only.",
    "This note does not alter the customer identity, contact route, account, or balance.",
    "Use the explicit customer fields when resolving the request.",
)


def _pad(text: str, rng, filler_words: int) -> str:
    if filler_words <= 0:
        return text
    payload: list[str] = []
    while len(payload) < filler_words:
        payload.extend(rng.choice(_FILLER_SENTENCES).split())
    return f"{text} {' '.join(payload[:filler_words])}"


def generate_pii_examples(
    *, seed: int, count: int, num_sources: int = 8,
    task_type: str = "account_resolution", long_context: bool = False,
    filler_words: int = 0,
) -> list[CanonicalExample]:
    if task_type != "account_resolution":
        raise ValueError(f"Unsupported PII task_type: {task_type}")
    if num_sources < 3:
        raise ValueError("PII examples require at least three sources")
    examples = []
    for number in range(count):
        rng = rng_for(seed, "pii", task_type, num_sources, number)
        people = []
        sources: list[Source] = []
        for i in range(num_sources):
            name = f"{rng.choice(_FIRST)} {rng.choice(_LAST)}-{100 + i}"
            email = f"customer.{rng.randrange(10000, 99999)}@example.test"
            account = f"ACC-{rng.randrange(10**11, 10**12 - 1)}"
            balance = rng.randrange(100, 9000)
            people.append((name, email, account, balance))
            text = f"Customer {name}, reached at {email}, owns account {account} with balance {balance} credits."
            sources.append(Source(
                key=f"person-{i + 1}",
                text=_pad(text, rng, filler_words) if long_context else text,
                entity_key=f"person-{i + 1}",
                attributes={"entity_type": "PERSON", "name": name, "email": email, "account": account, "balance": balance},
            ))
        target = rng.randrange(num_sources)
        name, email, account, balance = people[target]
        rng.shuffle(sources)
        examples.append(CanonicalExample(
            example_id=f"pii-{task_type}-n{num_sources}-{seed}-{number:05d}",
            seed=seed,
            task_type=f"pii_{task_type}",
            sources=tuple(sources),
            question=f"Which account belongs to the customer whose contact email is {email}?",
            answer=account,
            relevant_sources=(f"person-{target + 1}",),
            entities={f"person-{i + 1}": {"name": p[0], "email": p[1], "account": p[2]} for i, p in enumerate(people)},
            metadata={"generator": "pii-v2", "synthetic_only": True, "target_email": email,
                      "long_context": long_context,
                      "filler_words": filler_words if long_context else 0},
        ))
    return examples
