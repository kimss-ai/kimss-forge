"""Unit tests for Agent.delegate() (no live network)."""

from __future__ import annotations

import pytest

from kimss_forge import Agent
from kimss_forge.run_context import (
    RunContext,
    apply_response_lineage,
    set_pending_child,
    set_run_context,
    take_pending_child,
)


def test_delegate_requires_kimss_gateway():
    agent = Agent(
        model="gpt-4o-mini",
        api_key="sk-test",
        base_url="https://api.openai.com/v1",
    )
    with pytest.raises(ValueError, match="gateway='kimss'"):
        agent.delegate(agent_id="researcher")


def test_apply_response_lineage_stores_pending_child_not_current():
    set_run_context(None)
    set_pending_child(None)
    root = RunContext(run_id="run_abc", depth=0, span_id="span_root")
    set_run_context(root)
    apply_response_lineage(
        {
            "_kimss_lineage": {
                "X-Kimss-Run-Id": "run_abc",
                "X-Kimss-Depth": "1",
                "X-Kimss-Parent-Span": "span_root",
                "X-Kimss-Span-Id": "span_child_srv",
                "X-Kimss-Lineage": "hmac-child-token",
            }
        }
    )
    # Current hop identity must stay at depth 0.
    assert root.depth == 0
    assert root.lineage is None
    pending = take_pending_child()
    assert pending is not None
    assert pending.depth == 1
    assert pending.parent_span == "span_root"
    assert pending.span_id == "span_child_srv"
    assert pending.lineage == "hmac-child-token"


def test_delegate_uses_server_minted_pending_child(monkeypatch):
    monkeypatch.setenv("KIMSS_API_KEY", "kimss_test_key")
    set_run_context(None)
    set_pending_child(None)
    parent_ctx = RunContext(
        run_id="run_parent_abc",
        depth=0,
        span_id="span_root_001",
    )
    root = Agent(
        model="custom:kimss-gpt-5-3",
        instructions="Orchestrate.",
        gateway="kimss",
        agent_id="orchestrator",
        workspace_key="kimss_test_key",
        run_context=parent_ctx,
    )
    # Simulate gateway mint after a parent hop (no live network).
    minted = RunContext(
        run_id="run_parent_abc",
        depth=1,
        parent_span="span_root_001",
        span_id="span_child_srv",
        lineage="hmac-from-gateway",
    )
    root._client.pending_child = minted

    child = root.delegate(
        agent_id="researcher",
        instructions="Summarize sources.",
        mint_if_needed=False,
    )
    assert child._gateway_connected is True
    assert child.agent_id == "researcher"
    assert child._run_context is not None
    assert child._run_context.run_id == "run_parent_abc"
    assert child._run_context.depth == 1
    assert child._run_context.parent_span == "span_root_001"
    assert child._run_context.span_id == "span_child_srv"
    assert child._run_context.lineage == "hmac-from-gateway"

    headers = child._client.default_headers
    assert headers.get("X-Kimss-Agent-Id") == "researcher"
    assert headers.get("X-Kimss-Run-Id") == "run_parent_abc"
    assert headers.get("X-Kimss-Depth") == "1"
    assert headers.get("X-Kimss-Parent-Span") == "span_root_001"
    assert headers.get("X-Kimss-Span-Id") == "span_child_srv"
    assert headers.get("X-Kimss-Lineage") == "hmac-from-gateway"


def test_delegate_without_mint_raises_when_mint_disabled(monkeypatch):
    monkeypatch.setenv("KIMSS_API_KEY", "kimss_test_key")
    set_run_context(None)
    set_pending_child(None)
    root = Agent(
        model="custom:kimss-gpt-5-3",
        gateway="kimss",
        agent_id="orchestrator",
        workspace_key="kimss_test_key",
        run_context=RunContext(run_id="run_x", depth=0, span_id="span_x"),
    )
    with pytest.raises(RuntimeError, match="mint child lineage"):
        root.delegate(agent_id="researcher", mint_if_needed=False)
