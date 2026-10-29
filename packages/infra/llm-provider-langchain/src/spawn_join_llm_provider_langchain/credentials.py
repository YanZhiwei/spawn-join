"""Resolve credential references without exposing secret values."""

import os

from spawn_join_llm_provider import ConfigurationError


def resolve_credential(credential_ref: str) -> str:
    """Resolve an environment-variable credential reference.

    The reference is a variable name, never a secret value. Missing or blank
    values fail with a domain error whose message contains only the reference.
    """

    value = os.environ.get(credential_ref)
    if value is None or not value.strip():
        raise ConfigurationError(f"Credential reference {credential_ref!r} is not set")
    return value
