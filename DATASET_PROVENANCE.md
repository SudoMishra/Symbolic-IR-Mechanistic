# Dataset provenance

## Multi-hop benchmark: MuSiQue

Stages 2–4 use the official **MuSiQue-Answerable v1.0 development split**.
MuSiQue was selected because its questions are explicitly composed from two to
four single-hop questions and filtered to reduce shortcut solutions. Each record
contains 20 candidate paragraphs, paragraph-level supporting evidence, an
answer, answer aliases, and the gold decomposition. This lets the same example
measure answer quality, multi-hop depth, source selection, identifier binding,
and identifier reconstruction.

- Repository: <https://github.com/StonyBrookNLP/musique>
- Paper: <https://aclanthology.org/2022.tacl-1.31/>
- License: CC BY 4.0
- Official archive SHA-256: `98f839bf2fd5319f5c688aed77901a6d5c30b3b9f9f691ab9a8ecafb045ee0cd`
- Development JSONL SHA-256: `15fa63794d18a94ce12411aca6e2327e65b6e83b0b1490efab3f1962e48abf3b`

The checked-in manifest selects 100 examples (34 two-hop, 33 three-hop, and 33
four-hop) using seed `202602`. All selected examples have 20 paragraphs. At both
15 and 20 displayed sources, every rendered condition stays within 2,000–3,700
raw prompt tokens under all five real GGUF tokenizers. The manifest SHA-256 is
`de79604b6bfa0e81e1610f2660c40bb7e48b1af680696967a63060e17f9bb0ce`.

Fetch and verify the public split with:

```bash
.venv/bin/python scripts/fetch_musique.py
```

## Long-context generation benchmark: LongProc

## Selected benchmark

The long-generation experiment uses the public **LongProc Theory-of-Mind
Tracking 2K** split (`tom_tracking_2k`). It is a procedural state-tracking task:
the prompt describes agents, rooms, containers, and object movements, and the
model must emit the complete step-by-step belief-state trace plus a final answer.
This is preferable to open-ended summarization here because every reasoning step
has deterministic reference output and rule-based evaluation.

- Project: <https://princeton-pli.github.io/LongProc/>
- Repository: <https://github.com/princeton-pli/LongProc>
- License: Apache-2.0
- Pinned source revision: `673ec4c230876e941d674116d66d28783c186b15`
- Data SHA-256: `c7a03d3b71ad6b6a6eec45a7dc86cf911d8786541bce4884f4b6a4308bcf6e76`
- Prompt SHA-256: `1a15f592f722eea0e2e8622de960ea38ee4b594d09a58ecd91704f34db56908b`

The files are intentionally ignored by Git and are fetched reproducibly with:

```bash
.venv/bin/python scripts/fetch_longproc.py
```

The downloader pins the Git revision and rejects either file unless its SHA-256
matches the values above.

## Length-controlled subset

The complete split contains 200 examples. The checked-in selection manifest
contains the 25 examples satisfying both constraints under **all four real GGUF
tokenizers** used in this study:

- rendered prompt: 2,048–4,096 tokens;
- reference generation: 1,024–2,048 tokens.

| Model tokenizer | Prompt min / mean / max | Reference min / mean / max |
|---|---:|---:|
| Qwen2.5 1.5B | 2,449 / 2,524.2 / 2,566 | 1,803 / 1,891.3 / 2,035 |
| LFM2.5 1.2B | 2,582 / 2,635.2 / 2,694 | 1,839 / 1,942.0 / 2,043 |
| Gemma 4 E2B | 2,562 / 2,642.1 / 2,692 | 1,967 / 1,998.2 / 2,039 |
| Gemma 4 E4B | 2,562 / 2,642.1 / 2,692 | 1,967 / 1,998.2 / 2,039 |

Counts exclude the chat-template wrapper. The inference logs also retain the
backend-reported input and output token counts, so any wrapper overhead is visible.
Generation uses an 8,192-token context and a 2,048-token output cap. A model may
emit an end-of-sequence token before reaching the cap; the runner records this
rather than padding or forcing output.

## Evaluation

`src/symbolic_ir/evaluation/longproc.py` reproduces the official normalized
belief-trace evaluator:

- strict accuracy requires every trace line to match;
- partial accuracy is the correct prefix before the first wrong trace line;
- extraction and step counts diagnose malformed or truncated outputs.

The harness additionally reports normalized final-answer accuracy, actual token
usage, latency, and whether the 2,048-token cap was reached.
