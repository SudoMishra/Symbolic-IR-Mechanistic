# Authoritative Study Metric Glossary & Statistical Standards

This document establishes the single source of truth for evaluation metrics, mathematical definitions, contrast directions, and bootstrap procedures across all analysis scripts, figures, tables, captions, and prose.

---

## 1. Metric Glossary

| Metric Name | JSON Key | Mathematical / Algorithmic Definition | Permitted Prose Label |
|---|---|---|---|
| **Answer Exact Match** | `answer_exact_match` | Binary indicator $\mathbb{I}[\text{norm}(y_\text{pred}) = \text{norm}(y_\text{gold})]$ after lowercasing, punctuation stripping, and whitespace normalization. | Answer Exact Match / Answer Accuracy |
| **Answer F1** | `answer_f1` | Harmonic mean of token-level precision and recall between whitespace-tokenized predicted and gold answer strings: $2 \cdot \frac{P \cdot R}{P + R}$. | Answer F1 |
| **Citation Precision** | `citation_precision` | $\frac{|\mathcal{C}_\text{pred} \cap \mathcal{C}_\text{gold}|}{|\mathcal{C}_\text{pred}|}$ if $|\mathcal{C}_\text{pred}| > 0$ else 0. | Citation Precision |
| **Citation Recall** | `citation_recall` | $\frac{|\mathcal{C}_\text{pred} \cap \mathcal{C}_\text{gold}|}{|\mathcal{C}_\text{gold}|}$ if $|\mathcal{C}_\text{gold}| > 0$ else 1.0. | Citation Recall |
| **Citation F1** | `citation_f1` | $2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$. | Citation F1 |
| **Citation Exact Match** | `citation_exact_match` | Binary indicator $\mathbb{I}[\mathcal{C}_\text{pred} = \mathcal{C}_\text{gold}]$ requiring the exact set of valid citation identifiers including expected delimiters (e.g., `[1]`, `[uuid]`). | Strict Citation / Citation Exact Match |
| **Source Binding Recall** | `source_binding_recall` | Fraction of required gold sources successfully mapped from emitted identifiers (tolerant of formatting/delimiter variations): $\frac{|\mathcal{S}_\text{mapped} \cap \mathcal{S}_\text{gold}|}{|\mathcal{S}_\text{gold}|}$. | Source Binding Recall |
| **Exact Source Binding** | `source_binding_exact` | Binary indicator $\mathbb{I}[\mathcal{S}_\text{mapped} = \mathcal{S}_\text{gold}]$. Requires mapped sources to match gold sources exactly, accepting wrapper omissions (e.g. omitting brackets) but requiring the exact source set. | Exact Source Binding |
| **Invalid ID Rate** | `invalid_id_rate` | Fraction of emitted citation identifiers that do not correspond to any document provided in the prompt context. | Hallucinated / Invalid ID Rate |
| **Malformed ID Rate** | `malformed_id_rate` | Fraction of emitted citation strings that attempt to reference an identifier but violate the specified syntax (e.g., truncated hex, unmatched brackets). | Malformed ID Rate |
| **Surface-Only Failure Rate** | `wrapper_or_surface_failure` | Cases where source binding is completely correct ($\mathcal{S}_\text{mapped} = \mathcal{S}_\text{gold}$) but strict citation exact match failed due solely to syntax/wrapper formatting errors: $\mathbb{I}[\text{binding\_exact} \land \neg \text{citation\_strict}]$. | Surface Formatting Failure Rate |

---

## 2. Contrast Direction Contract

To eliminate sign ambiguities, all paired differences and effect estimates must follow this explicit convention:

$$\Delta = \text{Treatment} - \text{Control}$$

Specifically:
- **UUID vs Structured / Numeric**: $\Delta = \text{UUID} - \text{Numeric}$ (or $\text{UUID} - \text{Structured}$).
  - A **negative** delta ($\Delta < 0$) indicates that UUID degrades performance relative to structured/numeric identifiers (a "UUID penalty").
  - A **positive** delta ($\Delta > 0$) indicates UUID outperforming structured/numeric.
- **Reasoning Budget**: $\Delta = \text{Condition}_\text{Budget=B} - \text{Condition}_\text{Budget=0}$.
- **PII Sanitization**: $\Delta = \text{Masked Condition} - \text{Raw Condition}$.

All tables, plots, and sentences quoting percentage point (pp) deltas must state the direction explicitly.

---

## 3. Paired Bootstrap Specification

1. **Resampling Unit**: Paired semantic example ID (`example_id`). Both arms (e.g., structured and UUID) for a given example ID must be sampled together as a unit.
2. **Replication Count**: Exactly $B = 10,000$ bootstrap resamples.
3. **Confidence Level**: 95% two-sided confidence intervals, computed via the percentile method from the empirical bootstrap distribution:
   $$\text{CI}_{95\%} = \left[ q_{0.025}, q_{0.975} \right]$$
4. **Random Seed**: Standardized seed $S = 202620$ for reproducibility.

---

## 4. Statistical Support Definition

A hypothesis of difference is defined as **statistically supported** if and only if:
- The 95% paired bootstrap confidence interval strictly excludes zero:
  $$\text{CI}_\text{low} > 0 \quad \text{or} \quad \text{CI}_\text{high} < 0$$
- If the 95% confidence interval spans zero ($\text{CI}_\text{low} \le 0 \le \text{CI}_\text{high}$), the effect must be described as **not statistically significant** or **compatible with a null effect**, regardless of the sign of the point estimate.
