#!/usr/bin/env python3
"""Create or update the public Hugging Face Space for Kimss Forge.

Requires a write token (env HF_TOKEN or huggingface.co login).
Target: https://huggingface.co/spaces/kimss-ai/kimss-forge
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

SPACE_ID = "kimss-ai/kimss-forge"
SPACE_DIR = Path(__file__).resolve().parents[1] / "huggingface-space"


def main() -> int:
    try:
        from huggingface_hub import HfApi, login
    except ImportError:
        print("Install huggingface_hub: pip install huggingface_hub", file=sys.stderr)
        return 1

    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN")
    if token:
        login(token=token, add_to_git_credential=False)
    api = HfApi(token=token)
    try:
        who = api.whoami()
    except Exception as exc:  # noqa: BLE001
        print(f"Not logged in to Hugging Face ({exc}).", file=sys.stderr)
        print("Set HF_TOKEN or run: hf auth login", file=sys.stderr)
        return 2

    print(f"Authenticated as {who.get('name') or who.get('email')}")
    api.create_repo(
        repo_id=SPACE_ID,
        repo_type="space",
        space_sdk="static",
        exist_ok=True,
        private=False,
    )
    api.upload_folder(
        folder_path=str(SPACE_DIR),
        repo_id=SPACE_ID,
        repo_type="space",
        commit_message="Publish Kimss Forge — Kimss AI Secure Enterprise Agent Control Plane",
    )
    print(f"Published https://huggingface.co/spaces/{SPACE_ID}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
