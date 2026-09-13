"""Optional MCP tool loading (install with ``pip install 'kimss-forge[mcp]'``)."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional

from .tools import Tool


def mcp_tools_from_stdio(
    command: str,
    args: Optional[List[str]] = None,
    *,
    env: Optional[Dict[str, str]] = None,
) -> List[Tool]:
    """
    Connect to an MCP server over stdio and wrap its tools as harness Tools.

    Requires the optional ``mcp`` extra. Tools execute via a fresh short-lived
    session per call (simple; suitable for demos and scripts).
    """
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
    except ImportError as exc:
        raise ImportError(
            "MCP support requires: pip install 'kimss-forge[mcp]'"
        ) from exc

    server = StdioServerParameters(command=command, args=args or [], env=env)

    async def _list() -> List[Dict[str, Any]]:
        async with stdio_client(server) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                listed = await session.list_tools()
                return [
                    {
                        "name": t.name,
                        "description": (t.description or t.name),
                        "inputSchema": getattr(t, "inputSchema", None) or {},
                    }
                    for t in (listed.tools or [])
                ]

    specs = asyncio.run(_list())
    out: List[Tool] = []

    for spec in specs:
        name = str(spec["name"])
        description = str(spec["description"])
        parameters = spec.get("inputSchema") or {
            "type": "object",
            "properties": {},
        }

        def _make_fn(tool_name: str):
            def _fn(**kwargs: Any) -> str:
                async def _call() -> str:
                    async with stdio_client(server) as (read, write):
                        async with ClientSession(read, write) as session:
                            await session.initialize()
                            result = await session.call_tool(tool_name, arguments=kwargs)
                            parts = []
                            for block in getattr(result, "content", None) or []:
                                text = getattr(block, "text", None)
                                if text is not None:
                                    parts.append(text)
                                else:
                                    parts.append(str(block))
                            return "\n".join(parts) if parts else json.dumps(
                                {"ok": True}, default=str
                            )

                return asyncio.run(_call())

            _fn.__name__ = tool_name
            _fn.__doc__ = description
            return _fn

        out.append(
            Tool(
                name=name,
                description=description,
                parameters=parameters if isinstance(parameters, dict) else {
                    "type": "object",
                    "properties": {},
                },
                fn=_make_fn(name),
            )
        )
    return out
