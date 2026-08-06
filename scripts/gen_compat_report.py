#!/usr/bin/env python3
"""Generate the C0 compatibility report FROM EXECUTION.

The v0.1 -> v0.2.0 hardening tightens the accepted-instance set. Per the
compatibility policy, that change must not ride silently under the old
compatibility claim. This script classifies each tightening and — critically —
proves it by actually running the reference validator against the committed
fixture for that boundary, recording the real reported keyword/path. The output
is therefore execution-derived, not hand-authored, and a freshness test asserts
the committed report matches a fresh regeneration.

Usage:
  python scripts/gen_compat_report.py            # write the two artifacts
  python scripts/gen_compat_report.py --check    # exit 1 if committed != fresh
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import dagr_commerce_contracts.validate as V  # noqa: E402

PRIOR_VERSION = "0.1.0"
NEW_VERSION = "0.2.0"

# Each tightening, paired with the committed fixture that proves it. classification
# is one of: "breaking-correction" (rejects instances that were previously accepted
# but were never legitimate) or "newly-required" (adds a required field).
CORRECTIONS = [
    ("extensions-credential", "Raw credential key in `extensions`", "breaking-correction",
     "negative/intent.smuggled-extension-key.json", "intent.schema.json",
     "Move the credential out of `extensions`; reference it by redaction_marker/digest/custody."),
    ("extensions-credential-nested", "Nested credential key in `extensions`", "breaking-correction",
     "mutation/intent.nested-smuggled-extension.json", "intent.schema.json",
     "Same as above; the restriction now applies at any nesting depth."),
    ("extensions-verdict", "Aggregate-verdict key in `extensions`", "breaking-correction",
     "mutation/intent.verdict-extension-key.json", "intent.schema.json",
     "Do not carry a verdict/trusted/safe/compliant/verified/governed field; observations are per-path only."),
    ("extensions-authority", "Native/ARCS-authority-impersonating key in `extensions`", "breaking-correction",
     "mutation/intent.nested-authority-extension.json", "intent.schema.json",
     "Do not place object_type/envelope_kind/arcs_receipt/verifier_verdict in extensions; use protocol_native_reference."),
    ("timestamp-format", "Non-RFC3339 timestamp", "breaking-correction",
     "negative/intent.bad-timestamp.json", "intent.schema.json",
     "Emit RFC 3339 date-time (e.g. 2026-08-05T12:00:00Z)."),
    ("digest-shape", "Digest value not bound to algorithm/encoding", "breaking-correction",
     "mutation/native-evidence.nonhex-digest-value.json", "native-evidence.schema.json",
     "Provide a digest value matching the declared encoding/length (hex sha-256 = 64 hex chars)."),
    ("redaction-conditional", "`digest_only` redaction marker without a digest", "breaking-correction",
     "mutation/evidence-envelope.digest-only-no-digest.json", "evidence-envelope.schema.json",
     "digest_only requires digest; custody_reference requires custody; masked requires hint."),
    ("non-negative-amount", "Negative monetary amount", "breaking-correction",
     "mutation/settlement.negative-amount.json", "settlement.schema.json",
     "Use a non-negative amount for price/charge/cap fields."),
    ("positive-quantity", "Zero-quantity line", "breaking-correction",
     "mutation/cart.zero-quantity-line.json", "cart.schema.json",
     "Line quantity must be an integer >= 1."),
    ("required-contract-version", "Missing root `contract_version`", "newly-required",
     "negative/order.missing-contract-version.json", "order.schema.json",
     "Add `contract_version` (e.g. \"0.2.0\") to every top-level object."),
]


def _observed(registry, Draft, schema_name, fixture_rel):
    inst = json.loads((REPO_ROOT / "fixtures" / fixture_rel).read_text())
    validator = V._validator_for(schema_name, registry, Draft)
    errs = sorted(validator.iter_errors(inst), key=lambda e: e.json_path)
    if not errs:
        raise SystemExit(f"COMPAT-GEN ERROR: {fixture_rel} was ACCEPTED; hardening incomplete")
    e = errs[0]
    return {"keyword": e.validator, "path": e.json_path}


def build() -> dict:
    registry, Draft = V._build_registry()
    rows = []
    for cid, title, classification, fixture, schema, migration in CORRECTIONS:
        obs = _observed(registry, Draft, schema, fixture)
        rows.append({
            "id": cid, "title": title, "classification": classification,
            "proof_fixture": fixture, "schema": schema,
            "rejected_at": obs, "migration": migration,
        })
    return {
        "artifact": "dagr-commerce-contracts compatibility report",
        "prior_version": PRIOR_VERSION,
        "version": NEW_VERSION,
        "summary": {
            "breaking_corrections": sum(1 for r in rows if r["classification"] == "breaking-correction"),
            "newly_required": sum(1 for r in rows if r["classification"] == "newly-required"),
        },
        "note": "Every row is proven by running the reference validator against the named committed fixture; this file is generated by scripts/gen_compat_report.py, not hand-authored.",
        "corrections": rows,
    }


def render_json(data: dict) -> str:
    return json.dumps(data, indent=2) + "\n"


def render_md(data: dict) -> str:
    L = []
    L.append("# Compatibility report — dagr-commerce-contracts")
    L.append("")
    L.append(f"Prior version: `{data['prior_version']}` → this version: `{data['version']}`.")
    L.append("")
    L.append("This hardening **shrinks the accepted-instance set**, so it is a corrective")
    L.append("change, not a backward-compatible extension. It is published under a new")
    L.append("version rather than silently under the prior compatibility claim. Each row")
    L.append("below is proven by running the reference validator against a committed")
    L.append("fixture (see `scripts/gen_compat_report.py`), so this report cannot drift")
    L.append("from the schemas.")
    L.append("")
    s = data["summary"]
    L.append(f"- breaking corrections: **{s['breaking_corrections']}**")
    L.append(f"- newly required fields: **{s['newly_required']}**")
    L.append("")
    L.append("Because these repositories were created at Initial commit and C0 merged")
    L.append("exactly once, there are no external consumers to migrate; the schema `$id`")
    L.append("namespace stays at `v0.1` while the accepted set is corrected in place and")
    L.append("recorded here.")
    L.append("")
    L.append("| id | boundary | classification | rejected at | proof fixture | migration |")
    L.append("|----|----------|----------------|-------------|---------------|-----------|")
    for r in data["corrections"]:
        ra = f"`{r['rejected_at']['keyword']}` @ `{r['rejected_at']['path']}`"
        L.append(f"| {r['id']} | {r['title']} | {r['classification']} | {ra} | `{r['proof_fixture']}` | {r['migration']} |")
    L.append("")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    data = build()
    md, js = render_md(data), render_json(data)
    md_path = REPO_ROOT / "compatibility" / "COMPATIBILITY_REPORT.md"
    js_path = REPO_ROOT / "compatibility" / "compat-report.v0.1.json"
    if args.check:
        stale = []
        if md_path.read_text() != md:
            stale.append(str(md_path))
        if js_path.read_text() != js:
            stale.append(str(js_path))
        if stale:
            print("STALE compatibility artifacts: " + ", ".join(stale), file=sys.stderr)
            return 1
        print("compatibility report: fresh")
        return 0
    md_path.write_text(md)
    js_path.write_text(js)
    print(f"wrote {md_path.relative_to(REPO_ROOT)} and {js_path.relative_to(REPO_ROOT)} "
          f"({data['summary']['breaking_corrections']} breaking, {data['summary']['newly_required']} newly-required)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
