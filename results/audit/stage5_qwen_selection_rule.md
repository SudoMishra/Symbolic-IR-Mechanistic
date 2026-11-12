# Stage 5 Qwen 2.5 Confirmatory 800-Record Subset Selection Rule

## Context
In the exploratory/scaling phase of Stage 5, Qwen 2.5 1.5B was evaluated on 80 semantic examples (1,600 total records across 5 reasoning budgets and 4 arms), whereas Tiny Aya Global and Gemma 4 E2B were evaluated on the registered 40 semantic examples (800 records).

## Selection Rule
To ensure matched, balanced comparisons across all six models in the confirmatory cohort:
1. Filter Qwen 2.5 1.5B records strictly to the 40 semantic example IDs (`reasoning-entity_resolution-n15-202606-00000` through `reasoning-entity_resolution-n15-202606-00039`).
2. These 40 IDs are identical to the examples evaluated by Tiny Aya Global and Gemma 4 E2B (and designated for Gemma 4 E4B, Qwen 3.5 2B, and Qwen 3.5 4B).
3. The resulting subset contains exactly 800 records (40 examples × 5 budgets [64, 128, 256, 512, 1024] × 4 arms [numeric, random_compact, uuid, uuid_no_reproduction]).
4. The remaining 40 examples (IDs 00040 to 00079) remain preserved in raw storage (`eb6fd92cabf9.jsonl`) but do not enter published confirmatory aggregates.
