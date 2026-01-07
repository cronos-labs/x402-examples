"""
Standardized message enums used across pipelines and A2A task execution.

This module defines string-based enum classes for success, progress, and failure
messages. These enums provide a single source of truth for user-facing and
log-friendly messages emitted during pipeline execution.

All enums inherit from `AutoStrEnum`, ensuring they behave like plain strings
while retaining enum semantics.
"""

from .common import AutoStrEnum


class StatusMessage(AutoStrEnum):
    """
    Success and terminal status messages for pipeline execution.

    These messages are typically used for:
      - Structured logging
      - Final task status summaries
      - User-facing completion messages
    """

    PAYWALL_SUCCESS = "Paywalled resource fetched successfully"
    PAYWALL_FAILED = "Paywall pipeline failed"


class ProgressMessage(AutoStrEnum):
    """
    Progress message constants for stepwise execution updates.

    These messages describe high-level operational stages and are commonly
    emitted via progress/status events to inform clients of ongoing work.
    """

    PAYWALL_PLANNING = "Planning paywall request"
    PAYWALL_DISCOVERING_AGENTS = "Discovering agents"
    PAYWALL_SELECTING_TARGET = "Selecting target agent/resource"
    PAYWALL_FETCHING_RESOURCE = "Fetching resource (may trigger 402)"
    PAYWALL_RETRYING_FETCH = "Retrying fetch after settlement"


class FailMessage(AutoStrEnum):
    """
    Standardized failure message templates for task pipelines.

    These enums represent common failure scenarios and are used to produce
    consistent, user-facing error messages across the system.
    """

    PAYWALL_NO_AGENTS = "No agents discovered"
    PAYWALL_NO_TARGET = "No suitable agent/resource found in discovered AgentCards"
    PAYWALL_FETCH_FAILED = "Fetch failed"
