from __future__ import annotations

from abc import ABC, abstractmethod

from symbolic_ir.schema import GenerationRequest, GenerationResponse


class ModelBackend(ABC):
    @property
    @abstractmethod
    def model_name(self) -> str: ...

    @property
    def model_revision(self) -> str | None:
        return None

    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResponse: ...

