"""Local agent with a Python tool — still no Kimss account.

  pip install kimss-forge
  python examples/02_tools.py
"""

from __future__ import annotations

from kimss_forge import Agent, tool


@tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


agent = Agent(
    model="gpt-4o-mini",
    instructions="Use tools when helpful. Be brief.",
    tools=[multiply],
)

if __name__ == "__main__":
    print(agent.run("What is 12 times 7?"))
