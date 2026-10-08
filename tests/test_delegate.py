"""Unit tests for Agent.delegate() (no live network)."""

from __future__ import annotations

import pytest

from kimss_forge import Agent
from kimss_forge.run_context import RunContext, set_run_context


def test_delegate_requires_kimss_gateway():
    agent = Agent(
        model="gpt-4o-mini",
        api_key="sk-test",
        base_url="https://api.openai.com/v1",
    )
    with pytest.raises(ValueError, match="gateway='kimss'"):
        agent.delegate(agent_id="researcher")


def test_delegate_child_depth_run_id_and_lineage_headers(monkeypatch):
    monkeypatch.setenv("KIMSS_API_KEY", "kimss_test_key")
    set_run_context(None)
    parent_ctx = RunContext(
        run_id="run_parent_abc",
        depth=0,
        span_id="span_root_001",
        lineage="lineage-token-root",
    )
    root = Agent(
        model="custom:kimss-gpt-5-3",
        instructions="Orchestrate.",
        gateway="kimss",
        agent_id="orchestrator",
        workspace_key="kimss_test_key",
        run_context=parent_ctx,
    )
    assert root._gateway_connected is True
    assert root._run_context is not None
    assert root._run_context.depth == 0
    assert root._run_context.run_id == "run_parent_abc"

    child = root.delegate(
        agent_id="researcher",
        instructions="Summarize sources.",
    )
    assert child._gateway_connected is True
    assert child.agent_id == "researcher"
    assert child._run_context is not None
    assert child._run_context.run_id == "run_parent_abc"
    assert child._run_context.depth == 1
    assert child._run_context.parent_span == "span_root_001"
    assert child._run_context.span_id != "span_root_001"
    assert child._run_context.lineage == "lineage-token-root"

    headers = child._client.default_headers
    assert headers.get("X-Kimss-Agent-Id") == "researcher"
    assert headers.get("X-Kimss-Run-Id") == "run_parent_abc"
    assert headers.get("X-Kimss-Depth") == "1"
    assert headers.get("X-Kimss-Parent-Span") == "span_root_001"
    assert headers.get("X-Kimss-Span-Id") == child._run_context.span_id
    assert headers.get("X-Kimss-Lineage") == "lineage-token-root"
