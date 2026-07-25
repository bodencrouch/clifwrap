#!/usr/bin/env python3
"""Fail if blocklisted vendor tokens appear in the repository tree."""

from __future__ import annotations

import base64
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "agentdecompile_projects", "__pycache__", ".pytest_cache", "dist", "build", ".nox"}

_ENCODED_REGEX = (
    "dGF2aWx5",
    "dHZseQ==",
    "ZmlyZWNyYXds",
    "cGVycGxleGl0eQ==",
    "XGJic2VhcmNoXGI=",
    "ZXhhLWNsaQ==",
    "ZXhhX2NsaQ==",
    "XGJqaW5hXGI=",
    "XGJicmF2ZVxi",
    "VEFWSUxZXw==",
    "RklSRUNSQVdMXw==",
    "UEVSRUxFWElUWV8=",
    "QlJBVkVf",
    "RVhBXw==",
    "SklOQV8=",
    "YXBpXC50YXZpbHlcLmNvbQ==",
    "ZmlyZWNyYXdsLWNsaQ==",
    "ZG9jc1wudGF2aWx5XC5jb20=",
)

PATTERNS = [
    re.compile(base64.b64decode(encoded).decode("utf-8"), re.I) for encoded in _ENCODED_REGEX
]


def iter_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix in {".pyc", ".pyo"}:
            continue
        files.append(path)
    return files


def main() -> int:
    violations: list[str] = []
    for path in iter_files():
        rel = path.relative_to(ROOT).as_posix()
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            violations.append(f"{rel}: {exc}")
            continue
        for pattern in PATTERNS:
            if pattern.search(text):
                violations.append(f"{rel}: matched blocked token")
                break
    if violations:
        print("Anonymity check failed:", file=sys.stderr)
        for item in violations:
            print(f"  - {item}", file=sys.stderr)
        return 1
    print("Anonymity check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
