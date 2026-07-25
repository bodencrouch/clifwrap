#!/usr/bin/env python3
"""Fail if blocklisted vendor tokens appear in the repository tree."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "agentdecompile_projects", "__pycache__", ".pytest_cache", "dist", "build", ".nox"}

PATTERNS = [
    re.compile(r"searchcli", re.I),
    re.compile(r"searchcli", re.I),
    re.compile(r"scrapecli", re.I),
    re.compile(r"askcli", re.I),
    re.compile(r"\bquerycli\b", re.I),
    re.compile(r"indexcli", re.I),
    re.compile(r"indexcli", re.I),
    re.compile(r"\bjina\b", re.I),
    re.compile(r"\bquerycli\b", re.I),
    re.compile(r"SEARCHCLI_", re.I),
    re.compile(r"SCRAPECLI_", re.I),
    re.compile(r"PERPLEXITY_", re.I),
    re.compile(r"BRAVE_", re.I),
    re.compile(r"EXA_", re.I),
    re.compile(r"JINA_", re.I),
    re.compile(r"api\.searchcli\.com", re.I),
    re.compile(r"scrapecli", re.I),
    re.compile(r"docs\.searchcli\.com", re.I),
]

# Allow vendor tokens only inside the history-rewrite tooling itself.
ALLOWLIST_PREFIXES = (
    "scripts/_removed_anonymize/replacements.txt",
    "scripts/_removed_anonymize/path-renames.txt",
    "scripts/_removed_anonymize/commit_message_callback.py",
    "scripts/_removed_anonymize/apply_tree.py",
    "scripts/check_anonymity.py",
)


def iter_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if rel in ALLOWLIST_PREFIXES:
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
                violations.append(f"{rel}: matched /{pattern.pattern}/")
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
