"""Local multi-turn agent loop (model → tools → model). No Kimss governance logic."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .client import ChatClient
from .tools import Tool


DEFAULT_MAX_HOPS = 8


@dataclass
class AgentResult:
    """Outcome of a single ``Agent.run`` call."""

    text: str
    messages: List[Dict[str, Any]] = field(default_factory=list)
    hops: int = 0
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    raw: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        return self.text


def _assistant_message_from_choice(choice: Dict[str, Any]) -> Dict[str, Any]:
    msg = choice.get("message") or {}
    out: Dict[str, Any] = {"role": "assistant"}
    content = msg.get("content")
    if content is not None:
        out["content"] = content
    tool_calls = msg.get("tool_calls")
    if tool_calls:
        out["tool_calls"] = tool_calls
    return out


def _stringify_content(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    try:
        return json.dumps(content, default=str)
    except TypeError:
        return str(content)


def run_loop(
    *,
    client: ChatClient,
    model: str,
    messages: List[Dict[str, Any]],
    tools: List[Tool],
    max_hops: int = DEFAULT_MAX_HOPS,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
) -> AgentResult:
    """
    Run a multi-turn tool loop until the model returns text or max_hops is hit.

    Pure local orchestration — no Authority Boundary, vault, or plan checks.
    """
    tool_map = {t.name: t for t in tools}
    openai_tools = [t.openai_schema() for t in tools] or None
    history = list(messages)
    recorded_calls: List[Dict[str, Any]] = []
    last_raw: Optional[Dict[str, Any]] = None
    hops = 0

    for hop in range(max(1, max_hops)):
        hops = hop + 1
        raw = client.chat_completions(
            model=model,
            messages=history,
            tools=openai_tools,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        last_raw = raw
        choices = raw.get("choices") or []
        if not choices:
            return AgentResult(
                text="",
                messages=history,
                hops=hops,
                tool_calls=recorded_calls,
                raw=raw,
            )
        assistant = _assistant_message_from_choice(choices[0])
        history.append(assistant)
        tool_calls = assistant.get("tool_calls") or []
        if not tool_calls:
            return AgentResult(
                text=_stringify_content(assistant.get("content")),
                messages=history,
                hops=hops,
                tool_calls=recorded_calls,
                raw=raw,
            )

        for tc in tool_calls:
            fn = (tc.get("function") or {}) if isinstance(tc, dict) else {}
            name = str(fn.get("name") or "").strip()
            args_raw = fn.get("arguments")
            call_id = str(tc.get("id") or name or "tool")
            recorded_calls.append({"id": call_id, "name": name, "arguments": args_raw})
            if name not in tool_map:
                result_text = json.dumps({"error": f"unknown tool: {name}"})
            else:
                try:
                    result_text = tool_map[name].call(args_raw)
                except Exception as exc:  # noqa: BLE001 — surface tool errors to the model
                    result_text = json.dumps({"error": str(exc)})
            history.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": result_text,
                }
            )

    # Max hops exhausted after tool rounds — ask once more without tools for a final answer.
    raw = client.chat_completions(
        model=model,
        messages=history,
        tools=None,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    last_raw = raw
    choices = raw.get("choices") or []
    text = ""
    if choices:
        assistant = _assistant_message_from_choice(choices[0])
        history.append(assistant)
        text = _stringify_content(assistant.get("content"))
    return AgentResult(
        text=text,
        messages=history,
        hops=hops,
        tool_calls=recorded_calls,
        raw=last_raw,
    )
