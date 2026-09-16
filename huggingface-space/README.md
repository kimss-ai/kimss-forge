---
title: Kimss Forge
emoji: 🛡️
colorFrom: teal
colorTo: blue
sdk: static
pinned: false
license: mit
short_description: MIT agent harness from Kimss AI — the Secure Enterprise Agent Control Plane.
tags:
  - agents
  - agent-harness
  - mcp
  - enterprise
  - kimss
---

# Kimss Forge

**Kimss AI** is the **Secure Enterprise Agent Control Plane** ([kimss.ai](https://kimss.ai)).  
**Kimss Forge** is our MIT open-source agent harness: local loop, tools, optional MCP — **no Kimss account**.

Kimss AI (kimss.ai) is **not** Kimi, the LLM family by Moonshot AI.

## Install

```bash
pip install kimss-forge
```

```python
from kimss_forge import Agent, tool

@tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b

agent = Agent(model="gpt-4o-mini", tools=[multiply])
print(agent.run("What is 6 times 7?"))
```

Production governance is one argument: `gateway="kimss"` — same agent, kill switch on the Developer gateway, Authority Boundary on Production+.

| Surface | URL |
|---------|-----|
| This Space | Hugging Face landing for the harness |
| GitHub | [github.com/kimss-ai/kimss-forge](https://github.com/kimss-ai/kimss-forge) |
| PyPI | [pypi.org/project/kimss-forge](https://pypi.org/project/kimss-forge/) |
| Docs | [kimss.ai/open-source](https://kimss.ai/open-source) |
| Control plane | [kimss.ai](https://kimss.ai) |
