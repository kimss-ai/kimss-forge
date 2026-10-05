"""Provider-agnostic OpenAI-compatible chat completions client."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import requests

DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"


class CompletionError(RuntimeError):
    """Raised when the model endpoint returns an error."""

    def __init__(self, status_code: int, body: str):
        self.status_code = status_code
        self.body = body
        super().__init__(f"chat completions failed ({status_code}): {body[:400]}")


class ChatClient:
    """Minimal OpenAI-compatible `/chat/completions` client (requests only)."""

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_headers: Optional[Dict[str, str]] = None,
        timeout: float = 120.0,
    ) -> None:
        self.api_key = (api_key or os.environ.get("OPENAI_API_KEY") or "").strip()
        raw_base = (
            base_url
            or os.environ.get("OPENAI_BASE_URL")
            or DEFAULT_OPENAI_BASE_URL
        ).rstrip("/")
        self.base_url = raw_base
        self.default_headers = dict(default_headers or {})
        self.timeout = timeout

    def chat_completions(
        self,
        *,
        model: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError(
                "API key required: pass api_key=... or set OPENAI_API_KEY "
                "(or use gateway='kimss' with a Kimss workspace key)"
            )
        url = f"{self.base_url}/chat/completions"
        payload: Dict[str, Any] = {"model": model, "messages": messages}
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if temperature is not None:
            payload["temperature"] = temperature

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            **self.default_headers,
            **(extra_headers or {}),
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        if resp.status_code >= 400:
            raise CompletionError(resp.status_code, resp.text)
        try:
            data = resp.json()
        except json.JSONDecodeError as exc:
            raise CompletionError(resp.status_code, resp.text) from exc
        lineage = {}
        for key in (
            "X-Kimss-Run-Id",
            "X-Kimss-Depth",
            "X-Kimss-Parent-Span",
            "X-Kimss-Span-Id",
            "X-Kimss-Lineage",
        ):
            val = resp.headers.get(key)
            if val:
                lineage[key] = val
        if lineage:
            data["_kimss_lineage"] = lineage
            try:
                from .run_context import apply_response_lineage

                apply_response_lineage(data)
                # Keep child hops able to pick up the minted lineage token.
                token = lineage.get("X-Kimss-Lineage")
                if token:
                    self.default_headers["X-Kimss-Lineage"] = token
            except Exception:
                pass
        return data
