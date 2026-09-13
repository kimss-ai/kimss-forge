#!/usr/bin/env python3
"""Kimss Forge vs The Hard Way — LOC + optional live latency/token comparison.

Usage:
  python benchmarks/forge_vs_hard_way.py
  python benchmarks/forge_vs_hard_way.py --live   # needs OPENAI_API_KEY
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

HARD_WAY_LOC = 108  # reference hand-rolled loop size (see BENCHMARK.md)
FORGE_APP_LOC = 22  # Agent + @tool surface for the same task


def _print_loc_table() -> None:
    saved = HARD_WAY_LOC - FORGE_APP_LOC
    pct = 100.0 * saved / HARD_WAY_LOC
    print("=== Kimss Forge vs The Hard Way (boilerplate) ===")
    print(f"{'Metric':<40} {'Hard way':>12} {'Forge':>12}")
    print("-" * 68)
    print(f"{'App LOC (agent + loop + schemas)':<40} {HARD_WAY_LOC:>12} {FORGE_APP_LOC:>12}")
    print(f"{'Boilerplate reduction':<40} {'—':>12} {f'{pct:.0f}%':>12}")
    print()
    print("Forge surface for the benchmark task:")
    print(
        '  from kimss_forge import Agent, tool\n'
        '  @tool\n'
        '  def multiply(a: float, b: float) -> float:\n'
        '      """Multiply two numbers."""\n'
        '      return a * b\n'
        '  agent = Agent(model="gpt-4o-mini", tools=[multiply])\n'
        '  print(agent.run("What is 6 times 7?"))\n'
    )
    print("Production upgrade (one line): gateway=\"kimss\"")


def _usage_tokens(raw: Optional[Dict[str, Any]]) -> Tuple[int, int]:
    if not isinstance(raw, dict):
        return 0, 0
    usage = raw.get("usage") or {}
    return int(usage.get("prompt_tokens") or 0), int(usage.get("completion_tokens") or 0)


def _run_forge_live(model: str) -> Dict[str, Any]:
    from kimss_forge import Agent, tool

    @tool
    def multiply(a: float, b: float) -> float:
        """Multiply two numbers."""
        return a * b

    agent = Agent(model=model, tools=[multiply], instructions="Be brief. Use tools for math.")
    t0 = time.perf_counter()
    result = agent.run("What is 6 times 7? One short sentence.")
    elapsed = time.perf_counter() - t0
    prompt_t, completion_t = _usage_tokens(result.raw)
    return {
        "label": "kimss-forge",
        "text": str(result)[:200],
        "hops": result.hops,
        "seconds": round(elapsed, 3),
        "prompt_tokens": prompt_t,
        "completion_tokens": completion_t,
        "tool_calls": len(result.tool_calls),
    }


def _run_hard_way_live(model: str) -> Dict[str, Any]:
    """Minimal hand-rolled OpenAI tool loop (illustrative hard way)."""
    import requests

    api_key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    base = (os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
    tools = [
        {
            "type": "function",
            "function": {
                "name": "multiply",
                "description": "Multiply two numbers.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "number"},
                        "b": {"type": "number"},
                    },
                    "required": ["a", "b"],
                },
            },
        }
    ]
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": "Be brief. Use tools for math."},
        {"role": "user", "content": "What is 6 times 7? One short sentence."},
    ]
    prompt_total = 0
    completion_total = 0
    hops = 0
    tool_calls = 0
    t0 = time.perf_counter()
    final_text = ""
    for _ in range(8):
        hops += 1
        resp = requests.post(
            f"{base}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"model": model, "messages": messages, "tools": tools, "tool_choice": "auto"},
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        usage = data.get("usage") or {}
        prompt_total += int(usage.get("prompt_tokens") or 0)
        completion_total += int(usage.get("completion_tokens") or 0)
        msg = (data.get("choices") or [{}])[0].get("message") or {}
        messages.append(msg)
        calls = msg.get("tool_calls") or []
        if not calls:
            final_text = str(msg.get("content") or "")
            break
        for tc in calls:
            tool_calls += 1
            args = json.loads((tc.get("function") or {}).get("arguments") or "{}")
            out = float(args["a"]) * float(args["b"])
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.get("id"),
                    "content": str(out),
                }
            )
    elapsed = time.perf_counter() - t0
    return {
        "label": "hard-way",
        "text": final_text[:200],
        "hops": hops,
        "seconds": round(elapsed, 3),
        "prompt_tokens": prompt_total,
        "completion_tokens": completion_total,
        "tool_calls": tool_calls,
    }


def _print_live(rows: List[Dict[str, Any]]) -> None:
    print("=== Live run (same model / prompt) ===")
    keys = ("label", "hops", "tool_calls", "seconds", "prompt_tokens", "completion_tokens")
    print("  ".join(f"{k:>16}" for k in keys))
    for row in rows:
        print("  ".join(f"{row.get(k):>16}" for k in keys))
        print(f"  text: {row.get('text')!r}")
    if len(rows) == 2:
        hw, fg = rows[0], rows[1]
        if hw["prompt_tokens"] and fg["prompt_tokens"]:
            saved = hw["prompt_tokens"] - fg["prompt_tokens"]
            pct = 100.0 * saved / hw["prompt_tokens"]
            print(f"\nPrompt token delta (hard − forge): {saved} ({pct:.0f}%)")
        if hw["seconds"] and fg["seconds"]:
            print(f"Wall time delta (hard − forge): {hw['seconds'] - fg['seconds']:.3f}s")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Call the model endpoint")
    parser.add_argument("--model", default=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"))
    args = parser.parse_args()
    _print_loc_table()
    if not args.live:
        print("Tip: re-run with --live and OPENAI_API_KEY to measure latency/tokens.")
        return 0
    if not (os.environ.get("OPENAI_API_KEY") or "").strip():
        print("OPENAI_API_KEY required for --live", file=sys.stderr)
        return 2
    hard = _run_hard_way_live(args.model)
    forge = _run_forge_live(args.model)
    _print_live([hard, forge])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
