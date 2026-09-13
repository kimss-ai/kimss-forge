"""Unit tests for kimss-forge (no live network)."""

from __future__ import annotations

import json

import pytest
import responses

from kimss_forge import Agent, gateway_headers, tool
from kimss_forge.gateway import apply_kimss_gateway
from kimss_forge.tools import coerce_tools


@tool
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


def test_tool_schema():
    assert add.name == "add"
    assert "a" in add.parameters["properties"]
    assert add.call({"a": 2, "b": 3}) == "5"


def test_gateway_headers_require_agent_id():
    with pytest.raises(ValueError):
        gateway_headers(agent_id="")
    h = gateway_headers(agent_id="ops_bot", agent_name="Ops")
    assert h["X-Kimss-Agent-Id"] == "ops_bot"
    assert h["X-Kimss-Agent-Name"] == "Ops"


def test_apply_kimss_gateway(monkeypatch):
    monkeypatch.delenv("KIMSS_API_KEY", raising=False)
    monkeypatch.delenv("KIMSS_WORKSPACE_KEY", raising=False)
    url, key, headers = apply_kimss_gateway(
        workspace_key="kimss_test",
        agent_id="agent_1",
    )
    assert url.endswith("/v1")
    assert key == "kimss_test"
    assert headers["X-Kimss-Agent-Id"] == "agent_1"


@responses.activate
def test_agent_run_text_only():
    responses.add(
        responses.POST,
        "https://api.openai.com/v1/chat/completions",
        json={
            "choices": [
                {"message": {"role": "assistant", "content": "hello there"}}
            ]
        },
        status=200,
    )
    agent = Agent(
        model="gpt-4o-mini",
        instructions="Be brief.",
        api_key="sk-test",
        base_url="https://api.openai.com/v1",
    )
    result = agent.run("Hi")
    assert str(result) == "hello there"
    assert result.hops == 1


@responses.activate
def test_agent_tool_loop():
    # First response: tool call
    responses.add(
        responses.POST,
        "https://api.openai.com/v1/chat/completions",
        json={
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "type": "function",
                                "function": {
                                    "name": "add",
                                    "arguments": json.dumps({"a": 2, "b": 40}),
                                },
                            }
                        ],
                    }
                }
            ]
        },
        status=200,
    )
    # Second response: final text
    responses.add(
        responses.POST,
        "https://api.openai.com/v1/chat/completions",
        json={
            "choices": [
                {"message": {"role": "assistant", "content": "The sum is 42"}}
            ]
        },
        status=200,
    )
    agent = Agent(
        model="gpt-4o-mini",
        tools=[add],
        api_key="sk-test",
        base_url="https://api.openai.com/v1",
    )
    result = agent.run("What is 2+40?")
    assert "42" in result.text
    assert result.tool_calls[0]["name"] == "add"


@responses.activate
def test_agent_kimss_gateway_headers():
    def _check(request):
        assert request.headers.get("X-Kimss-Agent-Id") == "fleet_bot"
        assert request.headers.get("Authorization") == "Bearer kimss_abc"
        body = {
            "choices": [{"message": {"role": "assistant", "content": "ok"}}]
        }
        return (200, {"Content-Type": "application/json"}, json.dumps(body))

    responses.add_callback(
        responses.POST,
        "https://api.kimss.ai/v1/chat/completions",
        callback=_check,
    )
    agent = Agent(
        model="custom:demo",
        gateway="kimss",
        workspace_key="kimss_abc",
        agent_id="fleet_bot",
    )
    assert str(agent.run("ping")) == "ok"


def test_coerce_tools():
    tools = coerce_tools([add])
    assert len(tools) == 1
    assert tools[0].name == "add"
