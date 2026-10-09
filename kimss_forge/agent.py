"""High-level Agent API — local by default, Kimss gateway with one line."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Sequence, Union

from .client import ChatClient
from .gateway import apply_kimss_gateway, gateway_headers
from .loop import AgentResult, run_loop
from .run_context import (
    RunContext,
    ensure_root_context,
    get_pending_child,
    get_run_context,
    set_run_context,
    take_pending_child,
)
from .tools import Tool, coerce_tools

ToolLike = Union[Tool, Any]


class Agent:
    """
    Standalone agent harness.

    **Local (free, no Kimss account)::**

        agent = Agent(model="gpt-4o-mini", instructions="Be brief.", tools=[...])
        print(agent.run("Hello"))

    **Production via Kimss gateway (one line)::**

        agent = Agent(
            model="custom:your-vaulted-model",
            instructions="Be brief.",
            gateway="kimss",
            agent_id="my_agent",
            workspace_key="kimss_...",
        )

    **Declared child hop (depth+1)::**

        # Parent hop mints the child's HMAC identity in response headers.
        orchestrator.run("Plan the research")
        child = orchestrator.delegate(agent_id="researcher", model="custom:m")
        child.run("Summarize the ticket")
    """

    def __init__(
        self,
        *,
        model: str,
        instructions: str = "You are a helpful assistant.",
        tools: Optional[Sequence[ToolLike]] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        gateway: Optional[str] = None,
        workspace_key: Optional[str] = None,
        agent_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        max_hops: int = 8,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        timeout: float = 120.0,
        run_context: Optional[RunContext] = None,
    ) -> None:
        self.model = (model or "").strip()
        if not self.model:
            raise ValueError("model is required")
        self.instructions = instructions or ""
        self.tools = coerce_tools(list(tools) if tools else [])
        self.max_hops = max_hops
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._run_context = run_context

        gw = (gateway or "").strip().lower()
        extra_headers: Dict[str, str] = {}
        resolved_key = api_key
        resolved_base = base_url
        self._gateway_connected = False

        if gw in ("kimss", "kimss-ai", "true"):
            resolved_base, resolved_key, extra_headers = apply_kimss_gateway(
                workspace_key=workspace_key or api_key,
                agent_id=agent_id,
                agent_name=agent_name,
                base_url=base_url,
            )
            self._gateway_connected = True
        elif gw:
            raise ValueError(f"Unsupported gateway={gateway!r}; use None or 'kimss'")

        if resolved_key is None and not gw:
            resolved_key = os.environ.get("OPENAI_API_KEY")
        if resolved_base is None and not gw:
            resolved_base = os.environ.get("OPENAI_BASE_URL")

        self.agent_id = (agent_id or "").strip() or None
        self.agent_name = (agent_name or "").strip() or None
        self._workspace_key = workspace_key or api_key
        self._gateway = gw if self._gateway_connected else None
        self._base_url = resolved_base
        self._api_key = resolved_key
        self._timeout = timeout

        if self._gateway_connected:
            ctx = run_context or get_run_context() or ensure_root_context()
            self._run_context = ctx
            set_run_context(ctx)
            lineage_headers = gateway_headers(
                agent_id=self.agent_id or "agent",
                agent_name=self.agent_name,
                run_id=ctx.run_id,
                depth=ctx.depth,
                parent_span=ctx.parent_span,
                span_id=ctx.span_id,
                lineage=ctx.lineage,
            )
            extra_headers.update(lineage_headers)

        self._client = ChatClient(
            api_key=resolved_key,
            base_url=resolved_base,
            default_headers=extra_headers,
            timeout=timeout,
        )

    def _consume_minted_child(self) -> Optional[RunContext]:
        """Prefer client-stashed mint, then contextvar pending child."""
        pending = getattr(self._client, "pending_child", None)
        if pending is not None:
            self._client.pending_child = None
            take_pending_child()  # clear contextvar twin if present
            return pending
        return take_pending_child() or get_pending_child()

    def delegate(
        self,
        *,
        agent_id: str,
        model: Optional[str] = None,
        instructions: Optional[str] = None,
        tools: Optional[Sequence[ToolLike]] = None,
        agent_name: Optional[str] = None,
        lineage: Optional[str] = None,
        mint_if_needed: bool = True,
    ) -> "Agent":
        """Spawn a child agent using the gateway-minted next-hop identity.

        The parent must complete at least one ``run()`` so the gateway can sign
        ``X-Kimss-Lineage`` for depth>0. When ``mint_if_needed`` is True (default),
        ``delegate`` performs a short parent hop automatically if no mint exists yet.
        """
        if not self._gateway_connected:
            raise ValueError("delegate() requires gateway='kimss' so lineage is enforced")
        child_ctx = self._consume_minted_child()
        if child_ctx is None and mint_if_needed:
            # One declared parent hop mints the child HMAC (Depth/Parent/Span/Lineage).
            self.run("Prepare to delegate the next step to a child agent.")
            child_ctx = self._consume_minted_child()
        if child_ctx is None:
            raise RuntimeError(
                "Gateway did not mint child lineage headers. "
                "Call parent.run(...) once before delegate(), or check gateway connectivity."
            )
        if lineage:
            child_ctx = child_ctx.with_lineage(lineage)
        return Agent(
            model=model or self.model,
            instructions=instructions if instructions is not None else self.instructions,
            tools=tools if tools is not None else self.tools,
            api_key=self._api_key,
            base_url=self._base_url,
            gateway=self._gateway or "kimss",
            workspace_key=self._workspace_key,
            agent_id=agent_id,
            agent_name=agent_name or agent_id,
            max_hops=self.max_hops,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            timeout=self._timeout,
            run_context=child_ctx,
        )

    def run(
        self,
        user_text: str,
        *,
        messages: Optional[List[Dict[str, Any]]] = None,
    ) -> AgentResult:
        """Run one user turn (multi-hop tool loop). Returns AgentResult (str-compatible)."""
        if self._run_context is not None:
            set_run_context(self._run_context)
        history: List[Dict[str, Any]] = []
        if self.instructions.strip():
            history.append({"role": "system", "content": self.instructions})
        if messages:
            history.extend(messages)
        history.append({"role": "user", "content": user_text})
        return run_loop(
            client=self._client,
            model=self.model,
            messages=history,
            tools=self.tools,
            max_hops=self.max_hops,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            gateway_connected=self._gateway_connected,
        )
