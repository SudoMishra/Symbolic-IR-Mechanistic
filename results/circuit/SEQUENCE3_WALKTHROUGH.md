# Sequence 3 Reproducibility Walkthrough: Causal Circuit Decomposition & Subspace Localization

## 1. Executive Summary & Terminal Scientific Outcome
- **Terminal Scientific Outcome**: `validated_partial_mechanism`
- **Model**: Qwen 2.5 1.5B Instruct (`Qwen/Qwen2.5-1.5B-Instruct`)
- **Key Findings**:
  1. **Sequence 2R (Semantic Repair & Positive Controls)**: Correcting the distinguishing-token logit position to $d-1$ revealed that the late whole attention mixer at Layer 24 `pos_citation` has a statistical null causal effect on distinguishing citation targets (pooled shift $+0.001$ $[-0.147, +0.179]$). Instead, the residual stream carries a massive handle-identity representation at `pos_source_label` ($+2.125$ $[1.733, 2.552]$) and a statistically significant binding effect at Layer 14 `pos_post_evidence` ($+0.042$ $[0.018, 0.064]$ under label swap; $+0.209$ $[0.140, 0.273]$ under content swap).
  2. **Sequence 3A (Query Attention Head Circuit)**: Terminated as a **preregistered scientific null**. Because no whole attention mixer at citation positions met the positive-control eligibility criteria (nonzero shift with 95% CI not spanning zero), head-level screening was disabled per protocol without post-hoc search across unpreregistered layers.
  3. **Sequence 3B (Post-Evidence Causal Subspace)**: An orthonormal difference basis fitted on discovery post-evidence residual vectors confirmed a statistically significant positive causal shift on the held-out confirmation cohort ($N=80$ examples, 240 cases) at Rank 8 ($+0.0297$ $[0.0165, 0.0423]$) and Rank 16 ($+0.0321$ $[0.0174, 0.0456]$). The subspace exhibits clear cross-format dissociation: active on structured citations (up to 34.2% recovery), but near zero on compact/UUID formats.
  4. **Phase 6 (Behavioral Bridge)**: Under free generation, post-evidence subspace intervention (Layer 14 Rank 8) preserved exact factual answer accuracy at 40.6% [26.0%, 57.3%] (matching clean baseline 40.6%) while producing selective dissociation (8.3% [2.1%, 16.7%]).

---

## 2. Provenance & Dataset Integrity
- **Baseline Commit**: `e3f4bc652c8ac0c224f7bd973f1e3742811da2ba`
- **Python / PyTorch Environment**: Python 3.11.14, PyTorch 2.14.1+cu130, CUDA 13.0, NVIDIA GeForce RTX 4060 Laptop GPU (8,188 MiB).
- **Split Provenance & Manifest Hashes** (`data/circuit/dataset_manifest.json`):
  - `discovery_n32.jsonl`: `9112c31c27c653457e937d577ca226d9c661ef5dd4cf19cb07aa568e401c1072` (96 cases, 32 unique examples)
  - `validation_n32.jsonl`: `36435991721fa40ca7cfc2323c6f1d24a0d84b2e67df146d92ec06bf18fb2587` (96 cases, 32 unique examples)
  - `confirmation_n80.jsonl`: `3f5c66fa16dbbca0ee9dcf5c643956488a09f3ea7e2083907720970a2fe8be26` (240 cases, 80 unique examples)
  - `circuit_preregistration.json` (historical): `12363b12ad0d17088b9a2b535d8a87799e52579069d2d8fc77ae0c8681729b43`
  - `sequence3_preregistration.json` (new): `23f532fed2d7c88a868a124f6259ce2f5c9a50ca2cea31e70e4254298bc178fd`
- **Data Air-Gap**: Confirmation cohort was untouched until validation froze and pre-confirmation test/provenance checks completed.

---

## 3. Reproduction Commands

### Step 1: Run Full Test Suite
```bash
.venv/bin/pytest tests/
# Output: 104 passed in 4.21s
```

### Step 2: Phase 2 Sequence 2R Repaired Discovery Run & Synthesis
```bash
.venv/bin/python scripts/run_computation_vs_transport.py \
  --config configs/circuit/circuit_qwen25_15b.yaml \
  --dataset data/circuit/discovery_n32.jsonl \
  --output results/circuit/sequence3_work/qwen25_computation_vs_transport_discovery_n32_repaired.jsonl \
  --layers 14 20 24

.venv/bin/python scripts/analyze_computation_vs_transport.py \
  --input results/circuit/sequence3_work/qwen25_computation_vs_transport_discovery_n32_repaired.jsonl \
  --output-json results/circuit/sequence3_work/qwen25_computation_vs_transport_discovery_n32_synthesis_repaired.json \
  --output-md results/circuit/sequence3_work/FINDINGS_QWEN25_COMPUTATION_VS_TRANSPORT_REPAIRED.md
```

### Step 3: Phase 5 SVD Difference Basis Fitting (Discovery Only)
```bash
.venv/bin/python scripts/run_causal_subspace.py \
  --mode fit \
  --config configs/circuit/circuit_qwen25_15b.yaml \
  --discovery_dataset data/circuit/discovery_n32.jsonl \
  --basis_artifact results/circuit/sequence3_work/qwen25_subspace_basis_l14_post_evidence.pt \
  --layer 14 \
  --pos pos_post_evidence
```

### Step 4: Phase 5 Subspace Validation Evaluation & Analysis
```bash
.venv/bin/python scripts/run_causal_subspace.py \
  --mode eval \
  --config configs/circuit/circuit_qwen25_15b.yaml \
  --eval_dataset data/circuit/validation_n32.jsonl \
  --basis_artifact results/circuit/sequence3_work/qwen25_subspace_basis_l14_post_evidence.pt \
  --output results/circuit/sequence3_work/qwen25_subspace_validation_n32_eval.jsonl \
  --layer 14 \
  --pos pos_post_evidence \
  --ranks 1 2 4 8 16 32

.venv/bin/python scripts/analyze_causal_subspace.py \
  --input results/circuit/sequence3_work/qwen25_subspace_validation_n32_eval.jsonl \
  --output-json results/circuit/sequence3_work/qwen25_subspace_validation_synthesis.json \
  --output-md results/circuit/sequence3_work/FINDINGS_QWEN25_CAUSAL_SUBSPACE_VALIDATION.md
```

### Step 5: Phase 6 Behavioral Bridge Free Generation & Analysis
```bash
.venv/bin/python scripts/run_behavioral_bridge.py \
  --config configs/circuit/circuit_qwen25_15b.yaml \
  --dataset data/circuit/validation_n32.jsonl \
  --basis_path results/circuit/sequence3_work/qwen25_subspace_basis_l14_post_evidence.pt \
  --subspace_layer 14 \
  --subspace_rank 8 \
  --output results/circuit/sequence3_work/qwen25_behavioral_bridge_validation.jsonl

.venv/bin/python scripts/analyze_behavioral_bridge.py \
  --input results/circuit/sequence3_work/qwen25_behavioral_bridge_validation.jsonl \
  --output-json results/circuit/sequence3_work/qwen25_behavioral_bridge_synthesis.json \
  --output-md results/circuit/sequence3_work/FINDINGS_QWEN25_BEHAVIORAL_BRIDGE.md
```

### Step 6: Phase 7 Held-Out Confirmation Evaluation & Analysis
```bash
.venv/bin/python scripts/run_causal_subspace.py \
  --mode eval \
  --config configs/circuit/circuit_qwen25_15b.yaml \
  --eval_dataset data/circuit/confirmation_n80.jsonl \
  --basis_artifact results/circuit/sequence3_work/qwen25_subspace_basis_l14_post_evidence.pt \
  --output results/circuit/sequence3_work/qwen25_subspace_confirmation_n80_eval.jsonl \
  --layer 14 \
  --pos pos_post_evidence \
  --ranks 1 4 8 16 32

.venv/bin/python scripts/analyze_causal_subspace.py \
  --input results/circuit/sequence3_work/qwen25_subspace_confirmation_n80_eval.jsonl \
  --output-json results/circuit/sequence3_work/qwen25_subspace_confirmation_synthesis.json \
  --output-md results/circuit/sequence3_work/FINDINGS_QWEN25_CAUSAL_SUBSPACE_CONFIRMATION.md
```

---

## 4. Key Quantitative Results

### Phase 2: Sequence 2R Repaired Causal Shifts (Discovery Split, N=96)
All intervals report paired cluster-bootstrap 95% CIs ($B=1,000$, clustered by `example_id`):

| Layer | Semantic Position | Mixer Shift [95% CI] | MLP Shift [95% CI] | Residual Stream Shift [95% CI] |
|---|---|---|---|---|
| **L14** | `pos_source_label` | $-0.077$ $[-0.122, -0.027]$ | $-0.015$ $[-0.077, +0.050]$ | **$+2.125$ $[1.733, 2.552]$** |
| **L14** | `pos_evidence` | $+0.143$ $[0.086, 0.207]$ | $-0.011$ $[-0.041, +0.016]$ | **$+0.155$ $[0.089, 0.229]$** |
| **L14** | `pos_post_evidence` | $+0.035$ $[0.013, 0.055]$ | $+0.001$ $[-0.018, +0.022]$ | **$+0.042$ $[0.018, 0.064]$** |
| **L14** | `pos_citation` | $-0.004$ $[-0.024, +0.016]$ | $-0.001$ $[-0.022, +0.023]$ | $-0.039$ $[-0.064, -0.013]$ |
| **L20** | `pos_source_label` | $-0.032$ $[-0.068, -0.000]$ | $-0.048$ $[-0.134, +0.035]$ | **$+2.146$ $[1.745, 2.571]$** |
| **L20** | `pos_citation` | $-0.034$ $[-0.114, +0.057]$ | $+0.075$ $[-0.005, +0.169]$ | $+0.007$ $[-0.220, +0.223]$ |
| **L24** | `pos_source_label` | $-0.004$ $[-0.016, +0.009]$ | $+0.002$ $[-0.038, +0.038]$ | **$+1.318$ $[1.076, 1.591]$** |
| **L24** | `pos_post_evidence` | $+0.015$ $[0.003, 0.026]$ | $+0.003$ $[-0.008, +0.014]$ | $+0.014$ $[0.002, 0.027]$ |
| **L24** | `pos_citation` | $+0.001$ $[-0.147, +0.179]$ | $-0.102$ $[-0.175, -0.023]$ | $-0.446$ $[-0.793, -0.073]$ |

### Phase 7: Held-Out Confirmation Subspace Causal Shifts (N=80, 240 cases)

| Subspace Rank $k$ | Causal Shift [95% CI] | Retained Variance | Structured Recovery | Compact Recovery | UUID Recovery |
|---|---|---|---|---|---|
| **$k=1$** | $+0.0103$ $[-0.0021, +0.0231]$ | 17.7% | 6.2% | 6.9% | 0.3% |
| **$k=4$** | **$+0.0131$ $[0.0003, 0.0267]$** | 44.9% | 8.6% | $-5.0\%$ | $-0.8\%$ |
| **$k=8$** | **$+0.0297$ $[0.0165, 0.0423]$** | 62.3% | 12.7% | 1.7% | $-3.1\%$ |
| **$k=16$** | **$+0.0321$ $[0.0174, 0.0456]$** | 76.4% | 12.0% | 9.8% | $-2.5\%$ |
| **$k=32$** | **$+0.0289$ $[0.0126, 0.0444]$** | 88.0% | 10.8% | 2.3% | $-3.5\%$ |

---

## 5. Scientific Limitations & Boundaries
1. **No Single Compact Routing Head Circuit**: Late query-attention mixers at citation prediction positions do not show head-level causal dominance on distinguishing tokens. Handle identity is linearly propagated via the residual stream rather than routed dynamically through a single late mixer head.
2. **Format Sensitivity of Linear Subspace**: While a rank-8 linear subspace captures statistically significant causal shifts in structured identifiers ($[S1]$), it fails to transfer linearly to compact ($[7XD1]$) or UUID identifiers, demonstrating that evidence-handle binding representations depend on identifier morphology.
3. **Behavioral Transfer**: While post-evidence subspace intervention preserves factual answer correctness under free generation (40.6% EM), it redirects citation output in 8.3% of cases, demonstrating a partial causal bridge between internal representation and generated surface text.
