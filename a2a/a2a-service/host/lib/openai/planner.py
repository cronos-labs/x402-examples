"""
LLM-backed planner for selecting an X402 paywalled resource from discovered agents.

This module defines `PaywallPlanner`, which uses an injected LLM client (see
`lib.openai.client.OpenAIClient`) to choose the most suitable agent+resource
pair for a given user query.

Core behavior:
- Summarizes discovered agents and their resources into a compact, model-friendly
  structure.
- Prompts the LLM to return **ONLY** valid JSON (or `null`) identifying:
    - agentIndex
    - resourceIndex
    - reason (optional/freeform)
- Validates that the LLM response is valid JSON and matches the expected schema.

Error handling:
- Wrapped with `@handle_errors` so failures can be logged and safely converted to
  `None` (unless the decorator configuration is changed).
- Raises `LlmError` for invalid JSON or schema mismatches, enabling consistent
  upstream error reporting.
"""

import json
from typing import Any, Dict, List, Optional

from ..errors.app_error import LlmError
from ..errors.decorators import handle_errors


class PaywallPlanner:
    """
    Planner that selects a target X402 resource using an LLM.

    The planner is responsible for translating:
      - a natural-language `query`
      - a list of discovered agents (with AgentCards)

    ...into a concrete selection that downstream code can apply to fetch a
    paywalled resource.

    The returned selection is an object with at least:
      - agentIndex: index into the `agents` list
      - resourceIndex: index into the chosen agent's `card.resources` list
      - reason: optional explanation for selection (useful for debugging/logs)

    Attributes:
        client: LLM client providing an async `chat(messages) -> str` method.
    """

    def __init__(self, client: Any) -> None:
        """
        Create a new planner.

        Args:
            client: An LLM client instance providing an async `chat()` method
                that accepts OpenAI-style messages and returns a text response.

        Example:
            >>> planner = PaywallPlanner(OpenAIClient())
        """
        self.client = client

    @handle_errors(default_return=None, log=True, reraise=False)
    async def choose_target(
        self,
        query: str,
        agents: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """
        Choose the best agent resource for the provided query.

        This method:
          1) Builds a summarized view of discovered agents/resources for the model.
          2) Prompts the LLM to return ONLY valid JSON (or `null`).
          3) Parses and validates the returned JSON schema.

        The model is instructed to return:
            - `null` if no suitable X402 resource exists
            - otherwise a JSON object with schema:
              {"agentIndex": number, "resourceIndex": number, "reason": string}

        Args:
            query: Natural-language user query describing the desired paywalled resource.
            agents: Discovered agent records (each containing `card` and `baseUrl`),
                typically produced by `PaywallService.discover_agents()`.

        Returns:
            A dict containing the selection (agentIndex/resourceIndex/optional reason),
            or `None` if the model returns `null` or if errors occur and are handled by
            the decorator.

        Raises:
            LlmError: If the model returns invalid JSON or JSON that does not match
                the expected schema. (These are captured by `@handle_errors` unless
                re-raised.)
            Exception: Unexpected failures from the client or parsing (captured by
                `@handle_errors`).

        Example:
            >>> choice = await planner.choose_target(query="get paywalled data", agents=agents)
            >>> if choice:
            ...     print(choice["agentIndex"], choice["resourceIndex"])
        """
        summarized: List[Dict[str, Any]] = []

        for ai, agent in enumerate(agents):
            card = agent.get("card", {}) or {}
            resources = card.get("resources", []) or []

            summarized.append(
                {
                    "agentIndex": ai,
                    "name": card.get("name", agent.get("name", "unknown")),
                    "baseUrl": agent.get("baseUrl"),
                    "resources": [
                        {
                            "resourceIndex": ri,
                            "url": r.get("url"),
                            "description": r.get("description", ""),
                            "paywallProtocol": (r.get("paywall") or {}).get("protocol"),
                        }
                        for ri, r in enumerate(resources)
                    ],
                }
            )

        system = (
            "Select the best agent resource for the user query.\n"
            "Return ONLY valid JSON (no markdown, no prose).\n"
            "If no x402 resource exists, return null.\n"
            'Schema: {"agentIndex": number, "resourceIndex": number, "reason": string}\n'
        )

        payload = {"query": query, "agents": summarized}

        text = await self.client.chat(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(payload)},
            ]
        )

        text = (text or "").strip()
        if text == "null":
            return None

        try:
            obj = json.loads(text)
        except json.JSONDecodeError:
            raise LlmError(
                "Planner returned invalid JSON",
                context={"output": text[:300]},
            )

        if (
            not isinstance(obj, dict)
            or "agentIndex" not in obj
            or "resourceIndex" not in obj
        ):
            raise LlmError(
                "Planner returned JSON but not the expected schema",
                context={"output": obj},
            )

        return obj
