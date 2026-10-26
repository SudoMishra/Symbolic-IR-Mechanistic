"""Deterministic fictional citation and multi-hop reasoning datasets."""

from __future__ import annotations

from symbolic_ir.randomness import rng_for
from symbolic_ir.schema import CanonicalExample, Source


_PLACES = (
    "Avelon", "Brenwick", "Caelora", "Dunmere", "Erisport", "Faron", "Glimwick",
    "Hadrin", "Ilyra", "Jorvik", "Kestrel", "Lunaris", "Morhaven", "Nerith",
    "Orinth", "Pavora", "Quenby", "Rellin", "Soravel", "Tarnis", "Uldora",
    "Veymar", "Westrun", "Xandria", "Yarrow", "Zephra",
)
_CAPITALS = (
    "Narin", "Toval", "Elset", "Brinna", "Caldris", "Dovik", "Emberly", "Fenna",
    "Galen", "Hesta", "Iskar", "Juna", "Korin", "Liora", "Mavik", "Nessa",
    "Orren", "Pella", "Quill", "Rovan", "Sella", "Tarin", "Ulric", "Vanna",
)
_CURRENCIES = ("tal", "vex", "orin", "luma", "krel", "sorin", "dara", "penn")


def generate_citation_examples(
    *, seed: int, count: int, num_sources: int = 5, task_type: str = "single_hop",
) -> list[CanonicalExample]:
    if num_sources < 2:
        raise ValueError("num_sources must be at least 2")
    examples = []
    for example_number in range(count):
        rng = rng_for(seed, "citation", task_type, num_sources, example_number)
        places = rng.sample(_PLACES, min(num_sources, len(_PLACES)))
        while len(places) < num_sources:
            places.append(f"Region-{len(places) + 1}-{rng.randrange(10000)}")
        sources: list[Source] = []
        for i, place in enumerate(places):
            capital = _CAPITALS[(rng.randrange(len(_CAPITALS)) + i) % len(_CAPITALS)]
            population = rng.randrange(12, 950)
            currency = rng.choice(_CURRENCIES)
            sources.append(Source(
                key=f"source-{i + 1}",
                text=f"The fictional region {place} has capital {capital}, population {population} thousand, and uses the {currency}.",
                entity_key=place,
                attributes={"place": place, "capital": capital, "population": population, "currency": currency},
            ))

        if task_type == "single_hop":
            target = rng.randrange(num_sources)
            source = sources[target]
            question = f"What is the capital of {source.attributes['place']}?"
            answer = str(source.attributes["capital"])
            relevant = (source.key,)
            claims = (answer,)
        elif task_type == "multi_hop":
            first, second = rng.sample(range(num_sources), 2)
            left, right = sources[first], sources[second]
            total = int(left.attributes["population"]) + int(right.attributes["population"])
            question = f"What is the combined population, in thousands, of {left.attributes['place']} and {right.attributes['place']}?"
            answer = str(total)
            relevant = (left.key, right.key)
            claims = (f"{left.attributes['place']}: {left.attributes['population']}", f"{right.attributes['place']}: {right.attributes['population']}")
        elif task_type == "comparison":
            first, second = rng.sample(range(num_sources), 2)
            left, right = sources[first], sources[second]
            winner = left if int(left.attributes["population"]) > int(right.attributes["population"]) else right
            question = f"Which has the larger population: {left.attributes['place']} or {right.attributes['place']}?"
            answer = str(winner.attributes["place"])
            relevant = (left.key, right.key)
            claims = (answer,)
        else:
            raise ValueError(f"Unsupported citation task_type: {task_type}")

        order = list(range(num_sources))
        rng.shuffle(order)
        shuffled = tuple(sources[index] for index in order)
        examples.append(CanonicalExample(
            example_id=f"citation-{task_type}-n{num_sources}-{seed}-{example_number:05d}",
            seed=seed,
            task_type=task_type,
            sources=shuffled,
            question=question,
            answer=answer,
            relevant_sources=relevant,
            claims=claims,
            metadata={"generator": "citation-v1", "num_sources": num_sources},
        ))
    return examples

