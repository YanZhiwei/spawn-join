"""Load model catalogs from an explicit YAML file and resolve API keys."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from ._catalog import DEFAULT_MODEL_FILE, ModelCatalog, ModelSummary

__all__ = ["ModelCatalog", "ModelSummary", "load_model_catalog"]


def load_model_catalog(
    path: str | Path = DEFAULT_MODEL_FILE,
    *,
    env_file: str | Path | None | Literal["auto"] = "auto",
) -> ModelCatalog:
    """Load and validate a model catalog from an explicit YAML file."""
    return ModelCatalog.from_file(path, env_file=env_file)
