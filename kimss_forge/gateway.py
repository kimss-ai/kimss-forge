"""Kimss AI Gateway connect helpers (one-line production upgrade)."""

from __future__ import annotations

import os
from typing import Dict, Optional

KIMSS_GATEWAY_BASE_URL = "https://api.kimss.ai/v1"
KIMSS_GATEWAY_HOST = "https://api.kimss.ai"

# Header names match kimss_sdk / Invisible Proxy conventions.
HEADER_AGENT_ID = "X-Kimss-Agent-Id"
HEADER_AGENT_NAME = "X-Kimss-Agent-Name"
HEADER_CLIENT = "X-Kimss-Client"
HEADER_RUN_ID = "X-Kimss-Run-Id"
HEADER_DEPTH = "X-Kimss-Depth"
HEADER_PARENT_SPAN = "X-Kimss-Parent-Span"
HEADER_SPAN_ID = "X-Kimss-Span-Id"
HEADER_LINEAGE = "X-Kimss-Lineage"
CLIENT_KIMSS_FORGE = "kimss-forge"


def gateway_headers(
    *,
    agent_id: str,
    agent_name: Optional[str] = None,
    client: str = CLIENT_KIMSS_FORGE,
    run_id: Optional[str] = None,
    depth: Optional[int] = None,
    parent_span: Optional[str] = None,
    span_id: Optional[str] = None,
    lineage: Optional[str] = None,
) -> Dict[str, str]:
    """Return attribution headers for traffic routed through the Kimss gateway."""
    aid = (agent_id or "").strip()
    if not aid:
        raise ValueError("agent_id is required when using the Kimss gateway")
    headers: Dict[str, str] = {
        HEADER_AGENT_ID: aid,
        HEADER_CLIENT: (client or CLIENT_KIMSS_FORGE).strip() or CLIENT_KIMSS_FORGE,
    }
    name = (agent_name or "").strip()
    if name:
        headers[HEADER_AGENT_NAME] = name
    if (run_id or "").strip():
        headers[HEADER_RUN_ID] = str(run_id).strip()
    if depth is not None:
        headers[HEADER_DEPTH] = str(int(depth))
    if (parent_span or "").strip():
        headers[HEADER_PARENT_SPAN] = str(parent_span).strip()
    if (span_id or "").strip():
        headers[HEADER_SPAN_ID] = str(span_id).strip()
    if (lineage or "").strip():
        headers[HEADER_LINEAGE] = str(lineage).strip()
    return headers


def resolve_kimss_workspace_key(explicit: Optional[str] = None) -> str:
    """Resolve workspace key from argument or env (KIMSS_API_KEY / KIMSS_WORKSPACE_KEY)."""
    key = (explicit or "").strip()
    if key:
        return key
    for env_name in ("KIMSS_API_KEY", "KIMSS_WORKSPACE_KEY"):
        val = (os.environ.get(env_name) or "").strip()
        if val:
            return val
    raise ValueError(
        "Kimss workspace key required: pass workspace_key=... or set "
        "KIMSS_API_KEY / KIMSS_WORKSPACE_KEY"
    )


def apply_kimss_gateway(
    *,
    workspace_key: Optional[str] = None,
    agent_id: Optional[str] = None,
    agent_name: Optional[str] = None,
    base_url: Optional[str] = None,
) -> tuple[str, str, Dict[str, str]]:
    """
    Resolve base_url, api_key, and extra headers for Kimss gateway mode.

    Returns (base_url, api_key, extra_headers).
    """
    key = resolve_kimss_workspace_key(workspace_key)
    aid = (agent_id or os.environ.get("KIMSS_AGENT_ID") or "").strip()
    if not aid:
        raise ValueError(
            "agent_id is required for gateway='kimss' "
            "(pass agent_id=... or set KIMSS_AGENT_ID)"
        )
    url = (base_url or KIMSS_GATEWAY_BASE_URL).rstrip("/")
    headers = gateway_headers(agent_id=aid, agent_name=agent_name)
    return url, key, headers
