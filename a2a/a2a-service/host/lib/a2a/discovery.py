"""
Utilities for discovering A2A AgentCards from well-known endpoints.

This module provides a minimal helper for fetching an agent's public
AgentCard by probing standard `.well-known` paths on a given base URL.

The discovery process is intentionally simple and resilient:
- Multiple well-known paths are attempted in order.
- Network and parsing errors are swallowed and treated as non-fatal.
- An empty dict is returned when no valid AgentCard can be retrieved.
"""

import httpx
from typing import Dict

WELL_KNOWN_PATHS = [
    "/.well-known/agent-card.json",
    "/.well-known/agent.json",
]
"""
Standard well-known paths probed when attempting to discover an AgentCard.

Paths are tried in order until one returns HTTP 200 with a JSON body.
"""


async def fetch_agent_card(base_url: str) -> Dict:
    """
    Fetch an A2A AgentCard from a base URL.

    This function attempts to retrieve an AgentCard by appending known
    well-known paths (see `WELL_KNOWN_PATHS`) to the provided base URL.

    Behavior:
        - Trailing slashes are stripped from `base_url` before probing.
        - Each candidate URL is fetched via HTTP GET.
        - The first endpoint returning HTTP 200 is assumed to be an AgentCard
          and its parsed JSON body is returned.
        - Any network, timeout, or parsing errors are ignored.
        - If no valid AgentCard is found, an empty dict is returned.

    Args:
        base_url: Base URL of the agent (e.g. "http://localhost:8787").

    Returns:
        A dict representing the AgentCard JSON, or an empty dict if discovery
        fails.

    Example:
        >>> card = await fetch_agent_card("http://localhost:8787")
        >>> if card:
        ...     print(card.get("name"))
        ... else:
        ...     print("No agent card found")
    """
    base = base_url.rstrip("/")
    async with httpx.AsyncClient(timeout=5.0) as client:
        for path in WELL_KNOWN_PATHS:
            url = base + path
            try:
                r = await client.get(url)
                if r.status_code == 200:
                    return r.json()
            except Exception:
                pass
    return {}
