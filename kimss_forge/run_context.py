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
        """Mint a child hop: depth+1, parent=this span, new span_id."""
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


def apply_response_lineage(data: Dict[str, Any]) -> Optional[RunContext]:
    """Absorb server-minted lineage headers from a chat.completions response.

    Children must use the returned ``X-Kimss-Lineage`` token; forging depth without
    it is denied at the gateway.
    """
    if not isinstance(data, dict):
        return get_run_context()
    lin = data.get("_kimss_lineage") if isinstance(data.get("_kimss_lineage"), dict) else {}
    cur = get_run_context()
    if not lin:
        return cur
    token = lin.get("X-Kimss-Lineage") or lin.get("x-kimss-lineage")
    run_id = lin.get("X-Kimss-Run-Id") or lin.get("x-kimss-run-id")
    span = lin.get("X-Kimss-Span-Id") or lin.get("x-kimss-span-id")
    if cur is None:
        cur = RunContext(
            run_id=str(run_id or uuid.uuid4().hex),
            depth=0,
            span_id=str(span or uuid.uuid4().hex[:16]),
            lineage=str(token) if token else None,
        )
        _CURRENT.set(cur)
        return cur
    updated = cur
    if token:
        updated = updated.with_lineage(str(token))
    if span and not cur.span_id:
        updated = replace(updated, span_id=str(span))
    if run_id and not cur.run_id:
        updated = replace(updated, run_id=str(run_id))
    _CURRENT.set(updated)
    return updated
