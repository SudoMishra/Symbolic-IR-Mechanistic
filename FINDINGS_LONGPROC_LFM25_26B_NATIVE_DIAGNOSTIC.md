# LFM2.5-2.6B native LongProc diagnostic

## Question

Does the 4% final-answer score shown for LFM2.5-2.6B in Figure 5 reflect
LongProc capability, or an incompatibility between the checkpoint and the
evaluation harness?

## Artifact and runtime

- Checkpoint: `LiquidAI/LFM2.5-2.6B-GGUF`, Q4_K_M
- Revision: `e7caca5d835a3901a8e0d63e94009429bafafdfc`
- GGUF SHA-256: `02a8b7e17487d326e46d68ce0ba24211e1b80a14c4cd0597fa73c1cd697f52ed`
- Runtime: `llama-cpp-python==0.3.36`, full CUDA offload
- Native settings: temperature 0.1, top-k 50, top-p 1.0, min-p 0.0,
  repetition penalty 1.1
- Memory controls: 16,384-token context, flash attention, Q8_0 K/V cache
- Prompt: unchanged official LongProc ToM prompt with two demonstrations

The checkpoint has no supported switch for disabling reasoning. Native
generation starts a reasoning block and is expected to terminate it with
`</think>` before emitting the final response.

## Native full-prompt termination pilot

Five representative examples were run at a 2,048-token output cap (source
indices 25, 45, 60, 85, and 133).

| Metric | Result |
|---|---:|
| Hit output cap | 5 / 5 |
| Emitted `</think>` | 0 / 5 |
| Entered a valid final-response phase | 0 / 5 |
| Valid LongProc completions | 0 / 5 |

Example 45 was then extended without changing its prompt or sampler:

| Output cap | Hit cap | `</think>` emitted | Observation |
|---:|---:|---:|---|
| 2,048 | yes | no | Reasoning through the actual story; no final response |
| 8,192 | yes | no | Reached the correct state, then restarted trace construction |
| 12,288 | yes | no | Repeated derivation/trace construction; never exited reasoning |

At 12,288 tokens the model stated the correct endpoint inside its reasoning,
but this is not a valid LongProc completion because the checkpoint never closed
the reasoning block or emitted the requested final response.

## Capability control

To isolate endpoint state tracking from the long-trace output contract, both LFM
checkpoints received the same story and question without demonstrations and were
asked for only `Final Answer: <location>`.

| Checkpoint | Exact endpoint | Relaxed semantic endpoint |
|---|---:|---:|
| LFM2.5-1.2B-Instruct | 5 / 25 (20%) | 5 / 25 (20%) |
| LFM2.5-2.6B | 7 / 25 (28%) | 9 / 25 (36%) |

The relaxed score accepts answers such as `The key is in the nursery's rack`
when the reference is `the nursery's rack`. This control is diagnostic only; it
does not measure exact procedural-trace accuracy.

## Diagnosis

1. The original forced `</think>` intervention is invalid for this checkpoint.
   With the two demonstrations present, it caused first-demonstration copying in
   17 of 25 records and produced the 4% Figure 5 endpoint score.
2. Native generation removes demonstration copying but does not terminate on the
   LongProc prompt even with a 12,288-token output budget.
3. The concise control shows that LFM2.5-2.6B has non-zero endpoint-tracking
   capability and is not intrinsically worse than LFM2.5-1.2B on that control.
4. The unresolved failure is checkpoint-task compatibility: this pure-reasoning,
   agentic checkpoint does not satisfy LongProc's long exact-trace contract under
   its native inference interface.

## Figure 5 disposition

Do not use the current LFM2.5-2.6B bar as a model-scale comparison. The defensible
choices are to remove it from Figure 5 or label it as an unsupported forced-no-think
diagnostic. The native result should be reported separately as 100% reasoning
truncation in the termination pilot, not as a 4% capability estimate.

Raw diagnostic generations are stored in
`results/diagnostics/longproc_lfm25_26b_native/`.
