# LongProc 2K-output GPU findings

## Experiment

The complete cross-tokenizer subset contains 25 matched public LongProc
`tom_tracking_2k` examples per model: **100 GPU generations total**. Every prompt
is 2,048–4,096 model tokens and every reference trace is 1,024–2,048 tokens under
all four tested tokenizers. Decoding used temperature 0, an 8,192-token context,
and a 2,048-token output cap.

Strict accuracy requires every belief-state trace line to match. Partial accuracy
is the fraction of the reference trace preceding the first error. Confidence
intervals are Wilson intervals for proportions and paired-example bootstrap
intervals for mean partial accuracy.

## Results

| Model | Strict trace | Mean prefix accuracy (95% CI) | Final answer | Full trace emitted | Mean output | Cap hit | Mean latency | Throughput |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen2.5 1.5B Q4_K_M | 0/25 (0%) | 1.2% (0.5–2.0%) | 1/25 (4%) | 96% | 2,027 | 84% | 16.7 s | 121.2 tok/s |
| LFM2.5 1.2B Q4_K_M | 0/25 (0%) | 0.9% (0.4–1.5%) | 7/25 (28%) | 0% | 434 | 0% | 2.4 s | 182.5 tok/s |
| Gemma 4 E2B Q4_0 | 0/25 (0%) | 9.4% (4.8–15.8%) | 4/25 (16%) | 80% | 1,987 | 24% | 31.1 s | 63.9 tok/s |
| **Gemma 4 E4B Q4_0** | **2/25 (8%)** | **38.0% (26.9–50.2%)** | **19/25 (76%)** | **96%** | 1,996 | 0% | 41.5 s | 48.1 tok/s |

Gemma E4B's strict-accuracy 95% Wilson interval is 2.2–25.0%, and its final-answer
interval is 56.6–88.5%. The sample is adequate for a strong directional result,
but still too small for a precise absolute benchmark estimate.

## Main findings

1. **Gemma E4B is decisively strongest on this procedural long-output task.** Its
   mean correct prefix exceeds Gemma E2B by 28.7 percentage points (paired
   bootstrap 95% CI: 17.1–41.3 points). Its final-answer accuracy exceeds E2B by
   60 points (paired 95% CI: 40–80 points).
2. **Final-answer accuracy hides trace failures.** E4B gets 76% of final answers
   right but only 8% of complete traces exactly right. The gap directly supports
   evaluating intermediate state transitions rather than relying on endpoints.
3. **Qwen uses the full budget without tracking the state correctly.** It hits
   the 2,048-token cap on 84% of examples and usually emits at least as many trace
   lines as requested, yet has only 1.2% mean correct-prefix accuracy.
4. **LFM is fast because it does not perform the requested long generation.** It
   emits only 250–970 tokens (mean 434), never produces a complete trace, and has
   0.9% mean correct-prefix accuracy. Its 28% final-answer rate should not be read
   as successful procedural reasoning.
5. **Gemma E2B generally follows the format but loses state early.** It emits a
   full-length trace on 80% of examples, while mean correct-prefix accuracy is
   only 9.4% and no trace is completely correct.

## Runtime

Summed generation latency across the 100 records was 2,293.6 seconds (38.2
minutes), excluding model-loading and analysis overhead. The RTX 4060 accelerated
the matched smoke example by 5.3×–10.5× depending on model. See
`GPU_PROVENANCE.md` for the exact driver, toolkit, build, and offload settings.

The raw results are append-only JSONL files under:

```text
results/raw/longproc_tom_tracking_2k_qwen25_15b/d9aa86a5f1bb.jsonl
results/raw/longproc_tom_tracking_2k_lfm25_12b/0b5d0c4e89da.jsonl
results/raw/longproc_tom_tracking_2k_gemma4_e2b/8f3ca43ed227.jsonl
results/raw/longproc_tom_tracking_2k_gemma4_e4b/0c1e6973c57c.jsonl
```
