"""Deterministic multi-source reasoning tasks for the Stage 5 budget study."""

from __future__ import annotations

from collections.abc import Callable

from symbolic_ir.randomness import rng_for
from symbolic_ir.schema import CanonicalExample, Source

TASK_TYPES = ("arithmetic", "temporal", "constraint", "entity_resolution")
_FILLER_SENTENCES = (
    "The archived record was independently reviewed during the routine quarterly audit.",
    "Its formatting, storage location, access classification, and retention schedule are administrative details.",
    "This administrative note does not alter any value, date, identity, relationship, or constraint in the factual sentence.",
    "Readers should use the explicit factual sentence when solving the question and treat this note as neutral context.",
)


def _pad(text: str, rng, filler_words: int) -> str:
    if filler_words <= 0:
        return text
    payload: list[str] = []
    while len(payload) < filler_words:
        payload.extend(rng.choice(_FILLER_SENTENCES).split())
    return f"{text} {' '.join(payload[:filler_words])}"


def _distractors(rng, count: int) -> list[Source]:
    return [
        Source(
            f"distractor-{index}",
            f"An unrelated registry entry reports reference value {rng.randrange(100, 9999)} "
            f"for department {chr(65 + index % 20)} in cycle {rng.randrange(1, 40)}.",
        )
        for index in range(count)
    ]


def _arithmetic(rng) -> tuple[list[Source], str, str, int]:
    units, price = rng.randrange(24, 90), rng.randrange(8, 48)
    returned = rng.randrange(2, min(16, units))
    refund_pct = rng.choice((50, 60, 75, 80, 90, 100))
    facts = [
        Source("units", f"Company A bought {units} units from Company B."),
        Source("price", f"Company B charged {price} credits per unit."),
        Source("return-policy", f"Company A returned {returned} units, each refunded at {refund_pct}% of its original unit purchase price."),
    ]
    expenditure = units * price - returned * price * refund_pct / 100
    answer = str(int(expenditure)) if expenditure.is_integer() else f"{expenditure:.2f}"
    return facts, "What is Company A's net expenditure in credits after the refund?", answer, 3


def _temporal(rng) -> tuple[list[Source], str, str, int]:
    anchor = rng.randrange(3, 12)
    offsets = [rng.randrange(2, 7), rng.randrange(1, 5)]
    facts = [
        Source("anchor", f"The intake meeting occurred on day {anchor} of the project."),
        Source("review", f"The design review occurred {offsets[0]} days after the intake meeting."),
        Source("delivery", f"The final delivery occurred {offsets[1]} days after the design review."),
    ]
    question = "On which project day did the final delivery occur? Answer with the day number."
    return facts, question, str(anchor + sum(offsets)), 3


def _constraint(rng) -> tuple[list[Source], str, str, int]:
    names = rng.sample(("Asha", "Bela", "Chen", "Dario", "Eleni", "Farah"), 3)
    start = rng.randrange(1, 4)
    facts = [Source("seat-anchor", f"{names[0]} occupies seat {start}.")]
    facts.extend(
        Source(f"seat-link-{index}", f"{names[index]} sits immediately to the right of {names[index - 1]}.")
        for index in range(1, 3)
    )
    question = f"Which numbered seat does {names[2]} occupy? Answer with the seat number."
    return facts, question, str(start + 2), 3


def _entity_resolution(rng) -> tuple[list[Source], str, str, int]:
    person = rng.choice(("Mira", "Noor", "Owen", "Priya", "Ravi"))
    alias = rng.choice(("Kestrel", "Lynx", "Orchid", "Quartz", "Vega")) + str(rng.randrange(10, 99))
    project = rng.choice(("Atlas", "Borealis", "Cygnus", "Draco", "Equinox")) + "-" + str(rng.randrange(10, 99))
    artifact = rng.choice(("amber", "cobalt", "ivory", "silver", "teal")) + "-" + str(rng.randrange(100, 999))
    facts = [
        Source("person-alias", f"Researcher {person} uses the registry alias {alias}."),
        Source("alias-project", f"Registry alias {alias} owns project {project}."),
        Source("project-artifact", f"Project {project} published artifact {artifact}."),
    ]
    question = f"What artifact was ultimately published by the project owned through {person}'s account chain?"
    return facts, question, artifact, 3


_BUILDERS: dict[str, Callable] = {
    "arithmetic": _arithmetic,
    "temporal": _temporal,
    "constraint": _constraint,
    "entity_resolution": _entity_resolution,
}


def generate_reasoning_examples(
    *, seed: int, count: int, num_sources: int = 8, task_type: str = "arithmetic",
    long_context: bool = False, filler_words: int = 130,
) -> list[CanonicalExample]:
    if task_type not in TASK_TYPES:
        raise ValueError(f"Unsupported reasoning task_type: {task_type}")
    examples: list[CanonicalExample] = []
    for number in range(count):
        rng = rng_for(seed, "reasoning", task_type, num_sources, number)
        facts, question, answer, reasoning_steps = _BUILDERS[task_type](rng)
        if num_sources < len(facts):
            raise ValueError(f"{task_type} reasoning examples require at least {len(facts)} sources")
        sources = facts + _distractors(rng, num_sources - len(facts))
        if long_context:
            sources = [Source(source.key, _pad(source.text, rng, filler_words)) for source in sources]
        rng.shuffle(sources)
        aliases = []
        if "." in answer:
            aliases.append(answer.rstrip("0").rstrip("."))
        examples.append(CanonicalExample(
            example_id=f"reasoning-{task_type}-n{num_sources}-{seed}-{number:05d}",
            seed=seed,
            task_type=f"reasoning_{task_type}", sources=tuple(sources), question=question,
            answer=answer, relevant_sources=tuple(source.key for source in facts),
            metadata={"generator": "reasoning-v2", "num_sources": num_sources,
                      "reasoning_steps": reasoning_steps, "long_context": long_context,
                      "filler_words": filler_words if long_context else 0,
                      "answer_aliases": aliases},
        ))
    return examples
