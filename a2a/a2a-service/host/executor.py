"""
A2A agent executor implementation for the Paywall Agent.

This module defines `PaywallExecutor`, the runtime entrypoint invoked by the A2A
server when an RPC request is received. The executor is responsible for:

- Extracting a structured payload from the incoming request (string JSON, or
  structured message parts).
- Creating or reusing an A2A task object and attaching metadata for observability.
- Enqueuing the initial task event so downstream clients can track progress.
- Running the `PaywallPipeline`, which performs discovery, paywall handling,
  payment settlement, and retry logic.

The executor delegates core business logic to:
- `PaywallService` (I/O and integrations)
- `PaywallPlanner` (LLM planning via `OpenAIClient`)
- `PaywallPipeline` (orchestration of the end-to-end flow)
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.utils import new_task

from .pipeline import PaywallPipeline
from .service import PaywallService
from .lib.openai.client import OpenAIClient
from .lib.openai.planner import PaywallPlanner


class PaywallExecutor(AgentExecutor):
    """
    A2A `AgentExecutor` for discovering and accessing X402 paywalled resources.

    The executor is called by the A2A server for each incoming request. It builds
    a normalized payload (dict) to pass into `PaywallPipeline.run()`, and ensures
    the A2A task lifecycle is initialized and announced via the event queue.

    Attributes:
        service: High-level service wrapper used by the pipeline for network calls,
            payment handling, and any external integrations.
        planner: LLM-backed planner used to decide which discovery URLs to probe,
            what to fetch, and how to proceed when a paywall is encountered.
    """

    def __init__(self) -> None:
        """
        Initialize the executor with its required dependencies.

        This constructs:
        - `PaywallService()` for integration and transport operations.
        - `PaywallPlanner(OpenAIClient())` for model-driven planning.

        Notes:
            Dependency construction happens eagerly here. If you need to inject
            mocks or alternate implementations, refactor to accept parameters.
        """
        self.service = PaywallService()
        self.planner = PaywallPlanner(OpenAIClient())

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Execute a single agent request.

        This method attempts to extract a structured payload from the incoming
        request in the following order:

        1) If the user input is a string that *looks like JSON* (starts with `{` or `[`),
           try to parse it via `json.loads`.
        2) If parsing fails (or user input is empty), scan `context.message.parts` for a
           part with `data` that is a non-empty dict and use it.
        3) If no payload can be found, fall back to a default minimal payload.

        After normalizing the payload, the executor ensures there is an active task:
        - Uses `context.current_task` when present (e.g., resumed tasks).
        - Otherwise creates a new task via `new_task(context.message)`.

        The task metadata is populated for basic observability:
        - agent_name
        - UTC timestamp (ISO 8601)

        Finally, the method enqueues the task event and runs the `PaywallPipeline`.

        Args:
            context: A2A request context containing the incoming message, task, and
                helper methods such as `get_user_input()`.
            event_queue: Event queue used to publish task lifecycle and progress
                events back to the caller.

        Returns:
            None.

        Raises:
            Exception: Propagates unexpected errors from task creation, event
                enqueueing, or pipeline execution.

        Example:
            The executor is typically invoked by the A2A server framework rather
            than called directly, but conceptually:

            >>> await executor.execute(context, event_queue)
        """
        raw: str = context.get_user_input() or ""
        payload: Dict[str, Any] = {}

        # 1) Best-effort parse if the user input looks like JSON.
        if isinstance(raw, str) and raw.strip().startswith(("{", "[")):
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {}

        # 2) Fallback: pull structured data from message parts.
        if not payload and getattr(context.message, "parts", None):
            for part in context.message.parts:
                data: Optional[Any] = getattr(part, "data", None)
                if isinstance(data, dict) and data:
                    payload = data
                    break

        # 3) Final fallback: use a default query so the pipeline can proceed.
        if not payload:
            payload = {"query": "discover and fetch paywalled resource"}

        # Create or reuse a task associated with this request.
        task = context.current_task or new_task(context.message)
        task.metadata = {
            "agent_name": "paywall-agent",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Publish the initial task event so clients can track progress.
        await event_queue.enqueue_event(task)

        # Orchestrate the end-to-end discovery + payment flow.
        pipeline = PaywallPipeline(self.service, self.planner, event_queue, task)
        await pipeline.run(payload)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Cancel an in-flight execution.

        The current implementation is a no-op and returns immediately.

        Args:
            context: A2A request context for the task being cancelled.
            event_queue: Event queue that could be used to emit cancellation events.

        Returns:
            None.

        Notes:
            If you need cancellation support, consider:
            - marking the task as cancelled in the task store
            - emitting a cancellation event
            - ensuring `PaywallPipeline.run()` cooperates with cancellation
              (e.g., by checking task state or catching `asyncio.CancelledError`)
        """
        return
