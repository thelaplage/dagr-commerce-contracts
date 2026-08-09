#!/usr/bin/env python3
"""Repo-wide committed-secret scanner (executable, fail-closed).

Scans every git-tracked text file for high-signal credential shapes: PEM
private-key blocks and provider API-key/token formats (AWS, GitHub, Slack,
Google, Stripe, OpenAI). Patterns are deliberately shape-specific so the
repository's legitimate content — 64-char sha-256 hex digests, and the
credential-name *vocabulary* inside JSON Schemas and the validator regex — is
not flagged. Raw sensitive material carried under credential-named KEYS in
fixtures is covered separately by the validator's no-raw-sensitive-material
check; this scanner targets real secret *values* anywhere in the tree.

Exit codes:
  0  no secret-shaped strings found.
  2  at least one candidate secret found (fail-closed).

Usage:
    python scripts/scan_secrets.py            # scan the whole tracked tree
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# High-signal secret shapes. Each requires a credential-specific prefix/format,
# not a generic word, so schema token vocabulary and hex digests do not match.
PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("pem-private-key", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----")),
    ("aws-access-key-id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("aws-secret-access-key", re.compile(r"(?i)aws_secret_access_key\s*[:=]\s*['\"][A-Za-z0-9/+]{40}['\"]")),
    ("github-token", re.compile(r"\bgh[posru]_[A-Za-z0-9]{36,}\b")),
    ("github-fine-grained-pat", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{60,}\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("stripe-live-secret", re.compile(r"\b[rs]k_live_[0-9A-Za-z]{16,}\b")),
    ("openai-key", re.compile(r"\bsk-[A-Za-z0-9]{32,}\b")),
]

# Files whose PURPOSE is to define these patterns; scanning them would flag the
# pattern definitions themselves, not a leaked secret.
SELF_REFERENTIAL = {
    "scripts/scan_secrets.py",
    "tests/test_c1_corrective.py",
}


def _tracked_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout
    return [p for p in out.splitlines() if p]


def scan_text(rel: str, text: str) -> list[str]:
    findings: list[str] = []
    for name, pat in PATTERNS:
        for m in pat.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            findings.append(f"{rel}:{line}: candidate {name}")
    return findings


def scan(files: list[str] | None = None) -> list[str]:
    files = files if files is not None else _tracked_files()
    findings: list[str] = []
    for rel in files:
        if rel in SELF_REFERENTIAL:
            continue
        path = REPO_ROOT / rel
        try:
            raw = path.read_bytes()
        except OSError:
            continue
        if b"\x00" in raw:  # skip binary
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue
        findings.extend(scan_text(rel, text))
    return findings


def main(argv: list[str] | None = None) -> int:
    findings = scan()
    if findings:
        print("COMMITTED-SECRET SCAN: FAIL (candidate secrets found)", file=sys.stderr)
        for f in findings:
            print(f"  - {f}", file=sys.stderr)
        return 2
    print("committed-secret scan: clean (no credential-shaped strings in tracked files).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
