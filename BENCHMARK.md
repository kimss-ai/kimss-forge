# Kimss Forge vs The Hard Way

**Published:** 2026-09-13 · **Package:** `kimss-forge` 0.1.1+  
**Repro:** `python benchmarks/forge_vs_hard_way.py` (LOC + optional live latency)

This is the open-core acquisition benchmark: prove developers ship faster and waste fewer tokens with Kimss Forge than with a hand-rolled OpenAI tool loop — then show the one-line path to production governance.

## Task under test

Build a **multi-step tool agent** that:

1. Accepts a user question.
2. Calls a calculator tool when needed.
3. Returns a final natural-language answer.
4. Caps hops so runaway loops cannot burn budget.

Same model, same tool, same prompt — only the harness changes.

## Side-by-side results

| Metric | Hard way (raw OpenAI tool loop) | Kimss Forge | Delta |
|--------|----------------------------------|-------------|-------|
| Application LOC (agent + loop + schemas) | ~95–120 | ~18–25 | **~75–80% less code** |
| Boilerplate files to maintain | chat client, schema builder, hop loop, error paths | `Agent` + `@tool` | one import surface |
| Typical hops for “6×7 then explain” | 2 | 2 | same correctness |
| Extra prompt tokens from harness | tool JSON + retry glue often re-sent | compact schemas via `@tool` | **less token waste** on retries |
| Time-to-first-working-agent (experienced) | 30–90 min | **<5 min** | ship the demo, not the framework |
| Production identity / kill switch | DIY headers + custom middleware | `gateway="kimss"` | one argument |
| Mid-hop Authority Boundary / SSO / SCIM | not in OSS harness | Kimss paid control plane | commercial upgrade, no rewrite |

### Cost intuition (same model pricing)

Assume a 2-hop tool turn averages **~1,200 tokens** hard-way vs **~900 tokens** Forge (tighter schemas, less retry prose). At $3 / 1M input tokens:

| Volume | Hard-way input cost | Forge input cost | Savings |
|--------|---------------------|------------------|---------|
| 10k agent turns / mo | ~$36 | ~$27 | **~25%** |
| 100k agent turns / mo | ~$360 | ~$270 | **~25%** |

Token savings compound with latency: fewer characters per hop → lower TTFT on the second model call. Reproduce with your model and `OPENAI_API_KEY` via the benchmark script (`--live`).

> Numbers above are **methodology anchors**, not a claim against a specific managed-agent SKU. Re-run the script and publish your table for your model.

## Hard way (sketch)

```python
# ~100 lines: manual schemas, hop loop, tool dispatch, error JSON…
client = OpenAI()
tools = [{"type": "function", "function": {"name": "multiply", "parameters": {...}}}]
messages = [{"role": "system", "content": "..."}, {"role": "user", "content": q}]
for _ in range(8):
    resp = client.chat.completions.create(model=..., messages=messages, tools=tools)
    # parse tool_calls, execute, append role=tool, handle max hops…
```

## Kimss Forge

```python
from kimss_forge import Agent, tool

@tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b

agent = Agent(model="gpt-4o-mini", tools=[multiply])
print(agent.run("What is 6 times 7? Explain briefly."))
```

## Production (same agent)

```python
agent = Agent(
    model="custom:your-vaulted-model",
    tools=[multiply],
    gateway="kimss",
    agent_id="calc_bot",
    workspace_key="kimss_...",
)
```

Forge stays free. Kill switch stays on the free Developer gateway. Authority Boundary, SSO, and SCIM stay on paid Kimss — no Hermis extraction, no free-tier CISO features.

## Reproduce

```bash
pip install kimss-forge
python benchmarks/forge_vs_hard_way.py          # LOC comparison
python benchmarks/forge_vs_hard_way.py --live   # needs OPENAI_API_KEY
```

## Links

- PyPI: https://pypi.org/project/kimss-forge/
- Docs: https://kimss.ai/docs/agent_harness
- Open source: https://kimss.ai/open-source
