# Changelog

## Unreleased

- Public Hugging Face Space for the harness: [spaces/kimss-ai/kimss-forge](https://huggingface.co/spaces/kimss-ai/kimss-forge).

## 0.1.1 — 2026-09-13

- Soft non-blocking Authority Boundary warning when risky tools run without `gateway="kimss"`.
- Send `X-Kimss-Client: kimss-forge` on gateway traffic for PLG attribution.
- Publish Forge vs Hard Way benchmark (`BENCHMARK.md`, `benchmarks/forge_vs_hard_way.py`).
- Add `llm-context.md`, `llms.txt`, and Cursor skill for coding-assistant indexing.

## 0.1.0 — 2026-09-13

- Initial release of `kimss-forge`: local multi-turn agent loop, tool dispatch, optional MCP tools.
- Provider-agnostic OpenAI-compatible chat completions (any `base_url`).
- One-line Kimss gateway connect (`gateway="kimss"`) for identity, kill switch, metering, and audit.
