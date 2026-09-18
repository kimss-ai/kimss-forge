# Contributing to Kimss Forge

Thanks for helping improve the open-source agent harness.

## Public repo vs monorepo

| Surface | Role |
|---------|------|
| [kimss-ai/kimss-forge](https://github.com/kimss-ai/kimss-forge) | **Public mirror** — issues, PRs, and releases for the community |
| `kimssApi/kimss-forge/` (private monorepo) | Internal SSOT; CI mirrors to the public repo |

Prefer opening **issues and pull requests on the public repo**. Maintainers may land accepted changes via the monorepo mirror.

## Development

```bash
python -m pip install -e ".[dev,mcp]"
pytest
ruff check .
```

## Scope

- In scope: local agent loop, `@tool`, MCP extras, docs, examples, benchmarks.
- Out of scope: Hermis / Studio server governance (stays proprietary on the Kimss control plane).

## License

By contributing you agree your changes are MIT-licensed (see [LICENSE](LICENSE)).
