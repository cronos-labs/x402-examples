"""
agent/service.py

Service layer for discovering agents and fetching X402 paywalled resources.

This module defines `PaywallService`, which encapsulates the I/O-heavy operations
used by the Paywall Agent pipeline:

- Discovering AgentCards from discovery URLs.
- Validating and applying a planner "choice" (agentIndex/resourceIndex) to select
  a concrete paywalled resource.
- Fetching a protected resource, handling the X402 paywall flow:
    1) Attempt GET on resource URL
    2) If HTTP 402, parse the payment challenge ("accepts")
    3) Generate a signed payment header (EIP-3009 / Cronos facilitator)
    4) POST settlement to the resource's settlement endpoint
    5) Retry GET with `x-payment-id` header to retrieve the paid content

It also provides formatting utilities for returning a human-readable result.

Error handling:
- Methods are wrapped with `@handle_errors`, which converts thrown exceptions into
  standardized return values and optionally logs them.
- `generate_payment_header()` is configured to re-raise config errors to ensure
  missing credentials fail loudly and early.

Constants:
- `X402_PROTOCOL`: expected paywall protocol identifier ("x402")
- `X_PAYMENT_ID_HEADER`: header required for post-settlement retries ("x-payment-id")
- `DEFAULT_SETTLEMENT_PATH`: fallback settlement endpoint ("/api/pay")
"""

import os
import time
from typing import Any, Dict, List, Optional

import httpx
from eth_account import Account

from .lib.a2a.discovery import fetch_agent_card
from .lib.errors.app_error import ConfigError, NetworkError, ValidationError
from .lib.errors.decorators import handle_errors

from crypto_com_facilitator_client import Facilitator, CronosNetwork


X402_PROTOCOL = "x402"
"""
Identifier for X402 paywall protocol challenges.

Used to validate that a selected resource is compatible with this agent's
payment flow.
"""

X_PAYMENT_ID_HEADER = "x-payment-id"
"""
Header name used when retrying a protected resource request after settlement.

The settlement response yields (or implies) a `paymentId`, and the protected
resource is then retrieved by retrying with this header set.
"""

DEFAULT_SETTLEMENT_PATH = "/api/pay"
"""Default settlement endpoint path used when the AgentCard does not specify one."""


class PaywallService:
    """
    Service layer for paywall agent discovery, validation, and X402 fetch/payment flow.

    This class is used by `PaywallPipeline` to perform network requests and the
    X402 settlement process. It is intentionally focused on concrete operations
    and delegates planning decisions to higher layers.

    Notes:
        - Network calls are performed with `httpx.AsyncClient`.
        - Signing uses `eth_account.Account` built from the `X402_PRIVATE_KEY`
          environment variable.
        - Facilitator integration is performed via `x402.src.facilitator_client`.
    """

    @handle_errors(default_return=[], log=True, reraise=False)
    async def discover_agents(self, urls: list[str]) -> list[dict]:
        """
        Discover candidate agents by fetching AgentCards from discovery URLs.

        For each base URL, this method attempts to fetch an AgentCard and, if successful,
        normalizes it into a lightweight agent record:

            {
              "name": <card.name or "unknown">,
              "baseUrl": <card.url or base, without trailing "/">,
              "card": <raw card dict>
            }

        Args:
            urls: List of discovery base URLs. Each is passed to `fetch_agent_card()`.

        Returns:
            A list of discovered agent records. Returns an empty list if none are found
            or if errors occur (errors are handled by `@handle_errors`).

        Example:
            >>> agents = await service.discover_agents(["http://localhost:8787"])
            >>> print(agents[0]["name"], agents[0]["baseUrl"])
        """
        agents: list[dict] = []
        for base in urls:
            card = await fetch_agent_card(base)
            if card:
                agents.append(
                    {
                        "name": card.get("name", "unknown"),
                        "baseUrl": (card.get("url") or base).rstrip("/"),
                        "card": card,
                    }
                )
        return agents

    @handle_errors(default_return=None, log=True, reraise=False)
    def apply_choice(self, agents: List[dict], choice: dict) -> Optional[dict]:
        """
        Apply a planner choice to the discovered agents and select a paywalled resource.

        The planner is expected to return a structure containing indices:
        - agentIndex: which agent in `agents` to use
        - resourceIndex: which resource in the agent's AgentCard `resources` list to use

        This method validates:
        - indices exist and are integers
        - indices are within bounds
        - the selected resource's paywall protocol is "x402"

        On success, returns a copy of the chosen agent record with an added `resource`
        key containing the selected resource dictionary.

        Args:
            agents: List of agent records produced by `discover_agents()`.
            choice: Planner output containing `agentIndex` and `resourceIndex`.

        Returns:
            The selected target dict including `resource`, or `None` if an error occurs
            (errors are handled by `@handle_errors`).

        Raises:
            ValidationError: When indices are missing/invalid/out-of-range, or when the
                chosen resource is not an X402 paywalled resource. (These are captured
                by `@handle_errors` unless re-raised.)

        Example:
            >>> target = service.apply_choice(agents, {"agentIndex": 0, "resourceIndex": 1})
            >>> print(target["resource"]["url"])
        """
        try:
            ai = int(choice["agentIndex"])
            ri = int(choice["resourceIndex"])
        except Exception:
            raise ValidationError(
                "Choice missing/invalid indices", context={"choice": choice}
            )

        if ai < 0 or ai >= len(agents):
            raise ValidationError("agentIndex out of range", context={"agentIndex": ai})

        agent = agents[ai]
        card = agent.get("card", {}) or {}
        resources = card.get("resources", []) or []

        if ri < 0 or ri >= len(resources):
            raise ValidationError(
                "resourceIndex out of range", context={"resourceIndex": ri}
            )

        resource = resources[ri]
        if (resource.get("paywall") or {}).get("protocol") != X402_PROTOCOL:
            raise ValidationError(
                "Selected resource is not x402", context={"resource": resource}
            )

        out = dict(agent)
        out["resource"] = resource
        return out

    @handle_errors(
        default_return={"ok": False, "error": "unexpected_exception"},
        log=True,
        reraise=False,
    )
    async def fetch_resource(self, target: dict) -> dict:
        """
        Fetch a protected resource, performing X402 settlement if required.

        This method implements the X402 access flow:

        1) Resolve full `resource_url` from the target's `baseUrl` and resource `url`.
        2) Determine settlement path:
           - uses `resource.paywall.settlement` if present
           - falls back to `DEFAULT_SETTLEMENT_PATH`
        3) GET the resource:
           - If 200: return success with `paid=False`
           - If not 402: raise `NetworkError`
        4) If 402:
           - Parse JSON challenge and take the first entry of `challenge.accepts`
           - Extract `paymentId` from `accepts0.extra.paymentId`
           - Generate a signed payment header for the accept terms
           - POST to the settlement endpoint with:
               {"paymentId", "paymentHeader", "paymentRequirements"}
           - Retry GET with header `x-payment-id: <paymentId>`
           - Return success with `paid=True` and include settlement + data payloads

        Args:
            target: Target dict returned by `apply_choice()`, containing:
                - baseUrl: agent base URL
                - resource: selected resource dict from AgentCard

        Returns:
            A result dict with at minimum:
              - ok: bool
              - paid: bool (when ok=True)
              - data: parsed JSON response (when ok=True)

            On handled errors, returns:
              {"ok": False, "error": "..."} (as configured by `@handle_errors`).

        Raises:
            NetworkError: For unexpected HTTP statuses or failed settlement/retry.
            ValidationError: For malformed 402 challenge data.
            Exception: Other unexpected errors (captured by `@handle_errors`).

        Example:
            >>> result = await service.fetch_resource(target)
            >>> if result["ok"] and result["paid"]:
            ...     print("Paid access:", result["paymentId"])
        """
        base = target["baseUrl"].rstrip("/")
        resource = target["resource"]

        resource_url = resource["url"]
        if resource_url.startswith("/"):
            resource_url = base + resource_url

        settlement = (resource.get("paywall") or {}).get(
            "settlement", DEFAULT_SETTLEMENT_PATH
        )
        if not settlement.startswith("/"):
            settlement = "/" + settlement
        pay_endpoint = base + settlement

        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.get(resource_url)

            if res.status_code == 200:
                return {"ok": True, "paid": False, "data": res.json()}

            if res.status_code != 402:
                raise NetworkError(
                    "Unexpected status when fetching resource",
                    context={"status": res.status_code, "body": res.text[:400]},
                )

            challenge = res.json()
            accepts0 = (challenge.get("accepts") or [None])[0]
            if not accepts0:
                raise ValidationError(
                    "Invalid 402 challenge: no accepts",
                    context={"challenge": challenge},
                )

            payment_id = (accepts0.get("extra") or {}).get("paymentId")
            if not payment_id:
                raise ValidationError(
                    "Invalid 402 challenge: missing paymentId",
                    context={"accepts0": accepts0},
                )

            payment_header = await self.generate_payment_header(accepts0)

            pay_body = {
                "paymentId": payment_id,
                "paymentHeader": payment_header,
                "paymentRequirements": accepts0,
            }

            pay_res = await client.post(pay_endpoint, json=pay_body)
            if pay_res.status_code >= 400:
                try:
                    details = pay_res.json()
                except Exception:
                    details = {"body": pay_res.text[:400]}
                raise NetworkError("Settlement failed", context={"details": details})

            retry = await client.get(
                resource_url, headers={X_PAYMENT_ID_HEADER: payment_id}
            )
            if retry.status_code != 200:
                raise NetworkError(
                    "Retry after settlement failed",
                    context={"status": retry.status_code, "body": retry.text[:400]},
                )

            return {
                "ok": True,
                "paid": True,
                "paymentId": payment_id,
                "pay": pay_res.json(),
                "data": retry.json(),
            }

    @handle_errors(default_return="", log=True, reraise=True)
    async def generate_payment_header(self, accepts0: dict) -> str:
        """
        Generate a signed payment header for a given X402 "accept" requirement.

        This method reads a private key from the environment and produces a
        facilitator-compatible payment header, using the accept's payment fields:

        - payTo: recipient address
        - maxAmountRequired: amount in base units (string)
        - maxTimeoutSeconds: used to compute `valid_before`

        Configuration:
            - Requires `X402_PRIVATE_KEY` environment variable to be set.
            - Uses `CronosNetwork.CronosTestnet` by default (adjust for prod).

        Behavior:
            - If the facilitator client returns an awaitable, this method awaits it.
              Otherwise, returns it directly. This accommodates both sync/async
              facilitator implementations.

        Args:
            accepts0: First element of a 402 challenge's `accepts` list. Expected to
                include `payTo`, `maxAmountRequired`, and optionally `maxTimeoutSeconds`.

        Returns:
            A Base64-encoded payment header string.

        Raises:
            ConfigError: If `X402_PRIVATE_KEY` is not set. (Re-raised due to decorator config.)
            Exception: Unexpected errors from signing or facilitator interaction may be
                re-raised depending on `handle_errors` behavior.

        Example:
            >>> header = await service.generate_payment_header(accepts0)
            >>> assert isinstance(header, str) and header
        """
        private_key = os.getenv("X402_PRIVATE_KEY")
        if not private_key:
            raise ConfigError("X402_PRIVATE_KEY is not set")

        acct = Account.from_key(private_key)
        valid_before = int(time.time()) + int(accepts0.get("maxTimeoutSeconds", 300))

        fac = Facilitator(network=CronosNetwork.CronosTestnet)

        maybe = fac.generate_payment_header(
            to=accepts0["payTo"],
            value=accepts0["maxAmountRequired"],
            signer=acct,
            valid_before=valid_before,
            valid_after=0,
        )

        if hasattr(maybe, "__await__"):
            return await maybe
        return maybe

    def format_result(self, result: dict) -> str:
        """
        Format a fetch result into a human-readable string.

        The formatted output includes whether payment was required and the paymentId
        (when present), followed by a pretty-ish representation of the returned data.

        Args:
            result: Result dict produced by `fetch_resource()`.

        Returns:
            A formatted string suitable for emitting as an A2A text artifact.

        Example:
            >>> text = service.format_result({"paid": True, "paymentId": "abc", "data": {"x": 1}})
            >>> print(text)
            paid=True paymentId=abc
            <blank line>
            {'x': 1}
        """
        paid = result.get("paid")
        pid = result.get("paymentId", "—")
        return f"paid={paid} paymentId={pid}\n\n{result.get('data')}"
