"""
Abstract base class defining the contract for A2A agent implementations.

This module defines `BaseAgent`, an abstract base class (ABC) that standardizes
the execution model and lifecycle hooks for agents operating in an A2A-style
framework.

All concrete agents must implement the `handle()` coroutine, which processes
a user query and yields structured event dictionaries over time. Optional
lifecycle hooks (`on_start`, `on_finish`) are provided to support setup and
teardown logic around each task execution.
"""

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Optional


class BaseAgent(ABC):
    """
    Abstract interface and lifecycle definition for A2A agents.

    This class establishes:
      - A consistent asynchronous `handle()` interface that all agents must implement.
      - Optional lifecycle hooks (`on_start`, `on_finish`) that can be overridden
        for initialization and cleanup.

    Design contract:
        - `handle()` must be an async generator yielding dictionaries that represent
          structured agent events.
        - Yielded events should include fields such as content, completion state,
          and optional artifacts, depending on the consuming runtime.

    Subclasses:
        Concrete agents must subclass `BaseAgent` and provide an implementation
        of `handle()`.
    """

    @abstractmethod
    async def handle(
        self,
        query: str,
        context_id: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Handle a user query within a given task or session context.

        This coroutine represents the main execution entrypoint for an agent.
        Implementations are expected to:
          - Interpret and process the incoming query.
          - Yield structured event dictionaries incrementally as work progresses.
          - Terminate the generator when the task completes or when user input
            is required to continue.

        Args:
            query: The user's query or command.
            context_id: Identifier for the session or task context.
            metadata: Optional dictionary containing extra contextual data,
                configuration, or hints for execution.

        Yields:
            Structured event dictionaries describing agent output, progress,
            or control signals. The exact schema is defined by the surrounding
            A2A framework.

        Raises:
            NotImplementedError: If a subclass does not implement this method.

        Example:
            >>> class EchoAgent(BaseAgent):
            ...     async def handle(self, query, context_id, metadata=None):
            ...         yield {"text": query, "final": True}
        """
        raise NotImplementedError("Agent subclasses must implement handle().")

    async def on_start(self, context_id: str) -> None:
        """
        Optional lifecycle hook executed before task processing begins.

        Subclasses may override this method to perform setup logic such as:
          - Allocating resources
          - Initializing state
          - Logging task start events

        Args:
            context_id: The session or task identifier.

        Returns:
            None.
        """
        pass

    async def on_finish(self, context_id: str) -> None:
        """
        Optional lifecycle hook executed after task processing completes.

        Subclasses may override this method to perform teardown or post-processing,
        such as:
          - Releasing resources
          - Persisting results
          - Logging completion metrics

        Args:
            context_id: The session or task identifier.

        Returns:
            None.
        """
        pass
