"""
Enum definitions for artifact names used in A2A task execution.

This module defines `ArtifactName`, a string-based enum that standardizes the
names assigned to artifacts emitted during pipeline execution. Using a shared
enum avoids hard-coded strings and ensures consistent artifact naming across
agents, pipelines, and clients.
"""

from .common import AutoStrEnum


class ArtifactName(AutoStrEnum):
    """
    Standard artifact name identifiers.

    These values are used when emitting artifacts (e.g. via `finish()` or
    artifact update events) so downstream consumers can reliably identify
    and interpret the artifact type.
    """

    PAYWALLED_RESOURCE = "paywalled_resource"
