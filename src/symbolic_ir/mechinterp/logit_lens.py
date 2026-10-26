from __future__ import annotations


def token_logit_trajectory(hidden_states, lm_head, token_ids: list[int]):
    """Return layer-by-layer logits for target token IDs."""
    trajectory = []
    for layer, hidden in enumerate(hidden_states):
        logits = lm_head(hidden[:, -1, :])
        trajectory.append({"layer": layer, "logits": [float(logits[0, token].item()) for token in token_ids]})
    return trajectory

