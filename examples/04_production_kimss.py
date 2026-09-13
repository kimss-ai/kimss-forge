"""Production mode — one-line Kimss gateway connect.

When your org needs identity, kill switch, metering, and audit, point the
same Agent at the Kimss AI Gateway. Vault a model first at https://kimss.ai

  set KIMSS_API_KEY=kimss_...
  set KIMSS_AGENT_ID=my_fleet_agent
  python examples/04_production_kimss.py
"""

from __future__ import annotations

import os

from kimss_forge import Agent

# One line: gateway="kimss" → base_url=https://api.kimss.ai/v1 + X-Kimss-Agent-Id
agent = Agent(
    model=os.environ.get("KIMSS_MODEL", "custom:kimss-gpt-5-3"),
    instructions="You are a production assistant. Be brief.",
    gateway="kimss",
    agent_id=os.environ.get("KIMSS_AGENT_ID", "harness_demo"),
    # workspace_key from KIMSS_API_KEY / KIMSS_WORKSPACE_KEY if omitted
)

if __name__ == "__main__":
    print(agent.run("Confirm you can see this governed request."))
