"""Stable error taxonomy for the work runtime."""

from __future__ import annotations


class WorkError(Exception):
    """Base class for every work-runtime error."""


class WorkConfigurationError(WorkError):
    """Invalid configuration or policy input."""


class WorkNotFoundError(WorkError):
    """The requested work item does not exist."""


class WorkConflictError(WorkError):
    """An illegal state transition or duplicate idempotency key."""


class LeaseLostError(WorkError):
    """The caller no longer owns the lease and must stop writing back."""


class StoreError(WorkError):
    """A storage adapter failure; the original cause is preserved."""


class NotifierError(WorkError):
    """A wake-up adapter failure; notification is best-effort."""
