"""
Error-handling decorators for synchronous and asynchronous functions.

This module defines `handle_errors`, a unified decorator that can be applied to
both sync and async functions to provide consistent error handling behavior
across the codebase.

The decorator is designed to work with the application's structured error
hierarchy (`AppError`) while also safely catching unexpected exceptions.
"""

import asyncio
import functools
import logging
from typing import Any, Callable

from .app_error import AppError

logger = logging.getLogger(__name__)


def handle_errors(
    *,
    default_return: Any = None,
    log: bool = True,
    reraise: bool = False,
) -> Callable:
    """
    Decorator factory for unified error handling.

    This decorator can be applied to **both synchronous and asynchronous**
    functions. It intercepts raised exceptions and applies a consistent policy
    for logging, re-raising, or returning a default value.

    Error handling rules:
        - If an `AppError` is raised:
            - Optionally log the error via `AppError.log()`
            - Optionally re-raise the error
            - Otherwise, return `default_return`
        - If any other `Exception` is raised:
            - Optionally log the full stack trace
            - Optionally re-raise the exception
            - Otherwise, return `default_return`

    Args:
        default_return: Value to return if an error is caught and not re-raised.
        log: Whether to log caught exceptions.
        reraise: Whether to re-raise caught exceptions after logging.

    Returns:
        A decorator that wraps the target function with the specified
        error-handling behavior.

    Example:
        >>> @handle_errors(default_return=None, log=True, reraise=False)
        ... async def fetch_data():
        ...     ...
    """

    def decorator(func: Callable) -> Callable:
        """
        Apply error-handling behavior to the target function.

        The decorator automatically detects whether the wrapped function is
        asynchronous or synchronous and applies the appropriate wrapper.
        """

        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                """
                Async wrapper that applies unified error handling.

                Catches `AppError` and generic `Exception` instances according
                to the configuration provided to `handle_errors`.
                """
                try:
                    return await func(*args, **kwargs)
                except AppError as e:
                    if log:
                        e.log()
                    if reraise:
                        raise
                    return default_return
                except Exception as e:
                    if log:
                        logger.exception(f"Unexpected error in {func.__name__}: {e}")
                    if reraise:
                        raise
                    return default_return

            return async_wrapper

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            """
            Sync wrapper that applies unified error handling.

            Catches `AppError` and generic `Exception` instances according
            to the configuration provided to `handle_errors`.
            """
            try:
                return func(*args, **kwargs)
            except AppError as e:
                if log:
                    e.log()
                if reraise:
                    raise
                return default_return
            except Exception as e:
                if log:
                    logger.exception(f"Unexpected error in {func.__name__}: {e}")
                if reraise:
                    raise
                return default_return

        return sync_wrapper

    return decorator
