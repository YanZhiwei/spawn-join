"""Stable error taxonomy for the personal assistant host application."""

from __future__ import annotations


class HostError(Exception):
    """Base class for stable, host-application errors.

    Host errors describe which host concern failed (configuration, storage,
    scheduling, approvals). They deliberately do not wrap model-provider or
    framework errors; those keep their own taxonomy in the owning packages.
    """


class HostConfigError(HostError):
    """Application configuration is missing, malformed, or invalid."""


class HostStoreError(HostError):
    """Work-item or approval persistence failed."""


class HostSchedulingError(HostError):
    """The scheduler could not start or bound a work item."""


class HostApprovalError(HostError):
    """Approval bookkeeping or resume failed."""
