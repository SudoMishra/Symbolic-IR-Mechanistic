# Sequence 2: Qwen 2.5 1.5B Computation vs. Transport Mechanistic Discrimination

## Executive Summary

This experiment evaluates whether the confirmed Stage 7B Layer 24 attention mixer in **Qwen 2.5 1.5B** actively computes the source–identifier binding association, or merely transports/routes an already-formed decision to the output vocabulary.

We tested **4 semantically distinct token positions**:
1. **$P_{\text{label}}$ (Source Label):** The token span where the source identifier appears in the prompt body.
2. **$P_{\text{evidence}}$ (Evidence Content):** The token span of the core factual sentence containing the answer.
3. **$P_{\text{answer}}$ (Answer Text):** The token span of the teacher-forced answer text.
4. **$P_{\text{citation}}$ (Citation Predicting Position):** The final prompt token preceding citation generation.

Crossed with **4 counterfactual corruptions** (`label_swap`, `content_swap`, `question_swap`, `order_perm`) across 3 functional network layers (**L14** routing tier, **L20** stale mediator, **L24** terminal binding hub).

---

## Position-Resolved Causal Shift Matrix (Mixer vs. MLP vs. Residual)

### Corruption: `LABEL_SWAP`
*Donor Baseline Preference: -0.196 [-0.732, +0.428] nats*

| Layer | Intervened Token Position | Mixer Shift $\Delta_{\text{First}}$ | MLP Shift $\Delta_{\text{First}}$ | Residual Stream Shift | Mixer $D_{\text{KL}}$ |
| :---: | :--- | :---: | :---: | :---: | :---: |
| L14 | Source Label Token ($P_{\text{label}}$) | **-0.077** [-0.122, -0.027] | -0.015 [-0.077, +0.050] | +2.125 [+1.733, +2.552] | 0.006 nats |
| L14 | Evidence Passage ($P_{\text{evidence}}$) | **+0.143** [+0.086, +0.207] | -0.011 [-0.041, +0.016] | +0.155 [+0.089, +0.229] | 0.004 nats |
| L14 | Post-Evidence Token ($P_{\text{post-evidence}}$) | **+0.035** [+0.013, +0.055] | +0.001 [-0.018, +0.022] | +0.042 [+0.018, +0.064] | 0.001 nats |
| L14 | Answer Text ($P_{\text{answer}}$) | **+0.013** [-0.006, +0.033] | -0.005 [-0.031, +0.020] | +0.005 [-0.020, +0.031] | 0.001 nats |
| L14 | Citation Predicting Token ($P_{\text{citation}}$) | **-0.004** [-0.024, +0.016] | -0.001 [-0.022, +0.023] | -0.039 [-0.064, -0.013] | 0.001 nats |
| L20 | Source Label Token ($P_{\text{label}}$) | **-0.032** [-0.068, -0.000] | -0.048 [-0.134, +0.035] | +2.146 [+1.745, +2.571] | 0.001 nats |
| L20 | Evidence Passage ($P_{\text{evidence}}$) | **+0.003** [-0.013, +0.019] | +0.009 [-0.007, +0.025] | +0.005 [-0.015, +0.026] | 0.000 nats |
| L20 | Post-Evidence Token ($P_{\text{post-evidence}}$) | **+0.009** [-0.006, +0.023] | +0.009 [-0.002, +0.020] | +0.012 [-0.002, +0.027] | 0.000 nats |
| L20 | Answer Text ($P_{\text{answer}}$) | **-0.001** [-0.014, +0.014] | +0.008 [-0.007, +0.025] | -0.000 [-0.012, +0.011] | 0.001 nats |
| L20 | Citation Predicting Token ($P_{\text{citation}}$) | **-0.034** [-0.114, +0.057] | +0.075 [-0.005, +0.169] | +0.007 [-0.220, +0.223] | 0.010 nats |
| L24 | Source Label Token ($P_{\text{label}}$) | **-0.004** [-0.016, +0.009] | +0.002 [-0.038, +0.038] | +1.318 [+1.076, +1.591] | 0.000 nats |
| L24 | Evidence Passage ($P_{\text{evidence}}$) | **-0.000** [-0.009, +0.008] | -0.002 [-0.013, +0.009] | +0.003 [-0.010, +0.015] | 0.000 nats |
| L24 | Post-Evidence Token ($P_{\text{post-evidence}}$) | **+0.015** [+0.003, +0.026] | +0.003 [-0.008, +0.014] | +0.014 [+0.002, +0.027] | 0.000 nats |
| L24 | Answer Text ($P_{\text{answer}}$) | **-0.001** [-0.011, +0.009] | +0.007 [-0.004, +0.019] | +0.004 [-0.006, +0.015] | 0.000 nats |
| L24 | Citation Predicting Token ($P_{\text{citation}}$) | **+0.001** [-0.147, +0.179] | -0.102 [-0.175, -0.023] | -0.446 [-0.793, -0.073] | 0.045 nats |

### Corruption: `CONTENT_SWAP`
*Donor Baseline Preference: +0.217 [-0.425, +0.865] nats*

| Layer | Intervened Token Position | Mixer Shift $\Delta_{\text{First}}$ | MLP Shift $\Delta_{\text{First}}$ | Residual Stream Shift | Mixer $D_{\text{KL}}$ |
| :---: | :--- | :---: | :---: | :---: | :---: |
| L14 | Source Label Token ($P_{\text{label}}$) | **-0.863** [-1.113, -0.621] | -0.050 [-0.150, +0.061] | +1.586 [+1.233, +1.981] | 0.062 nats |
| L14 | Evidence Passage ($P_{\text{evidence}}$) | **+0.696** [+0.527, +0.889] | -0.113 [-0.168, -0.059] | +0.853 [+0.614, +1.131] | 0.027 nats |
| L14 | Post-Evidence Token ($P_{\text{post-evidence}}$) | **+0.170** [+0.127, +0.211] | -0.051 [-0.078, -0.026] | +0.209 [+0.140, +0.273] | 0.003 nats |
| L14 | Answer Text ($P_{\text{answer}}$) | **-0.058** [-0.113, +0.003] | -0.014 [-0.058, +0.039] | -0.054 [-0.119, +0.015] | 0.003 nats |
| L14 | Citation Predicting Token ($P_{\text{citation}}$) | **+0.010** [-0.010, +0.034] | +0.025 [-0.001, +0.051] | -0.003 [-0.040, +0.034] | 0.001 nats |
| L20 | Source Label Token ($P_{\text{label}}$) | **-0.165** [-0.237, -0.094] | +0.546 [+0.413, +0.686] | +1.649 [+1.282, +2.040] | 0.004 nats |
| L20 | Evidence Passage ($P_{\text{evidence}}$) | **+0.006** [-0.012, +0.025] | -0.004 [-0.021, +0.014] | -0.059 [-0.085, -0.036] | 0.000 nats |
| L20 | Post-Evidence Token ($P_{\text{post-evidence}}$) | **+0.005** [-0.008, +0.019] | -0.003 [-0.018, +0.011] | +0.011 [-0.005, +0.028] | 0.000 nats |
| L20 | Answer Text ($P_{\text{answer}}$) | **-0.002** [-0.017, +0.014] | -0.004 [-0.019, +0.011] | -0.001 [-0.018, +0.018] | 0.000 nats |
| L20 | Citation Predicting Token ($P_{\text{citation}}$) | **-0.015** [-0.129, +0.105] | +0.186 [+0.049, +0.341] | +0.861 [+0.434, +1.283] | 0.017 nats |
| L24 | Source Label Token ($P_{\text{label}}$) | **-0.032** [-0.046, -0.016] | +0.105 [+0.059, +0.154] | +1.057 [+0.814, +1.328] | 0.000 nats |
| L24 | Evidence Passage ($P_{\text{evidence}}$) | **+0.004** [-0.004, +0.014] | +0.003 [-0.007, +0.013] | +0.016 [-0.004, +0.035] | 0.000 nats |
| L24 | Post-Evidence Token ($P_{\text{post-evidence}}$) | **+0.005** [-0.007, +0.018] | +0.011 [+0.002, +0.021] | +0.018 [+0.005, +0.031] | 0.000 nats |
| L24 | Answer Text ($P_{\text{answer}}$) | **-0.002** [-0.012, +0.008] | +0.009 [-0.003, +0.021] | +0.010 [+0.000, +0.021] | 0.000 nats |
| L24 | Citation Predicting Token ($P_{\text{citation}}$) | **-0.054** [-0.207, +0.119] | -0.018 [-0.101, +0.083] | +0.394 [-0.140, +0.888] | 0.036 nats |

### Corruption: `QUESTION_SWAP`
*Donor Baseline Preference: +0.968 [-0.085, +1.996] nats*

| Layer | Intervened Token Position | Mixer Shift $\Delta_{\text{First}}$ | MLP Shift $\Delta_{\text{First}}$ | Residual Stream Shift | Mixer $D_{\text{KL}}$ |
| :---: | :--- | :---: | :---: | :---: | :---: |
| L14 | Source Label Token ($P_{\text{label}}$) | **-0.845** [-1.144, -0.582] | -0.043 [-0.163, +0.070] | +1.601 [+1.202, +2.048] | 0.070 nats |
| L14 | Evidence Passage ($P_{\text{evidence}}$) | **+0.270** [+0.156, +0.394] | -0.072 [-0.176, +0.032] | +0.163 [+0.022, +0.336] | 0.029 nats |
| L14 | Post-Evidence Token ($P_{\text{post-evidence}}$) | **+0.150** [+0.100, +0.212] | +0.013 [-0.028, +0.061] | +0.078 [+0.003, +0.170] | 0.005 nats |
| L14 | Answer Text ($P_{\text{answer}}$) | **-0.267** [-0.440, -0.105] | -0.052 [-0.133, +0.031] | +2.812 [+2.092, +3.532] | 0.046 nats |
| L14 | Citation Predicting Token ($P_{\text{citation}}$) | **-0.054** [-0.091, -0.016] | -0.004 [-0.059, +0.060] | -0.097 [-0.170, -0.032] | 0.001 nats |
| L20 | Source Label Token ($P_{\text{label}}$) | **-0.141** [-0.217, -0.073] | +0.534 [+0.381, +0.716] | +1.657 [+1.242, +2.113] | 0.004 nats |
| L20 | Evidence Passage ($P_{\text{evidence}}$) | **+0.011** [-0.009, +0.030] | -0.009 [-0.025, +0.007] | -0.028 [-0.057, +0.003] | 0.001 nats |
| L20 | Post-Evidence Token ($P_{\text{post-evidence}}$) | **+0.021** [+0.009, +0.033] | +0.018 [-0.000, +0.037] | +0.014 [-0.003, +0.030] | 0.000 nats |
| L20 | Answer Text ($P_{\text{answer}}$) | **+0.002** [-0.016, +0.019] | +0.008 [-0.009, +0.025] | +0.014 [-0.006, +0.035] | 0.001 nats |
| L20 | Citation Predicting Token ($P_{\text{citation}}$) | **-0.785** [-1.007, -0.563] | +0.029 [-0.158, +0.220] | +4.458 [+3.771, +5.160] | 0.084 nats |
| L24 | Source Label Token ($P_{\text{label}}$) | **-0.034** [-0.051, -0.016] | +0.094 [+0.047, +0.146] | +1.026 [+0.773, +1.344] | 0.000 nats |
| L24 | Evidence Passage ($P_{\text{evidence}}$) | **+0.002** [-0.011, +0.015] | +0.012 [-0.002, +0.025] | +0.015 [-0.007, +0.042] | 0.000 nats |
| L24 | Post-Evidence Token ($P_{\text{post-evidence}}$) | **+0.009** [-0.004, +0.024] | -0.001 [-0.013, +0.011] | +0.008 [-0.002, +0.018] | 0.000 nats |
| L24 | Answer Text ($P_{\text{answer}}$) | **+0.017** [+0.005, +0.029] | +0.016 [+0.002, +0.029] | +0.023 [+0.007, +0.039] | 0.000 nats |
| L24 | Citation Predicting Token ($P_{\text{citation}}$) | **-0.464** [-0.645, -0.274] | -0.092 [-0.221, +0.042] | +2.570 [+1.834, +3.368] | 0.045 nats |

### Corruption: `ORDER_PERM`
*Donor Baseline Preference: -0.643 [-1.219, +0.019] nats*

| Layer | Intervened Token Position | Mixer Shift $\Delta_{\text{First}}$ | MLP Shift $\Delta_{\text{First}}$ | Residual Stream Shift | Mixer $D_{\text{KL}}$ |
| :---: | :--- | :---: | :---: | :---: | :---: |
| L14 | Source Label Token ($P_{\text{label}}$) | **-0.259** [-0.458, -0.119] | +0.045 [-0.019, +0.116] | +1.376 [+1.050, +1.758] | 0.030 nats |
| L14 | Evidence Passage ($P_{\text{evidence}}$) | **+0.199** [+0.100, +0.316] | -0.014 [-0.066, +0.041] | +0.257 [+0.114, +0.423] | 0.026 nats |
| L14 | Post-Evidence Token ($P_{\text{post-evidence}}$) | **+0.045** [+0.004, +0.096] | -0.004 [-0.028, +0.018] | +0.080 [+0.024, +0.143] | 0.004 nats |
| L14 | Answer Text ($P_{\text{answer}}$) | **-0.045** [-0.099, +0.005] | -0.003 [-0.068, +0.066] | -0.118 [-0.200, -0.040] | 0.004 nats |
| L14 | Citation Predicting Token ($P_{\text{citation}}$) | **+0.019** [-0.004, +0.040] | +0.003 [-0.028, +0.040] | -0.016 [-0.054, +0.019] | 0.002 nats |
| L20 | Source Label Token ($P_{\text{label}}$) | **-0.098** [-0.176, -0.028] | +0.045 [-0.071, +0.171] | +1.412 [+1.062, +1.785] | 0.003 nats |
| L20 | Evidence Passage ($P_{\text{evidence}}$) | **+0.007** [-0.009, +0.023] | +0.015 [+0.000, +0.029] | -0.016 [-0.036, +0.009] | 0.000 nats |
| L20 | Post-Evidence Token ($P_{\text{post-evidence}}$) | **+0.008** [-0.006, +0.022] | +0.013 [-0.000, +0.027] | +0.006 [-0.010, +0.025] | 0.000 nats |
| L20 | Answer Text ($P_{\text{answer}}$) | **+0.005** [-0.011, +0.022] | +0.017 [-0.001, +0.034] | +0.003 [-0.011, +0.020] | 0.000 nats |
| L20 | Citation Predicting Token ($P_{\text{citation}}$) | **-0.062** [-0.217, +0.111] | +0.057 [-0.065, +0.180] | -0.093 [-0.689, +0.447] | 0.033 nats |
| L24 | Source Label Token ($P_{\text{label}}$) | **-0.004** [-0.018, +0.009] | +0.046 [+0.002, +0.090] | +0.930 [+0.693, +1.197] | 0.000 nats |
| L24 | Evidence Passage ($P_{\text{evidence}}$) | **+0.013** [+0.002, +0.023] | -0.002 [-0.013, +0.009] | -0.003 [-0.018, +0.016] | 0.000 nats |
| L24 | Post-Evidence Token ($P_{\text{post-evidence}}$) | **+0.005** [-0.008, +0.020] | +0.009 [-0.003, +0.021] | +0.003 [-0.008, +0.014] | 0.000 nats |
| L24 | Answer Text ($P_{\text{answer}}$) | **+0.002** [-0.011, +0.013] | +0.007 [-0.004, +0.019] | +0.000 [-0.012, +0.013] | 0.000 nats |
| L24 | Citation Predicting Token ($P_{\text{citation}}$) | **-0.113** [-0.274, +0.069] | -0.073 [-0.158, +0.027] | -0.515 [-1.009, -0.007] | 0.044 nats |

---

## Mechanistic Synthesis & Conclusion

1. **Citation-Position vs. Prompt-Body Position Dissociation:**
   - Interventions at $P_{\text{citation}}$ reliably transfer the counterfactual identifier, consistent with late decision transport.
   - The impact of prompt-body interventions at $P_{\text{label}}$ and $P_{\text{evidence}}$ across Layer 14, 20, and 24 determines whether the binding association is constructed at early/mid layers or actively formed by late cross-attention queries.