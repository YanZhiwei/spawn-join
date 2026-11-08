"""Explicit registration of upstream harness and provider profiles.

DeepAgents profiles are beta and live in process-wide registries. This module
only validates the product-supplied bindings and forwards them to the upstream
registration functions before graph construction. It does not expose a second
registry or claim to know the final middleware stack.
"""

from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import Any

from deepagents import (
    HarnessProfile,
    HarnessProfileConfig,
    ProviderProfile,
    register_harness_profile,
    register_provider_profile,
)

from .errors import ProfileConfigurationError
from .middleware import RESERVED_MIDDLEWARE_NAMES


def _require_key(key: str, label: str) -> str:
    if not key.strip():
        raise ProfileConfigurationError(f"profiles.{label}: key must not be blank")
    return key


def _excluded_middleware(
    profile: HarnessProfile | HarnessProfileConfig,
) -> Collection[Any]:
    return profile.excluded_middleware


def _validate_unique(
    bindings: Sequence[Any],
    label: str,
) -> None:
    seen: set[str] = set()
    for binding in bindings:
        if binding.key in seen:
            raise ProfileConfigurationError(
                f"profiles.{label}: duplicate key {binding.key!r}"
            )
        seen.add(binding.key)


def _validate_reserved_names(
    bindings: Sequence[HarnessProfileBinding],
    extra_reserved: Collection[str] = (),
) -> None:
    reserved = RESERVED_MIDDLEWARE_NAMES | set(extra_reserved)
    for binding in bindings:
        excluded = {
            entry
            for entry in _excluded_middleware(binding.profile)
            if isinstance(entry, str)
        }
        conflicts = excluded & reserved
        if conflicts:
            names = ", ".join(sorted(conflicts))
            raise ProfileConfigurationError(
                f"profiles.harness.{binding.key}: cannot exclude package-reserved "
                f"middleware: {names}"
            )


@dataclass(frozen=True, slots=True)
class HarnessProfileBinding:
    """One harness profile bound to a provider or model key."""

    key: str
    profile: HarnessProfile | HarnessProfileConfig

    def __post_init__(self) -> None:
        _require_key(self.key, "harness")


@dataclass(frozen=True, slots=True)
class ProviderProfileBinding:
    """One provider profile bound to a provider or model key."""

    key: str
    profile: ProviderProfile

    def __post_init__(self) -> None:
        _require_key(self.key, "providers")


@dataclass(frozen=True, slots=True)
class ProfilesConfiguration:
    """Validated profile registrations applied before graph assembly."""

    harness: Sequence[HarnessProfileBinding] = ()
    providers: Sequence[ProviderProfileBinding] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "harness", tuple(self.harness))
        object.__setattr__(self, "providers", tuple(self.providers))

    @property
    def harness_keys(self) -> tuple[str, ...]:
        return tuple(binding.key for binding in self.harness)

    @property
    def provider_keys(self) -> tuple[str, ...]:
        return tuple(binding.key for binding in self.providers)

    def validate(self, extra_reserved: Collection[str] = ()) -> None:
        """Reject duplicate keys and package-reserved middleware exclusions."""

        _validate_unique(self.harness, "harness")
        _validate_unique(self.providers, "providers")
        _validate_reserved_names(self.harness, extra_reserved)

    def apply(self, extra_reserved: Collection[str] = ()) -> None:
        """Validate, then register every binding with DeepAgents."""

        self.validate(extra_reserved)
        try:
            for binding in self.harness:
                register_harness_profile(binding.key, binding.profile)
            for binding in self.providers:
                register_provider_profile(binding.key, binding.profile)
        except Exception as exc:
            raise ProfileConfigurationError(
                "profiles: upstream profile registration failed"
            ) from exc
