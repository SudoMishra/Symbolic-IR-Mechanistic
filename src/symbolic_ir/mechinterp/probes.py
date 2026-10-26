from __future__ import annotations


def fit_linear_probe(features, labels, *, random_state: int = 0):
    try:
        from sklearn.linear_model import LogisticRegression
    except ImportError as exc:
        raise RuntimeError("Install llm-symbolic-ir[mechinterp] for linear probes") from exc
    probe = LogisticRegression(max_iter=2000, random_state=random_state)
    return probe.fit(features, labels)
