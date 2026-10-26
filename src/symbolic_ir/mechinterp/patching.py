from __future__ import annotations

from contextlib import AbstractContextManager


def _primary(output):
    if hasattr(output, "last_hidden_state"):
        return output.last_hidden_state
    return output[0] if isinstance(output, (tuple, list)) else output


def _replace_primary(output, modified):
    if isinstance(output, tuple):
        return (modified, *output[1:])
    if isinstance(output, list):
        return [modified, *output[1:]]
    return modified


class ActivationPatcher(AbstractContextManager):
    """Replace selected token positions in one PyTorch module's output."""

    def __init__(self, model, module_name: str, source_activation, token_positions: list[int]) -> None:
        modules = dict(model.named_modules())
        if module_name not in modules:
            raise KeyError(f"Unknown module: {module_name}")
        self.source_activation = source_activation
        self.token_positions = token_positions

        def patch(module, inputs, output):
            primary = _primary(output)
            modified = primary.clone()
            modified[:, self.token_positions, :] = self.source_activation[:, self.token_positions, :].to(modified.device)
            return _replace_primary(output, modified)

        self._handle = modules[module_name].register_forward_hook(patch)

    def __exit__(self, exc_type, exc_value, traceback):
        self._handle.remove()
        return False


class PositionActivationRecorder(AbstractContextManager):
    """Capture only selected positions from one module's output.

    Keeping the selection inside the hook avoids retaining a full long-context
    residual stream merely to patch a handful of positions later.
    """

    def __init__(self, model, module_name: str, token_positions: list[int]) -> None:
        modules = dict(model.named_modules())
        if module_name not in modules:
            raise KeyError(f"Unknown module: {module_name}")
        if not token_positions:
            raise ValueError("token_positions must not be empty")
        self.activation = None

        def capture(_module, _inputs, output):
            primary = _primary(output)
            self.activation = primary[0, token_positions, :].detach().cpu()

        self._handle = modules[module_name].register_forward_hook(capture)

    def __exit__(self, exc_type, exc_value, traceback):
        self._handle.remove()
        return False


class PositionActivationPatcher(AbstractContextManager):
    """Patch an aligned position set, broadcasting it across the batch.

    ``source_activation`` has shape ``[positions, hidden]``. Source and target
    position counts must match; callers should explicitly choose pooled or
    endpoint representations when two tokenizations have different lengths.
    """

    def __init__(self, model, module_name: str, source_activation, target_positions: list[int]) -> None:
        modules = dict(model.named_modules())
        if module_name not in modules:
            raise KeyError(f"Unknown module: {module_name}")
        if not target_positions:
            raise ValueError("target_positions must not be empty")
        if source_activation.ndim != 2 or source_activation.shape[0] != len(target_positions):
            raise ValueError(
                "source_activation must have shape [len(target_positions), hidden]"
            )

        def patch(_module, _inputs, output):
            primary = _primary(output)
            modified = primary.clone()
            values = source_activation.to(device=modified.device, dtype=modified.dtype)
            modified[:, target_positions, :] = values.unsqueeze(0).expand(modified.shape[0], -1, -1)
            return _replace_primary(output, modified)

        self._handle = modules[module_name].register_forward_hook(patch)

    def __exit__(self, exc_type, exc_value, traceback):
        self._handle.remove()
        return False


class BatchPositionActivationPatcher(AbstractContextManager):
    """Patch different aligned positions and donor states in each batch row."""

    def __init__(self, model, module_name: str, source_activations, target_positions) -> None:
        modules = dict(model.named_modules())
        if module_name not in modules:
            raise KeyError(f"Unknown module: {module_name}")
        if len(source_activations) != len(target_positions):
            raise ValueError("A donor activation is required for every target position set")
        for values, positions in zip(source_activations, target_positions):
            if values.ndim != 2 or values.shape[0] != len(positions):
                raise ValueError("Every donor must have shape [len(target_positions[row]), hidden]")

        def patch(_module, _inputs, output):
            primary = _primary(output)
            if primary.shape[0] != len(source_activations):
                raise ValueError("Runtime batch size does not match the configured donor batch")
            modified = primary.clone()
            for row, (values, positions) in enumerate(zip(source_activations, target_positions)):
                modified[row, positions, :] = values.to(device=modified.device, dtype=modified.dtype)
            return _replace_primary(output, modified)

        self._handle = modules[module_name].register_forward_hook(patch)

    def __exit__(self, exc_type, exc_value, traceback):
        self._handle.remove()
        return False
