"""Declared multi-agent delegation through the Kimss gateway.

Requires a Kimss API key. The parent hop mints child lineage headers
(Run-Id, Depth, Parent-Span, Span-Id, Lineage); Agent.delegate() consumes
that mint. If you call delegate() before any parent run, Forge performs a
short parent hop automatically.

  set KIMSS_API_KEY=kimss_...
  set KIMSS_AGENT_ID=orchestrator
  python examples/05_delegation.py

Inspect the run tree in the product at /app/runs (or run a demo swarm there
without writing any client code).
"""

from __future__ import annotations

import os

from kimss_forge import Agent

root = Agent(
    model=os.environ.get("KIMSS_MODEL", "custom:kimss-gpt-5-3"),
    instructions="You are an orchestrator. Delegate research; do not invent facts.",
    gateway="kimss",
    agent_id=os.environ.get("KIMSS_AGENT_ID", "orchestrator"),
)

if __name__ == "__main__":
    # Parent hop signs the next child identity (HMAC bound to Depth/Parent/Span).
    print(root.run("Plan a one-step research handoff; keep the plan under 40 words."))
    researcher = root.delegate(
        agent_id="researcher",
        instructions="Summarize only from tools or provided context. Be brief.",
        mint_if_needed=False,
    )
    print(researcher.run("List two risks of unbounded agent fan-out."))
