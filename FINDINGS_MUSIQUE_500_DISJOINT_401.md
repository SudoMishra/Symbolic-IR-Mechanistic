# MuSiQue Sensitivity Analysis: 401 Genuinely Disjoint Examples

**Design:** 12832 deterministic GPU generations across 8 models restricted to the 401 examples strictly disjoint from earlier 100-item cohorts (excluding 51 items from initial balanced-100 and 48 from heldout-100).

| Model | Sources | Numeric binding | UUID binding | UUID−numeric binding (95% CI) | Numeric answer F1 | UUID answer F1 |
|---|---:|---:|---:|---:|---:|---:|
| tiny-aya-global-GGUF:q4_k_m | 15 | 43.5% | 30.2% | **-13.32 pp** [-16.19, -10.49] | 26.3% | 34.4% |
| tiny-aya-global-GGUF:q4_k_m | 20 | 40.9% | 24.2% | **-16.69 pp** [-19.62, -13.80] | 26.5% | 29.9% |
| LFM2.5-1.2B-Instruct-GGUF:q4_k_m | 15 | 23.1% | 18.7% | **-4.34 pp** [-7.17, -1.50] | 9.2% | 8.7% |
| LFM2.5-1.2B-Instruct-GGUF:q4_k_m | 20 | 17.4% | 9.9% | **-7.48 pp** [-9.95, -5.05] | 8.0% | 6.0% |
| LFM2.5-2.6B-GGUF:q4_k_m | 15 | 25.7% | 18.5% | **-7.15 pp** [-9.93, -4.26] | 27.8% | 27.1% |
| LFM2.5-2.6B-GGUF:q4_k_m | 20 | 24.2% | 14.2% | **-9.93 pp** [-12.97, -6.88] | 25.0% | 21.5% |
| Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 15 | 21.2% | 15.7% | **-5.51 pp** [-8.31, -2.66] | 19.2% | 19.3% |
| Qwen2.5-1.5B-Instruct-GGUF:q4_k_m | 20 | 17.7% | 9.2% | **-8.52 pp** [-11.26, -5.82] | 18.4% | 20.5% |
| gemma-4-E2B-it-qat-q4_0-gguf | 15 | 47.2% | 43.1% | **-4.16 pp** [-6.65, -1.72] | 16.7% | 16.6% |
| gemma-4-E2B-it-qat-q4_0-gguf | 20 | 46.6% | 41.4% | **-5.20 pp** [-7.67, -2.76] | 14.8% | 15.5% |
| gemma-4-E4B-it-qat-q4_0-gguf | 15 | 47.9% | 42.0% | **-5.84 pp** [-8.56, -3.24] | 24.9% | 24.4% |
| gemma-4-E4B-it-qat-q4_0-gguf | 20 | 44.6% | 37.4% | **-7.15 pp** [-9.77, -4.61] | 24.7% | 21.8% |
| Qwen3.5-2B-GGUF:q4_k_m | 15 | 37.6% | 30.6% | **-6.98 pp** [-9.68, -4.36] | 30.7% | 30.8% |
| Qwen3.5-2B-GGUF:q4_k_m | 20 | 34.1% | 29.3% | **-4.72 pp** [-7.32, -2.08] | 30.0% | 28.8% |
| Qwen3.5-4B-GGUF:q4_k_m | 15 | 62.2% | 59.5% | **-2.72 pp** [-5.17, -0.39] | 43.3% | 40.7% |
| Qwen3.5-4B-GGUF:q4_k_m | 20 | 59.5% | 57.6% | **-1.83 pp** [-4.18, +0.52] | 41.3% | 40.3% |
