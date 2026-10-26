from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Iterable


class ActivationRecorder(AbstractContextManager):
    """Capture PyTorch module outputs by exact module name."""

    def __init__(self, model, module_names: Iterable[str]) -> None:
        wanted = set(module_names)
        modules = dict(model.named_modules())
        missing = wanted - modules.keys()
        if missing:
            raise KeyError(f"Unknown modules: {sorted(missing)}")
        self.activations = {}
        self._handles = []
        for name in wanted:
            def hook(module, inputs, output, name=name):
                value = output[0] if isinstance(output, tuple) else output
                self.activations[name] = value.detach().cpu()
            self._handles.append(modules[name].register_forward_hook(hook))

    def __exit__(self, exc_type, exc_value, traceback):
        for handle in self._handles:
            handle.remove()
        return False

