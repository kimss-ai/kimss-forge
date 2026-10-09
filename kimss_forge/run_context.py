"""Declared-run context for multi-agent Forge sessions (contextvar)."""

from __future__ import annotations

import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field, replace
from typing import Any, Dict, Optional


@dataclass
class RunContext:
    """Lineage carried across Agent.run / Agent.delegate hops."""

    run_id: str
    depth: int = 0
    parent_span: Optional[str] = None
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    lineage: Optional[str] = None

    def child(self, *, lineage: Optional[str] = None) -> "RunContext":
        """Local child hop sketch (depth+1). Prefer server-minted pending child."""
        return RunContext(
            run_id=self.run_id,
            depth=int(self.depth) + 1,
            parent_span=self.span_id,
            span_id=uuid.uuid4().hex[:16],
            lineage=(lineage or self.lineage),
        )

    def headers(self) -> Dict[str, str]:
        out: Dict[str, str] = {
            "X-Kimss-Run-Id": self.run_id,
            "X-Kimss-Depth": str(int(self.depth)),
            "X-Kimss-Span-Id": self.span_id,
        }
        if self.parent_span:
            out["X-Kimss-Parent-Span"] = self.parent_span
        if self.lineage:
            out["X-Kimss-Lineage"] = self.lineage
        return out

    def with_lineage(self, lineage: Optional[str]) -> "RunContext":
        if not lineage:
            return self
        return replace(self, lineage=str(lineage))


_CURRENT: ContextVar[Optional[RunContext]] = ContextVar("kimss_forge_run_context", default=None)
# Gateway response headers describe the *next* child hop (HMAC is bound to that identity).
_PENDING_CHILD: ContextVar[Optional[RunContext]] = ContextVar(
    "kimss_forge_pending_child", default=None
)


def get_run_context() -> Optional[RunContext]:
    return _CURRENT.get()


def set_run_context(ctx: Optional[RunContext]) -> None:
    _CURRENT.set(ctx)


def ensure_root_context() -> RunContext:
    cur = _CURRENT.get()
    if cur is not None:
        return cur
    ctx = RunContext(run_id=uuid.uuid4().hex, depth=0, span_id=uuid.uuid4().hex[:16])
    _CURRENT.set(ctx)
    return ctx


def get_pending_child() -> Optional[RunContext]:
    return _PENDING_CHILD.get()


def set_pending_child(ctx: Optional[RunContext]) -> None:
    _PENDING_CHILD.set(ctx)


def take_pending_child() -> Optional[RunContext]:
    """Consume the gateway-minted next-hop identity (one child per parent hop)."""
    pending = _PENDING_CHILD.get()
    _PENDING_CHILD.set(None)
    return pending


def run_context_from_lineage_headers(lin: Dict[str, Any]) -> Optional[RunContext]:
    """Build a RunContext from gateway response lineage headers (next hop)."""
    if not isinstance(lin, dict) or not lin:
        return None
    token = lin.get("X-Kimss-Lineage") or lin.get("x-kimss-lineage")
    run_id = lin.get("X-Kimss-Run-Id") or lin.get("x-kimss-run-id")
    depth_raw = lin.get("X-Kimss-Depth") or lin.get("x-kimss-depth")
    parent = lin.get("X-Kimss-Parent-Span") or lin.get("x-kimss-parent-span")
    span = lin.get("X-Kimss-Span-Id") or lin.get("x-kimss-span-id")
    if not run_id or span is None or depth_raw is None:
        return None
    try:
        depth = int(depth_raw)
    except (TypeError, ValueError):
        return None
    return RunContext(
        run_id=str(run_id),
        depth=depth,
        parent_span=str(parent) if parent else None,
        span_id=str(span),
        lineage=str(token) if token else None,
    )


def apply_response_lineage(data: Dict[str, Any]) -> Optional[RunContext]:
    """Absorb server-minted *next-hop* lineage from a chat.completions response.

    Response headers (Depth/Parent/Span/Lineage) identify the child hop the gateway
    just signed. They must not overwrite the current hop's request identity.
    Children must use ``take_pending_child()`` (via ``Agent.delegate``).
    """
    if not isinstance(data, dict):
        return get_run_context()
    lin = data.get("_kimss_lineage") if isinstance(data.get("_kimss_lineage"), dict) else {}
    pending = run_context_from_lineage_headers(lin)
    if pending is not None:
        set_pending_child(pending)
    return get_run_context()
