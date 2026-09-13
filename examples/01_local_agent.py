"""Local agent — no Kimss account required.

Requires OPENAI_API_KEY (or any OpenAI-compatible endpoint via OPENAI_BASE_URL).

  pip install kimss-forge
  python examples/01_local_agent.py
"""

from __future__ import annotations

from kimss_forge import Agent

agent = Agent(
    model="gpt-4o-mini",
    instructions="You are a concise assistant. Reply in one short sentence.",
)

if __name__ == "__main__":
    print(agent.run("What is Kimss in one sentence? (guess from the name)"))
