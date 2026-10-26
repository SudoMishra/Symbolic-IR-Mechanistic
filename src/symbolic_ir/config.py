"""Configuration loading, validation, hashing, and grid expansion."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

import yaml


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class ExperimentConfig:
    name: str
    seed: int
    dataset: dict[str, Any]
    identifiers: tuple[str, ...]
    backend: dict[str, Any]
    generation: dict[str, Any]
    output_dir: str
    metadata: dict[str, Any]

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ExperimentConfig":
        required = {"name", "seed", "dataset", "identifiers", "backend"}
        missing = sorted(required - value.keys())
        if missing:
            raise ConfigError(f"Missing required config keys: {', '.join(missing)}")
        if not value["identifiers"]:
            raise ConfigError("identifiers must contain at least one condition")
        return cls(
            name=str(value["name"]),
            seed=int(value["seed"]),
            dataset=dict(value["dataset"]),
            identifiers=tuple(map(str, value["identifiers"])),
            backend=dict(value["backend"]),
            generation=dict(value.get("generation", {})),
            output_dir=str(value.get("output_dir", "results/raw")),
            metadata=dict(value.get("metadata", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "seed": self.seed,
            "dataset": self.dataset,
            "identifiers": list(self.identifiers),
            "backend": self.backend,
            "generation": self.generation,
            "output_dir": self.output_dir,
            "metadata": self.metadata,
        }

    @property
    def digest(self) -> str:
        payload = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()[:12]


def load_config(path: str | Path) -> ExperimentConfig:
    with Path(path).open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ConfigError("Top-level configuration must be a mapping")
    return ExperimentConfig.from_dict(value)


def expand_grid(config: ExperimentConfig) -> Iterator[dict[str, Any]]:
    """Yield dataset cells while keeping paired examples aligned by seed."""
    grid = dict(config.dataset.get("grid", {}))
    base = {key: value for key, value in config.dataset.items() if key != "grid"}
    cells: list[dict[str, Any]] = [base]
    for key, values in grid.items():
        if not isinstance(values, list):
            raise ConfigError(f"dataset.grid.{key} must be a list")
        cells = [{**cell, key: value} for cell in cells for value in values]
    yield from cells

