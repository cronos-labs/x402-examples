"""
Convenience helpers for emitting structured A2A task events.

This module provides a small set of async helper functions that wrap common
A2A event patterns—clarification requests, progress updates, successful
completion, failure, and cancellation—into reusable utilities.

Each helper:
- Enqueues one or more A2A events onto the provided `event_queue`
- Updates task state consistently (`working`, `completed`, `failed`, `cancelled`)
- Ensures the correct `final` flag behavior so conversations either remain open
  or are cleanly finalized

These helpers are intentionally thin and declarative, and are typically called
from pipelines or executors rather than directly by business logic.
"""

from a2a.types import (
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from a2a.utils import new_agent_text_message, new_text_artifact


async def clarify(event_queue, task, question: str) -> None:
    """
    Request clarification from the user when additional input is required.

    This helper publishes a clarification artifact (non-append) containing the
    provided question text, then updates the task status to `working` so the
    conversation remains open and the user can respond.

    Args:
        event_queue: Active A2A event queue used to enqueue outgoing events.
        task: Current task context containing task and context identifiers.
        question: Clarification question text to present to the user.

    Returns:
        None.

    Example:
        >>> await clarify(event_queue, task, "Which resource should I fetch?")
    """
    await event_queue.enqueue_event(
        TaskArtifactUpdateEvent(
            append=False,
            context_id=task.context_id,
            task_id=task.id,
            last_chunk=True,
            artifact=new_text_artifact(
                name="clarification_needed",
                text=question,
            ),
        )
    )
    await event_queue.enqueue_event(
        TaskStatusUpdateEvent(
            status=TaskStatus(state=TaskState.working),
            final=False,  # keep the session open for user input
            context_id=task.context_id,
            task_id=task.id,
        )
    )


async def progress(event_queue, task, text: str) -> None:
    """
    Emit a non-final progress update indicating that work is ongoing.

    This helper sends a `working` task status update with a textual message,
    allowing clients to display intermediate progress while keeping the task
    session active.

    Args:
        event_queue: Event queue to enqueue progress updates.
        task: Current task context object.
        text: Human-readable progress message.

    Returns:
        None.

    Example:
        >>> await progress(event_queue, task, "Discovering agents…")
    """
    await event_queue.enqueue_event(
        TaskStatusUpdateEvent(
            status=TaskStatus(
                state=TaskState.working,
                message=new_agent_text_message(text, task.context_id, task.id),
            ),
            final=False,
            context_id=task.context_id,
            task_id=task.id,
        )
    )


async def finish(event_queue, task, text: str, name: str = "result") -> None:
    """
    Signal successful task completion and emit the final result artifact.

    This helper publishes a final artifact containing the result payload, then
    marks the task state as `completed` and closes the event stream.

    Args:
        event_queue: Event queue handling outgoing task events.
        task: Task instance to mark as completed.
        text: Final result content (text or serialized JSON).
        name: Artifact name/label for the result (default: "result").

    Returns:
        None.

    Example:
        >>> await finish(event_queue, task, "Fetched resource successfully")
    """
    await event_queue.enqueue_event(
        TaskArtifactUpdateEvent(
            append=False,
            context_id=task.context_id,
            task_id=task.id,
            last_chunk=True,
            artifact=new_text_artifact(name=name, text=text),
        )
    )
    await event_queue.enqueue_event(
        TaskStatusUpdateEvent(
            status=TaskStatus(state=TaskState.completed),
            final=True,
            context_id=task.context_id,
            task_id=task.id,
        )
    )


async def fail(event_queue, task, text: str) -> None:
    """
    Report a structured task failure and finalize the task.

    This helper emits a `failed` task status update with an associated failure
    message and marks the task as final.

    Args:
        event_queue: A2A event queue used to publish failure information.
        task: Task object representing the failed operation.
        text: Failure message describing the error.

    Returns:
        None.

    Example:
        >>> await fail(event_queue, task, "Payment settlement failed")
    """
    await event_queue.enqueue_event(
        TaskStatusUpdateEvent(
            status=TaskStatus(
                state=TaskState.failed,
                message=new_agent_text_message(text, task.context_id, task.id),
            ),
            final=True,
            context_id=task.context_id,
            task_id=task.id,
        )
    )


async def cancel(event_queue, task, text: str = "Task cancelled.") -> None:
    """
    Emit a structured cancellation event for an interrupted or aborted task.

    This helper sends a `cancelled` task status update with an optional message
    and finalizes the task's event stream.

    Args:
        event_queue: A2A event queue used to propagate cancellation.
        task: Task being cancelled.
        text: Optional cancellation message (default: "Task cancelled.").

    Returns:
        None.

    Example:
        >>> await cancel(event_queue, task)
    """
    await event_queue.enqueue_event(
        TaskStatusUpdateEvent(
            status=TaskStatus(
                state=TaskState.cancelled,
                message=new_agent_text_message(text, task.context_id, task.id),
            ),
            final=True,
            context_id=task.context_id,
            task_id=task.id,
        )
    )
