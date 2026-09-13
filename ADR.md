# ADR: Open-core Kimss Forge (mirrored into public repo)

> Canonical vault copy: `kimss-docs/rules/decisions/adr-open-core-harness.md`.
> This file is included in the public tree so contributors see the open-core boundary.

## Context

TrueFoundry-style open core separates a **free developer harness** from a **paid governance control plane**. Kimss already had MIT gateway clients that require a Kimss account. Developers needed a standalone loop with **zero signup friction**.

## Decision

1. Ship **Kimss Forge** — unified names: GitHub `kimss-ai/kimss-forge`, PyPI `kimss-forge`, import `kimss_forge`, monorepo `kimss-forge/`.
2. Forge is **standalone**: OpenAI-compatible completions, `@tool`, optional MCP — no Kimss credentials for the default path.
3. One-line upgrade: `Agent(..., gateway="kimss", agent_id=..., workspace_key=...)`.
4. **Do not open-source Hermis** (`kimssapi_functions/hermis/`) or vault/plan/SCIM/Authority Boundary logic. Forge is written fresh.
5. **Kill switch stays on Developer (free)** as the adoption hook. CISO paywall: Authority Boundary, PII scrub, Threat Intercepts UI, Team & Access, SSO, SCIM.

## Why not `hermis-core`?

Hermis is the proprietary Studio/server loop. Naming the OSS package after it would imply we open-sourced governance we intentionally keep closed.

## Consequences

- Mirror secrets: `KIMSS_FORGE_MIRROR_PAT` + `KIMSS_FORGE_MIRROR_REPO=kimss-ai/kimss-forge`
- Non-runtime: `kimss_forge/` in `.deployexclude`
- Marketing `/open-source`, docs `/docs/agent_harness`
