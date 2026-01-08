"""
Centralized application configuration.

This module defines immutable configuration settings for the paywall agent and
related components. Configuration values are primarily sourced from environment
variables, with sensible defaults provided for local development.

The `Settings` dataclass is instantiated once at import time as `settings` and
is intended to be imported and reused throughout the codebase.
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """
    Immutable container for application configuration values.

    This dataclass groups all runtime configuration in a single, typed object.
    Values are resolved eagerly at import time, typically from environment
    variables, and should be treated as read-only.

    Configuration categories:
        - LLM: Model selection for OpenAI-backed planners.
        - Paywall discovery: Default agent discovery URLs.
        - Server: HTTP server binding configuration.
        - X402: Payment/signing credentials.

    Attributes:
        llm_model: Name of the LLM model used for planning and reasoning.
        default_discovery_urls: Tuple of base URLs used for initial agent discovery.
        A2A_AGENT_PORT: TCP port on which the paywall agent HTTP server listens.
        x402_private_key: Private key used for X402 payment signing, or None if unset.
    """

    # LLM
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    """Default LLM model name used by OpenAI-backed planners."""

    # Paywall discovery
    default_discovery_urls: tuple[str, ...] = ("http://localhost:8787",)
    """Default base URLs used to discover AgentCards."""

    # Server
    A2A_AGENT_PORT: int = int(os.getenv("A2A_AGENT_PORT", "9001"))
    """Port on which the paywall agent HTTP server will listen."""

    # X402
    x402_private_key: str | None = os.getenv("X402_PRIVATE_KEY")
    """Private key used for X402 payment signing, if configured."""


# Singleton-style settings instance used throughout the application.
settings = Settings()
