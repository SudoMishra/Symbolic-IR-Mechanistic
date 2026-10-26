# LongProc 2K-output cross-model smoke findings

## Scope

This report covers **one matched example** (`tom_tracking_2k` source index 7)
from the public LongProc benchmark. It verifies the long-context data path,
decoding, persistence, and official trace evaluation across all four local GGUF
models. It is a feasibility smoke, not an estimate of benchmark accuracy.

All runs used temperature 0, an 8,192-token context, and a 2,048-token output
cap. The example has 41 reference trace steps. Token counts are model-specific;
the `input` column includes the backend's chat-template overhead.

| Model | Input tokens | Output tokens | Reference tokens | Output cap hit | Correct prefix | Strict | Final | CPU latency |
|---|---:|---:|---:|:---:|---:|---:|---:|---:|
| Qwen2.5 1.5B Q4_K_M | 2,541 | 2,048 | 1,870 | yes | 0/41 (0.0%) | 0 | 0 | 104.1 s |
| LFM2.5 1.2B Q4_K_M | 2,619 | 296 | 1,839 | no | 0/41 (0.0%) | 0 | 0 | 18.7 s |
| Gemma 4 E2B Q4_0 | 2,640 | 2,012 | 2,037 | no | 8/41 (19.5%) | 0 | 0 | 169.3 s |
| Gemma 4 E4B Q4_0 | 2,640 | 2,048 | 2,037 | yes | 8/41 (19.5%) | 0 | 0 | 290.3 s |

## What happened

- Qwen generated beyond the required 41 steps and was truncated mid-step at the
  cap. Its initial visibility state was wrong, so official prefix accuracy was 0.
- LFM stopped voluntarily after 296 tokens and emitted only 8 parseable trace
  lines. Its initial state was also wrong. This demonstrates that a 2,048-token
  budget does not guarantee the model will use it.
- Gemma E2B emitted all 41 trace steps and a final answer without hitting the
  cap. Its first discrepancy was step 8, where it mislabeled an object move as
  “coin location unchanged.” It then ended with the wrong belief location.
- Gemma E4B emitted all 41 trace steps but hit the cap immediately after the
  `Final Answer:` label. Its first discrepancy was also at step 8, but the state
  error differed from E2B's.

The two Gemma variants therefore showed better procedural-format adherence and
a longer correct prefix on this example, but one matched example cannot establish
a model ranking. Strict accuracy is deliberately unforgiving: one incorrect
state transition makes the entire trace non-exact.

## Full matrix

The checked-in cross-tokenizer subset contains 25 examples per model, or 100
generations total. Every reference is 1,024–2,048 tokens under all four model
tokenizers. Based only on the observed smoke latencies and assuming similar output
behavior, a serial CPU run is multi-hour; the append-only files are resumable.

```bash
for config in configs/longproc/*.yaml; do
  .venv/bin/python scripts/run_longproc.py --config "$config"
done
```

Do not treat the four smoke rows as the full experiment. The main comparison
should aggregate strict accuracy, mean prefix accuracy, final-answer accuracy,
completion length, cap-hit rate, and latency over all 25 matched examples.
