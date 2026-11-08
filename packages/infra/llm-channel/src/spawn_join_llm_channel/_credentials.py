"""Resolve opaque credential references from an explicit environment mapping."""

import os
from collections.abc import Mapping

from spawn_join_llm_provider import ConfigurationError


def validate_api_key(api_key: str) -> str:
    """Reject empty or whitespace-padded API keys before SDK construction."""
    if not api_key or api_key != api_key.strip():
        raise ConfigurationError(
            "API key must be non-empty without surrounding whitespace"
        )
    return api_key


def resolve_api_key(
    credential_ref: str,
    *,
    environ: Mapping[str, str] | None = None,
) -> str:
    """Resolve ``credential_ref`` as an environment variable name.

    The caller may pass an explicit mapping for tests or host-managed
    environments. The process environment is read only; it is never mutated.
    """
    source = os.environ if environ is None else environ
    value = source.get(credential_ref)
    if value is None:
        raise ConfigurationError(
            f"credential {credential_ref!r} is not set in the environment"
        )
    return validate_api_key(value)
