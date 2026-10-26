# GPU execution provenance

The full LongProc experiment and the MuSiQue Stage 2–4 experiments ran on one NVIDIA GeForce RTX 4060 Laptop GPU.

- GPU memory: 8,188 MiB reported by `nvidia-smi` (7,805 MiB visible to llama.cpp)
- NVIDIA driver: 580.126.20
- CUDA toolkit: 12.9.86
- Compute capability: 8.9 (`sm_89`)
- `llama-cpp-python`: 0.3.36
- llama.cpp build flags: `GGML_CUDA=ON`, `CMAKE_CUDA_ARCHITECTURES=89`
- Model offload: all layers (`n_gpu_layers: -1`)
- K/Q/V offload: enabled
- Context: 8,192 tokens
- Decoding: temperature 0; maximum 2,048 output tokens for LongProc and 256 for MuSiQue short-answer citation QA

Models were run sequentially so the 8 GB device never had to hold two models at
once. The MuSiQue run adds Tiny Aya Global to Qwen, LFM, and Gemma E2B/E4B.
Result metadata records the exact model revisions, configuration digests,
dataset revision, dataset hashes, and selected example IDs.

For the matched source-index-7 smoke example, recorded CPU-to-GPU latency changed
from 104.1 to 16.9 seconds for Qwen (6.2× speedup), 18.7 to 1.8 seconds for LFM
(10.5×), 169.3 to 31.9 seconds for Gemma E2B (5.3×), and 290.3 to 42.5 seconds
for Gemma E4B (6.8×). GPU floating-point execution changed deterministic-decoding
outputs for three models, so the full comparison uses GPU records exclusively.

## MuSiQue Stage 2–4 result integrity

The five completed files contain 1,500 unique request keys each (7,500 total).
Backend-reported input lengths span 2,056–3,777 tokens after chat-template
wrapping. Aggregate measured generation latency is 3.07 GPU-hours.

| Model | Raw JSONL SHA-256 |
|---|---|
| Qwen2.5 1.5B | `321b1128b7bcaefff2117768fba1481f62556a06ab41c4d03374912f755994c7` |
| LFM2.5 1.2B | `663f0f49c28c55cd73d5b047f592891f5c2232a47211a1b74ebb3f384c0b2991` |
| Gemma 4 E2B | `5d658650de6a915e421c7def94f5c10bd491a1323167938b6de3dc1207ecef7d` |
| Gemma 4 E4B | `ddbeb531485597e8a9347437fe80003000e9643579711a2a3e657b5594fe0ee2` |
| Tiny Aya Global | `4002cbf5255c540abb6d7e1474612073d00308c70d85273a22cb690af3ade153` |

The processed paired-analysis JSON SHA-256 is
`129a41ade4389ce89691a8e706724ba5f63ab78b7fa90208230779769f66ecd9`.

## Stage 6 hidden-state collection

Stage 6 used the same RTX 4060 Laptop GPU and official BF16 Transformers
checkpoints. Qwen and LFM fit directly on CUDA. Gemma used Accelerate CPU
offload and loaded only the exact text modules because the experiment contains
no image or audio inputs. All runs used `torch==2.14.1+cu130`,
`accelerate==1.15.0`, and `safetensors==0.8.0`; Qwen/LFM used
`transformers==4.57.6`, while Gemma 4 used `transformers==5.20.2`.

| Model | Passes | Prompt tokens min/mean/max | Completion pass | Peak CUDA MiB | Config digest |
|---|---:|---:|---:|---:|---|
| Qwen2.5 1.5B | 240 | 2,428 / 3,046.4 / 3,943 | 193.9 s | 3,524.8 | `e631b6fa4a16` |
| LFM2.5 1.2B | 240 | 2,564 / 3,137.6 / 3,885 | 151.7 s | 2,491.2 | `eeccba2608d3` |
| Gemma 4 E2B | 240 | 2,425 / 3,044.0 / 3,946 | 555.4 s | 7,236.9 | `ea2905fcb779` |
| Gemma 4 E4B | 240 | 2,425 / 3,044.0 / 3,946 | 1,050.5 s | 7,228.2 | `8973f6266084` |

Each directory contains 240 compressed arrays and 80 complete three-condition
blocks. Every recorded array hash was rechecked successfully.

| Model | Manifest SHA-256 | Metadata SHA-256 | Processed JSON SHA-256 |
|---|---|---|---|
| Qwen2.5 1.5B | `91f95be0f1a474308d9799c11da19ef098ab6b979c18b6d655a1ca9ecbc3a9a1` | `2643e3dd1430e8d354dd1562bed63a3e2296e5b92975925d48c8941ca6ae4738` | `0b03c3c53deda36ae5dcfdd2ffdddd6eba81f2d556f7809aa591c9321716f36f` |
| LFM2.5 1.2B | `772d31c23f8d89a0bc2eb62d4c3aebcde3cf36423051d2ccc48cde43bc358d96` | `b9c44d2b9bbde6c429add53f3ae27a54752aef9a0c477856af255493dc5ef2ba` | `1daa4cf96a0e8c387ba12facfc9e0b27a4a172afbcc9c01093cfe93756541763` |
| Gemma 4 E2B | `4a6569e544c1ddf2eb36e2a2a96b209ce17469ae6778a6ccb53b61d55fa8c8b1` | `03726f1d27c55f28b03a6163f4f6ce5cab4b513e06124e5cae80e333a3bc9558` | `8d88d86e037cc1b7068b12ea99790a092c4ebb3c826937bfa1d8dcd51ab19b37` |
| Gemma 4 E4B | `eabba7cdbfd0c8d36c8d5ab7156a9dc72c88c71092a2f2ba58a19fe382f5d77f` | `2bb41852317cd6145b387f355e3923a25bb518d7a5405bb12b238239b1b8624f` | `5082678d6e75cb122075b8125bcfc48f2b22ebffd595c8c64e9fcd5983a74a73` |

The memory-efficient hook collector was checked against Qwen's original full
hidden-state method on the same example. Maximum absolute error across all
stored span types was below `3e-8`.

## Stage 7 causal interventions

Stage 7 used the same official BF16 checkpoints with `torch==2.14.1+cu130` and
`transformers==5.20.2`. Qwen and LFM scored the old/new citation candidates as a
batch of two. Gemma used memory-safe single-candidate forwards with Accelerate
CPU offload. All prompts remained in the requested 2K–4K range. Qwen/LFM use
eight semantic examples; Gemma E2B uses four and E4B two because of offload cost.

| Model | Semantic examples | Paired swaps | Interventions | Prompt tokens min/max | Peak CUDA MiB | Config digest |
|---|---:|---:|---:|---:|---:|---|
| Qwen2.5 1.5B | 8 | 24 | 384 | 2,452 / 3,889 | 3,486.4 | `ed4f8ec474bc` |
| LFM2.5 1.2B | 8 | 24 | 384 | 2,588 / 3,850 | 2,758.1 | `69f32f38d3d4` |
| Gemma 4 E2B | 4 | 12 | 192 | 2,453 / 3,887 | 7,312.7 | `b0e9e07604a2` |
| Gemma 4 E4B | 2 | 6 | 96 | 2,453 / 2,932 | 7,209.5 | `2af614377c25` |

| Model | Manifest SHA-256 | Metadata SHA-256 | Processed JSON SHA-256 |
|---|---|---|---|
| Qwen2.5 1.5B | `09d138a9713aba640550e89d5941d56316365640c7fdceac6e1db6865974e5bc` | `bb54c4b184ec3ea857757d7d980fbe60a09c14afcf9f0efde2d5c08846695203` | `d74052dc576267e9450251bd123fe082e400cb8eb17efc8ab5cf15f4d1d4cee2` |
| LFM2.5 1.2B | `4bdccc8a5ae4c45100b98f6fa012a69c5fb0880672e14849bf8696515654336a` | `3d3bec285fee70f0f3e8f3f38b69e7c65c582b5de727c3d81ab4f5d8aebcde00` | `ee4235d8b472bd021d9b470ceef045ecf1139676cb55fb24980978d6b998ccf0` |
| Gemma 4 E2B | `d97ac52139db686d409c46c201c17669aa52590921bd18606383cc9a316589c4` | `d8b7bbcf1ed233eaa977728088f91f673c098ec772981743009eb0e5cb1645f3` | `9c7eef85f70f0db3c5ff28048b28cdbc4bdca3986824955cd25983b05a5807bc` |
| Gemma 4 E4B | `372db8701116faeacf4f09cc47507d1ea9f30fc47ebbf5f1ec21a1d032b4cdd2` | `cce80e6f24234b9cfdaf13cbcf0cf3a16730a7009f361e6f05f433b670902c52` | `731591d3256afb96c7053d53f85e9437a48e4d52c45e5dabeaeebc61c5694d55` |

## Stage 8 entity canonicalization

Stage 8 used the same CUDA llama.cpp environment and full GPU layer offload.
Each model completed 160 deterministic generations: 40 synthetic
account-resolution examples at 15 or 20 records, rendered under four entity
representations. The decoder cap was 64 tokens. Backend-reported prompts span
approximately 2.2K–3.5K native tokens. Fixed `[S1]` source identifiers and
no-citation answers isolate entity representation from source-label format.

| Model | Generations | Prompt tokens min/max | Config digest |
|---|---:|---:|---|
| Qwen2.5 1.5B | 160 | 2,337 / 3,435 | `02832ba6fcee` |
| LFM2.5 1.2B | 160 | 2,330 / 3,194 | `b1925dfd4dda` |
| Gemma 4 E2B | 160 | 2,334 / 3,472 | `91fb9e635f1d` |
| Gemma 4 E4B | 160 | 2,334 / 3,472 | `e2b46e3fd26e` |
| Tiny Aya Global | 160 | 2,602 / 3,461 | `ff28bcbdebfc` |

| Model | Raw JSONL SHA-256 | Metadata SHA-256 | Processed JSON SHA-256 |
|---|---|---|---|
| Qwen2.5 1.5B | `ab16e37b72f9dd0b4246c6257ee853ffc0cd2948c00383f469c6f75ae9a74b80` | `294fad511538ab7cb93b52c9d8953d1c9664e304f0991a11a4c7d46aedc0a839` | `fc89e606b9735d7fea161b6e637028dc5c62a86c06d444c2b2e8fd2cbb8d87b4` |
| LFM2.5 1.2B | `573978e18ec79cdfcf568df0b0b7f6e44fbebd723234218f9c116422935e7696` | `957a0d8885f87633799c07c6f74cd721f51aa02572df6219787a95b66c439781` | `54c46e7b8e9b7a2ccf71a088a60c1d3ffe35d06cbd9a5e04495272a6f2903b91` |
| Gemma 4 E2B | `4b45c4947dfd9e92357f4e29e6b6a191ca8a10de861e223f436cdd78755c50a3` | `ca4ad8fd12d7933de3fb071568f8632ec1119bcdc0f8fd6c9b50eeecc79cb610` | `e378ce350c6f12e83bf3e7a283343ffef6eb5a5b891d98f1d19cdad1ff099a16` |
| Gemma 4 E4B | `83387d2bb4ac83e0c69f66bfc8515c3b6555c1ba558a68060876686c81c0c51a` | `0ce378d6a188fdd3fc25701a6f7c6fd143429666cbf9f0e350f9ad6024f2253a` | `57fc17dd143998f95d3437a25b70d0abc607e6095fde3ecf94ed4b2a813ab2ab` |
| Tiny Aya Global | `9dfd05fbe84ac1006ff3bd0d70b9a34ab9136b98fc83bc5080b55601f4a8a614` | `c3442ba063fbb68673ea6a885c944cb53ea18d29da78a40375c3dbd35705f80b` | `904605cf424bad156aaa5f16d4e060827b54c83b0faaca0e625db06c160431e5` |

The cross-model report SHA-256 is
`492872907932bbe25f4eac6e51a0c583eddee1c0d1d0753445b9e65ae6a092d5`.
