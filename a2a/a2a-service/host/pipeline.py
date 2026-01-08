"""
Orchestration pipeline for discovering and accessing X402 paywalled resources.

This module defines `PaywallPipeline`, an async workflow that coordinates:

- Emitting structured progress events to the A2A event stream.
- Discovering candidate agents from one or more discovery URLs.
- Using an LLM-backed planner to select the best target agent for a user query.
- Fetching a protected resource from the chosen target, including any paywall /
  payment-handling logic encapsulated by `PaywallService`.
- Emitting a final artifact on success, or a failure event on errors.

The pipeline is intentionally thin and delegates core behavior to:
- `PaywallService`: discovery, target selection application, resource fetching,
  and result formatting.
- `PaywallPlanner`: choosing the target agent given a query and discovered agents.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .lib.a2a.events import progress, finish, fail
from .lib.enums.message import FailMessage, ProgressMessage
from .lib.enums.name import ArtifactName
from .lib.errors.app_error import AppError


class PaywallPipeline:
    """
    End-to-end workflow for "discover -> choose -> fetch -> report" in the paywall agent.

    The pipeline is designed to be invoked by `PaywallExecutor` with a normalized
    request payload. It emits incremental progress updates, and returns early
    with a failure event if any required step cannot be completed.

    Attributes:
        service: Service layer providing discovery, fetch, formatting, and
            choice application logic (e.g., payment settlement + retry behavior).
        planner: Planner responsible for selecting the best target agent based on
            a natural-language query and the list of discovered agents.
        event_queue: A2A event queue used to emit progress / finish / fail events.
        task: The A2A task instance associated with this request.
    """

    def __init__(self, service: Any, planner: Any, event_queue: Any, task: Any) -> None:
        """
        Create a new pipeline instance.

        Args:
            service: `PaywallService`-like object implementing:
                - discover_agents(discovery_urls)
                - apply_choice(agents, choice)
                - fetch_resource(target)
                - format_result(result)
            planner: `PaywallPlanner`-like object implementing:
                - choose_target(query, agents)
            event_queue: A2A `EventQueue` (or compatible) used to send events.
            task: A2A task object representing the ongoing request.

        Notes:
            Types are intentionally loose (`Any`) to keep the pipeline decoupled
            from concrete implementations and simplify testing/mocking.
        """
        self.service = service
        self.planner = planner
        self.event_queue = event_queue
        self.task = task

    async def run(self, payload: Dict[str, Any]) -> None:
        """
        Execute the paywall discovery and fetch workflow.

        Payload contract:
            - discoveryUrls (optional): list[str]
                One or more URLs to query for AgentCards / discovery endpoints.
                Defaults to ["http://localhost:8787"].
            - query (optional): str
                Natural-language intent describing what paywalled resource to fetch.
                Defaults to "fetch paywalled resource".

        High-level steps:
            1) Emit planning + discovery progress events.
            2) Discover agents from the provided discovery URLs.
            3) Ask the planner to choose the best target agent for the query.
            4) Apply the planner's choice to a concrete target record.
            5) Fetch the resource via the service (handles 402/payment internally).
            6) On success, emit a `finish` event with an artifact containing formatted text.
               On failure, emit a `fail` event and return.

        Error handling:
            - `AppError` is treated as a structured application error: it is logged and
              surfaced as a standardized failure message.
            - Any other exception is treated as unexpected: a generic failure event is emitted.

        Args:
            payload: A dict-like request object (typically parsed from JSON or message parts).

        Returns:
            None. Results are communicated via emitted events.

        Example:
            >>> pipeline = PaywallPipeline(service, planner, event_queue, task)
            >>> await pipeline.run({
            ...     "discoveryUrls": ["http://localhost:8787"],
            ...     "query": "get paywalled resource"
            ... })
        """
        try:
            discovery_urls: List[str] = payload.get("discoveryUrls") or [
                "http://localhost:8787"
            ]
            query: str = payload.get("query") or "fetch paywalled resource"

            # Announce planning and discovery start.
            await progress(
                self.event_queue,
                self.task,
                f"{ProgressMessage.PAYWALL_PLANNING}: {query}",
            )
            await progress(
                self.event_queue,
                self.task,
                f"{ProgressMessage.PAYWALL_DISCOVERING_AGENTS}: {discovery_urls}",
            )

            # 1) Discover agents.
            agents = await self.service.discover_agents(discovery_urls)
            if not agents:
                await fail(self.event_queue, self.task, FailMessage.PAYWALL_NO_AGENTS)
                return

            # 2) Select target agent.
            await progress(
                self.event_queue,
                self.task,
                ProgressMessage.PAYWALL_SELECTING_TARGET,
            )

            choice = await self.planner.choose_target(query=query, agents=agents)
            if not choice:
                await fail(self.event_queue, self.task, FailMessage.PAYWALL_NO_TARGET)
                return

            target: Optional[Dict[str, Any]] = self.service.apply_choice(agents, choice)
            if not target:
                await fail(
                    self.event_queue,
                    self.task,
                    f"{FailMessage.PAYWALL_NO_TARGET}: {choice}",
                )
                return

            # 3) Fetch resource (service is responsible for payment handling & retries).
            await progress(
                self.event_queue,
                self.task,
                f"Selected: {target['name']} ({target['baseUrl']})",
            )
            await progress(
                self.event_queue,
                self.task,
                ProgressMessage.PAYWALL_FETCHING_RESOURCE,
            )

            result: Dict[str, Any] = await self.service.fetch_resource(target)
            if not result.get("ok"):
                await fail(
                    self.event_queue,
                    self.task,
                    f"{FailMessage.PAYWALL_FETCH_FAILED}: {result}",
                )
                return

            # 4) Emit success artifact with formatted output.
            await finish(
                self.event_queue,
                self.task,
                text=self.service.format_result(result),
                name=ArtifactName.PAYWALLED_RESOURCE,
            )

        except AppError as e:
            # Central handler for structured application errors.
            e.log()
            await fail(
                self.event_queue,
                self.task,
                f"{FailMessage.PAYWALL_FETCH_FAILED}: {e.message}",
            )

        except Exception as e:
            # Central handler for any unexpected errors.
            await fail(
                self.event_queue,
                self.task,
                f"{FailMessage.PAYWALL_FETCH_FAILED}: unexpected_error={type(e).__name__}",
            )
