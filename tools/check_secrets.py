#!/usr/bin/env python3
"""Fail safely when tracked source resembles a committed credential.

The check prints only the rule and file path, never the matching value. GitHub
secret scanning remains the authoritative provider-token scanner; this small
local gate catches common mistakes before a push.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
MAX_FILE_SIZE = 5 * 1024 * 1024

SENSITIVE_NAMES = (
    re.compile(r"(^|/)\.env($|\.)", re.IGNORECASE),
    re.compile(r"(^|/)(id_rsa|id_dsa|id_ecdsa|id_ed25519)$", re.IGNORECASE),
    re.compile(r"(^|/).+\.(pem|p12|pfx|key)$", re.IGNORECASE),
    re.compile(r"(^|/)(credentials|secrets?)\.(json|ya?ml)$", re.IGNORECASE),
    re.compile(r"(^|/)(\.npmrc|\.pypirc|\.netrc)$", re.IGNORECASE),
)

CONTENT_RULES = (
    (
        "private key",
        re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    ),
    ("GitHub token", re.compile(rb"(?:github_pat_[A-Za-z0-9_]{40,}|gh[pousr]_[A-Za-z0-9]{30,})")),
    ("AWS access key", re.compile(rb"(?:AKIA|ASIA)[0-9A-Z]{16}")),
    ("Telegram bot token", re.compile(rb"\b[0-9]{6,12}:[A-Za-z0-9_-]{30,}\b")),
    (
        "literal secret assignment",
        re.compile(
            rb"(?i)['\"]?(?:[a-z0-9]+[_-])*(?:token|secret|password|api[_-]?key|"
            rb"access[_-]?key|private[_-]?key)['\"]?\s*[:=]\s*"
            rb"['\"](?![.$<{])[A-Za-z0-9_./+=:-]{20,}['\"]"
        ),
    ),
)


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def main() -> int:
    failures: list[tuple[str, str]] = []
    checked = 0

    for relative in tracked_files():
        normalized = PurePosixPath(relative).as_posix()
        for pattern in SENSITIVE_NAMES:
            if pattern.search(normalized):
                failures.append((normalized, "sensitive filename"))

        path = ROOT / relative
        if not path.is_file() or path.stat().st_size > MAX_FILE_SIZE:
            continue
        data = path.read_bytes()
        if b"\0" in data:
            continue
        checked += 1
        for rule, pattern in CONTENT_RULES:
            if pattern.search(data):
                failures.append((normalized, rule))

    if failures:
        print("Secret checks failed (values intentionally hidden):")
        for relative, rule in sorted(set(failures)):
            print(f"- {relative}: {rule}")
        return 1

    print(f"Secret checks passed: {checked} tracked text files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
