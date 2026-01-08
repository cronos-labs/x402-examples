"""
Async OpenAI client wrapper for LLM-backed planning and reasoning.

This module defines `OpenAIClient`, a thin abstraction over the official
`openai.AsyncOpenAI` client. It centralizes:

- Model selection (via constructor argument or environment variable)
- API key validation
- A simplified `chat()` interface for sending chat-style prompts and
  retrieving the model’s textual response

The client is designed to be used by higher-level components (e.g. planners)
that want a minimal, opinionated interface rather than direct access to the
OpenAI SDK.
"""

import os
from typing import Dict, List, Optional, Union

from openai import AsyncOpenAI


class OpenAIClient:
    """
    Asynchronous OpenAI chat client with minimal configuration.

    This class wraps `AsyncOpenAI` and exposes a single `chat()` method for
    sending chat-completion requests. It enforces the presence of an API key
    and applies a default temperature suitable for planning and decision-making.

    Configuration:
        - `OPENAI_API_KEY` (required): API key used to authenticate requests.
        - `LLM_MODEL` (optional): Default model name. Falls back to
          `"gpt-4o-mini"` if not set.

    Attributes:
        model: Default model name used for chat completions.
        client: Underlying `AsyncOpenAI` client instance.
    """

    def __init__(self, model: Optional[str] = None):
        """
        Initialize the OpenAI client.

        Args:
            model: Optional model name to use for chat completions. If not
                provided, the value of the `LLM_MODEL` environment variable
                is used, falling back to `"gpt-4o-mini"`.

        Raises:
            RuntimeError: If the `OPENAI_API_KEY` environment variable is not set.

        Example:
            >>> client = OpenAIClient()
            >>> client = OpenAIClient(model="gpt-4.1-mini")
        """
        self.model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")

        self.client = AsyncOpenAI(api_key=api_key)

    async def chat(
        self,
        messages: List[Dict[str, Union[str, Dict]]],
        model: Optional[str] = None,
    ) -> str:
        """
        Send a chat-completion request and return the model's response text.

        This method forwards the provided messages to the OpenAI Chat Completions
        API and returns the content of the first choice as a stripped string.

        Behavior:
            - Uses the provided `model` argument if supplied.
            - Otherwise falls back to the client's default model.
            - Applies a low temperature (0.2) for more deterministic outputs.

        Args:
            messages: List of message objects in OpenAI chat format, e.g.:
                [
                  {"role": "system", "content": "You are a planner."},
                  {"role": "user", "content": "Choose the best agent."}
                ]
            model: Optional model override for this request.

        Returns:
            The model's response text. If the response content is empty or null,
            an empty string is returned.

        Raises:
            Exception: Propagates errors from the OpenAI SDK (network errors,
                authentication issues, invalid requests, etc.).

        Example:
            >>> text = await client.chat([
            ...     {"role": "user", "content": "Summarize this task."}
            ... ])
            >>> print(text)
        """
        response = await self.client.chat.completions.create(
            model=model or self.model,
            messages=messages,
            temperature=0.2,
        )
        return (response.choices[0].message.content or "").strip()
