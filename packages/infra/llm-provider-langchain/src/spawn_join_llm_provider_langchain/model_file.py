"""Load model catalogs from an explicit YAML file and resolve API keys."""

from __future__ import annotations

from pathlib import Path

from ._model_catalog import ModelCatalog, ModelSummary

__all__ = ["ModelCatalog", "ModelSummary", "load_model_catalog"]


def load_model_catalog(
    path: str | Path,
    *,
    env_file: str | Path | None = None,
) -> ModelCatalog:
    """Load and validate a model catalog from an explicit YAML file."""
    return ModelCatalog.from_file(path, env_file=env_file)
