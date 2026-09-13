"""High-level Agent API — local by default, Kimss gateway with one line."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Sequence, Union

from .client import ChatClient
from .gateway import apply_kimss_gateway
from .loop import AgentResult, run_loop
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
    ) -> None:
        self.model = (model or "").strip()
        if not self.model:
            raise ValueError("model is required")
        self.instructions = instructions or ""
        self.tools = coerce_tools(list(tools) if tools else [])
        self.max_hops = max_hops
        self.max_tokens = max_tokens
        self.temperature = temperature

        gw = (gateway or "").strip().lower()
        extra_headers: Dict[str, str] = {}
        resolved_key = api_key
        resolved_base = base_url

        if gw in ("kimss", "kimss-ai", "true"):
            resolved_base, resolved_key, extra_headers = apply_kimss_gateway(
                workspace_key=workspace_key or api_key,
                agent_id=agent_id,
                agent_name=agent_name,
                base_url=base_url,
            )
        elif gw:
            raise ValueError(f"Unsupported gateway={gateway!r}; use None or 'kimss'")

        if resolved_key is None and not gw:
            resolved_key = os.environ.get("OPENAI_API_KEY")
        if resolved_base is None and not gw:
            resolved_base = os.environ.get("OPENAI_BASE_URL")

        self.agent_id = (agent_id or "").strip() or None
        self._client = ChatClient(
            api_key=resolved_key,
            base_url=resolved_base,
            default_headers=extra_headers,
            timeout=timeout,
        )

    def run(
        self,
        user_text: str,
        *,
        messages: Optional[List[Dict[str, Any]]] = None,
    ) -> AgentResult:
        """Run one user turn (multi-hop tool loop). Returns AgentResult (str-compatible)."""
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
        )
