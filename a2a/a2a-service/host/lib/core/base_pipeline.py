"""
Abstract base class for event-driven A2A pipelines.

This module defines `BasePipeline`, a lightweight abstraction that standardizes
how pipelines are structured and executed within an A2A agent runtime.

A pipeline is responsible for orchestrating work across a service layer and
emitting structured A2A events (progress, artifacts, status updates) through
an `EventQueue` tied to a specific `Task`.
"""

from abc import ABC, abstractmethod

from a2a.server.events.event_queue import EventQueue
from a2a.types import Task


class BasePipeline(ABC):
    """
    Foundational structure for event-driven A2A pipelines.

    This base class establishes a common constructor and a required `run()`
    coroutine that concrete pipelines must implement.

    Responsibilities:
        - Hold references to the service layer, event queue, and task context.
        - Provide a consistent entrypoint (`run`) for pipeline execution.
        - Allow higher-level components (executors/agents) to interact with
          pipelines in a uniform way.
    """

    def __init__(self, service, event_queue: EventQueue, task: Task) -> None:
        """
        Initialize the pipeline with core runtime dependencies.

        Args:
            service: Service instance used by the pipeline to perform domain-
                specific operations (network calls, persistence, etc.).
            event_queue: Active A2A `EventQueue` used to emit task events.
            task: Current A2A `Task` object containing IDs and metadata.

        Notes:
            This constructor performs no validation and assumes the caller
            provides compatible objects.
        """
        self.service = service
        self.event_queue = event_queue
        self.task = task

    @abstractmethod
    async def run(self, query: str) -> None:
        """
        Execute the main orchestration logic for the pipeline.

        Concrete implementations must define how a user query or command is
        processed, including:
          - Calling into the service layer
          - Emitting progress, artifact, and status events
          - Handling success, failure, or cancellation conditions

        Args:
            query: The user query or command initiating the pipeline.

        Returns:
            None.

        Raises:
            NotImplementedError: If the subclass does not implement this method.

        Example:
            >>> class MyPipeline(BasePipeline):
            ...     async def run(self, query: str) -> None:
            ...         await do_work(query)
            ...         await emit_events()
        """
        raise NotImplementedError
