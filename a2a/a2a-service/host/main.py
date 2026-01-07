"""
Entry point for the Paywall Agent server.

This module boots an A2A (Agent-to-Agent) HTTP server using Starlette via
`A2AStarletteApplication` and exposes:

- An Agent Card at `/.well-known/agent-card.json` describing the agent's
  identity, capabilities, and skills.
- An RPC endpoint at `/rpc` that dispatches incoming A2A requests to the
  configured `DefaultRequestHandler`.

The agent is backed by a `PaywallExecutor`, and uses in-memory stores for
task tracking and (optionally) push notification configuration.

Notes:
- Environment variables are loaded on import via `python-dotenv` (`load_dotenv()`),
  allowing `lib.config.settings` to resolve configuration from the environment.
- This module is intended to be executed directly (e.g. `python -m agent.main`)
  to start a local server, typically bound to `0.0.0.0` on
  `settings.A2A_AGENT_PORT`.
"""

from dotenv import load_dotenv

load_dotenv()

import asyncio
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryPushNotificationConfigStore, InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from .executor import PaywallExecutor
from .lib.config import settings


async def main() -> None:
    """
    Build and run the Paywall Agent HTTP server.

    This function wires together:
    - In-memory task storage (`InMemoryTaskStore`) for tracking request lifecycle.
    - In-memory push-notification config storage (`InMemoryPushNotificationConfigStore`).
    - A default A2A request handler (`DefaultRequestHandler`) backed by `PaywallExecutor`.
    - An `AgentCard` describing the agent's capabilities and skills.
    - A Starlette application via `A2AStarletteApplication(...).build(...)`.
    - A Uvicorn server configured to use the asyncio loop.

    The server exposes:
    - Agent Card: `/.well-known/agent-card.json`
    - RPC endpoint: `/rpc`

    Returns:
        None. This coroutine runs the server until shutdown.

    Raises:
        RuntimeError: If the underlying Uvicorn server fails to start.
        Exception: Propagates unexpected errors from app construction or server startup.

    Example:
        Run the server from a shell:

        >>> python -m agent.main

        Or programmatically:

        >>> import asyncio
        >>> from agent.main import main
        >>> asyncio.run(main())
    """
    # Stores used by the A2A framework to track tasks and (optionally) push configs.
    task_store = InMemoryTaskStore()
    push_store = InMemoryPushNotificationConfigStore()

    # Request handler that dispatches incoming RPC calls to our agent executor.
    handler = DefaultRequestHandler(
        agent_executor=PaywallExecutor(),
        task_store=task_store,
        push_config_store=push_store,
    )

    # AgentCard describes this agent to other agents/clients (identity + skills).
    agent_card = AgentCard(
        version="1.0.0",
        name="paywall-agent",
        description="Discovers X402 paywalled resources via AgentCards and pays to access them.",
        url=f"http://localhost:{settings.A2A_AGENT_PORT}",
        capabilities=AgentCapabilities(
            streaming=True,
            push_notifications=False,
            state_transition_history=False,
            extensions=None,
        ),
        default_input_modes=["text/plain", "application/json"],
        default_output_modes=["text/plain", "application/json"],
        skills=[
            AgentSkill(
                id="discover_and_fetch_x402",
                name="Discover & fetch X402 resource",
                description=(
                    "Discover agent cards, call a protected endpoint, handle 402, "
                    "settle payment, retry with x-payment-id."
                ),
                tags=["x402", "payments", "discovery"],
                examples=[
                    (
                        f'{{"discoveryUrls": {list(settings.default_discovery_urls)}, '
                        f'"query": "get paywalled resource"}}'
                    )
                ],
            )
        ],
        supports_authenticated_extended_card=False,
    )

    # Build the ASGI app, mounting the agent card and RPC routes.
    app = A2AStarletteApplication(agent_card=agent_card, http_handler=handler).build(
        agent_card_url="/.well-known/agent-card.json",
        rpc_url="/rpc",
    )

    # Run with Uvicorn using the asyncio event loop.
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=settings.A2A_AGENT_PORT,
        loop="asyncio",
    )
    await uvicorn.Server(config).serve()


if __name__ == "__main__":
    """
    Script entrypoint.

    Executes `main()` inside an asyncio event loop when run as a script.
    """
    asyncio.run(main())
