#!/usr/bin/env python3
"""Generate compatibility/version-policy.v0.1.json from the committed schema bytes.

The digests in the policy are computed from the on-disk schema files, so the
policy is never hand-authored. Re-run after any schema change:

    python3 scripts/gen_version_policy.py

The check in tests/test_contracts.py fails if the committed policy is stale.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
COMMERCE_DIR = REPO_ROOT / "schemas" / "commerce" / "v0.1"
OUT = REPO_ROOT / "compatibility" / "version-policy.v0.1.json"

POLICY = {
    "policy_id": "dagr-commerce-contracts.version-policy.v0.1",
    "vocabulary_version": "0.1.0",
    "schema_draft": "https://json-schema.org/draft/2020-12/schema",
    "identifier_namespace": "https://contracts.dagr-commerce.dev/schema/v0.1/",
    "identifier_namespace_note": (
        "Schema $id URIs are stable, repository-local, versioned identifiers only. "
        "They are not a published, registered, or upstream standard, and network "
        "resolution is neither required nor implied."
    ),
    "versioning": {
        "scheme": "semver-major.minor.patch",
        "patch": "editorial or additive-optional changes; positive fixtures remain valid",
        "minor": "additive changes (new optional fields, new object types); positive fixtures remain valid",
        "major": "breaking changes; requires a new versioned directory and a documented migration",
        "compatibility_guarantee": (
            "Within a major.minor line, changes are additive and non-breaking to the "
            "committed positive fixtures."
        ),
        "deprecation": (
            "Deprecated fields are marked in the schema description and retained for at "
            "least one minor version before removal in a major version."
        ),
    },
    "claim_discipline": {
        "no_aggregate_verdict": (
            "No object or report emits an aggregate trusted/safe/compliant/verified/"
            "governed verdict. Outcomes are per-path/per-check observation states only."
        ),
        "protocol_neutral": (
            "No contract requires a specific commerce protocol, payment rail, chain, "
            "PSP, merchant, wallet, or DAGR transport."
        ),
        "projection_not_receipt": (
            "The evidence-envelope references native payloads by digest/custody and is "
            "not an ARCS receipt or a verifier verdict."
        ),
    },
}


def main() -> int:
    schemas = []
    for schema_file in sorted(COMMERCE_DIR.glob("*.json")):
        raw = schema_file.read_bytes()
        doc = json.loads(raw)
        schemas.append({
            "file": f"schemas/commerce/v0.1/{schema_file.name}",
            "id": doc.get("$id"),
            "title": doc.get("title"),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "byte_length": len(raw),
        })
    policy = dict(POLICY)
    policy["schemas"] = schemas
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(policy, indent=2, sort_keys=False) + "\n")
    print(f"wrote {OUT} with {len(schemas)} schema digests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
