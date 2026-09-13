# Kimss Forge — open-source agent harness

[![PyPI](https://img.shields.io/pypi/v/kimss-forge.svg)](https://pypi.org/project/kimss-forge/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/pypi/pyversions/kimss-forge.svg)](https://pypi.org/project/kimss-forge/)

**Build and run agents with any model — free, forever. Connect Kimss when production needs governance.**

**Kimss Forge** (`kimss-forge` on PyPI, `import kimss_forge`) is a small MIT-licensed harness: a local multi-turn tool loop that talks to any OpenAI-compatible endpoint (OpenAI, Azure/Foundry, Anthropic-compatible proxies, Ollama, vLLM). **No Kimss account required** to develop and test.

When your security team needs identity, kill switch, budgets, and audit for production, flip one argument — `gateway="kimss"` — and traffic routes through the [Kimss AI Gateway](https://kimss.ai).

```python
from kimss_forge import Agent, tool

@tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b

# Local — your provider key only
agent = Agent(model="gpt-4o-mini", tools=[multiply])
print(agent.run("What is 6 times 7?"))

# Production — one line to the Kimss control plane
agent = Agent(
    model="custom:your-vaulted-model",
    tools=[multiply],
    gateway="kimss",
    agent_id="ops_bot",
    workspace_key="kimss_...",
)
```

## Naming (unified)

| Surface | Name |
|---------|------|
| Product | **Kimss Forge** |
| GitHub | [kimss-ai/kimss-forge](https://github.com/kimss-ai/kimss-forge) |
| PyPI | `kimss-forge` |
| Import | `import kimss_forge` / `from kimss_forge import Agent` |
| Monorepo SSOT | `kimssApi/kimss-forge/` |

## Why this exists

| Layer | Cost | What you get |
|-------|------|----------------|
| **Forge (this package)** | Free / MIT | Run agents, tools, MCP; any model endpoint |
| **Kimss Developer gateway** | Free tier (25k governed requests/mo) | Identity, audit trail, **kill switch** |
| **Kimss Production+** | Paid | Authority Boundary, RBAC, Threat Intercepts, PII scrub |
| **Kimss Scale / Enterprise** | Paid | SSO, SCIM, retention, schema isolation |

Developers adopt Forge to ship faster. CISOs purchase the control plane when production governance is mandatory — without rewriting the agent.

## Install

```bash
pip install kimss-forge
# optional MCP tools:
pip install 'kimss-forge[mcp]'
```

## Local (zero Kimss)

```bash
export OPENAI_API_KEY=sk-...
# optional: OPENAI_BASE_URL=https://your-endpoint/v1
python examples/01_local_agent.py
```

## Production via Kimss (one line)

1. Sign up at [kimss.ai](https://kimss.ai/app/signup) (Developer tier is free).
2. Vault your provider under **Connected Infrastructure**.
3. Mint a `kimss_...` workspace key.
4. Set `gateway="kimss"`, `agent_id=...`, and the workspace key.

```python
Agent(
    model="custom:your-vaulted-model",
    gateway="kimss",          # → https://api.kimss.ai/v1
    agent_id="fleet_reporter",
    workspace_key="kimss_...",
)
```

Every call sends `X-Kimss-Agent-Id`. Disable that agent in the Kimss UI and subsequent hops return **403** (kill switch). Paid tiers add Authority Boundary, Team & Access, SCIM/SSO, and more — see [pricing](https://kimss.ai/pricing).

## Examples

| Script | What it shows |
|--------|----------------|
| `examples/01_local_agent.py` | Local chat, no tools |
| `examples/02_tools.py` | `@tool` functions |
| `examples/03_mcp.py` | MCP stdio tools (`[mcp]` extra) |
| `examples/04_production_kimss.py` | Gateway connect |

## Design decision

See [ADR.md](ADR.md) (why Forge is separate from the proprietary Hermis server loop, and why kill switch stays free).

## Related

- Control-plane client (register agents, report usage): [`kimss`](https://pypi.org/project/kimss/) / [kimss-python-sdk](https://github.com/kimss-ai/kimss-python-sdk)
- Gateway quickstart: [kimss-python-quickstart](https://github.com/kimss-ai/kimss-python-quickstart)
- Docs: [Agent harness](https://kimss.ai/docs/agent_harness) · [Open source](https://kimss.ai/open-source)

## License

MIT — see [LICENSE](LICENSE).
