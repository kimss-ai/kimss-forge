"""Optional MCP tools (requires kimss-forge[mcp]).

Point COMMAND at any MCP stdio server. Example uses a placeholder —
replace with your server command.

  pip install 'kimss-forge[mcp]'
  python examples/03_mcp.py
"""

from __future__ import annotations

import os
import sys

from kimss_forge import Agent
from kimss_forge.mcp import mcp_tools_from_stdio

# Example: npx -y @modelcontextprotocol/server-filesystem /tmp
COMMAND = os.environ.get("MCP_COMMAND", "").strip()
ARGS = [a for a in os.environ.get("MCP_ARGS", "").split(" ") if a]

if __name__ == "__main__":
    if not COMMAND:
        print(
            "Set MCP_COMMAND (and optional MCP_ARGS) to an MCP stdio server, e.g.\n"
            '  set MCP_COMMAND=npx\n'
            '  set MCP_ARGS=-y @modelcontextprotocol/server-everything\n',
            file=sys.stderr,
        )
        sys.exit(1)
    tools = mcp_tools_from_stdio(COMMAND, ARGS or None)
    agent = Agent(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        instructions="Use MCP tools when helpful. Be brief.",
        tools=tools,
    )
    print(agent.run(os.environ.get("PROMPT", "List available tools and say hello.")))
