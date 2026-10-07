"""LangGraph-style header propagation for declared Kimss runs.

Kimss Forge automates this via Agent.delegate(). This example shows the
manual pattern for frameworks that use the OpenAI client directly.

  set KIMSS_API_KEY=kimss_...
  python examples/06_langgraph_delegation.py
"""

from __future__ import annotations

import os

from openai import OpenAI

from kimss_forge.gateway import gateway_headers
from kimss_forge.run_context import ensure_root_context

BASE = os.environ.get("KIMSS_BASE_URL", "https://api.kimss.ai/v1")
KEY = os.environ.get("KIMSS_API_KEY") or os.environ.get("KIMSS_WORKSPACE_KEY") or ""


def main() -> None:
    if not KEY:
        raise SystemExit("Set KIMSS_API_KEY first")

    ctx = ensure_root_context()
    client = OpenAI(
        base_url=BASE,
        api_key=KEY,
        default_headers=gateway_headers(
            agent_id="langgraph-orchestrator",
            run_id=ctx.run_id,
            depth=ctx.depth,
            parent_span=ctx.parent_span,
            span_id=ctx.span_id,
            lineage=ctx.lineage,
        ),
    )
    r = client.chat.completions.create(
        model=os.environ.get("KIMSS_MODEL", "gpt-4.1-mini"),
        messages=[{"role": "user", "content": "Propose a two-step research plan."}],
    )
    print(r.choices[0].message.content)

    # Next hop: read child headers from the HTTP response (Forge client does this).
    # With the raw OpenAI SDK, capture response.headers from a lower-level call
    # or use kimss_forge.ChatClient which applies_response_lineage automatically.
    print("Run id for /app/runs:", ctx.run_id)


if __name__ == "__main__":
    main()
