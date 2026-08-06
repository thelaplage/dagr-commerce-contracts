# BUILD_REPORT — Lane C0 (dagr-commerce-contracts foundation)

Protocol-neutral, language-neutral commerce evidence vocabulary: JSON Schema
Draft 2020-12 contracts, positive/negative/mutation fixtures, a reference
validator, vendored `.ecosystem` coordination schemas, and CI.

## Base
- Branch: `feat/commerce-contracts-foundation-v0-1`
- Base (origin/main): `3156db7a2e3d9ad4d225487b1c8e43d5ce53cab4`

## Gate — exact commands and real results

Environment: isolated venv, CPython 3.14, deps `jsonschema referencing PyYAML
pytest` (matches `.github/workflows/ci.yml`).

### 1. Reference validator (`PYTHONPATH=src python -m dagr_commerce_contracts.validate`) — exit 0
```
[PASS] schemas-parse: 30/30 schema files parse and are valid Draft 2020-12
[PASS] positive-fixtures: 16/16 positive fixtures validate against their schema
[PASS] negative-fixtures: 10/10 negative fixtures fail for the intended path-scoped reason
[PASS] mutation-fixtures: 6/6 mutation fixtures fail for the intended path-scoped reason
[PASS] ecosystem-declarations: 13/13 .ecosystem declarations validate against vendored schemas
[PASS] no-aggregate-verdict: scanned 17 schemas and all fixtures for aggregate-verdict outcome values
[PASS] no-raw-sensitive-material: scanned 16 positive fixtures for raw sensitive material
exit_code=0 (all checks passed)
```

### 2. Version policy is not stale
```
python scripts/gen_version_policy.py   # wrote compatibility/version-policy.v0.1.json with 17 schema digests
git diff --exit-code compatibility/version-policy.v0.1.json   # no diff -> not stale
```

### 3. Test suite (`python -m pytest -q`)
```
11 passed
```

### 4. Whitespace / conflict-marker check
```
git diff --check   # clean
```

## Gate outcomes (per-check; no aggregate verdict is claimed)
- schemas-parse: PASS (30/30)
- positive-fixtures: PASS (16/16)
- negative-fixtures: PASS (10/10, path-scoped)
- mutation-fixtures: PASS (6/6, path-scoped)
- ecosystem-declarations: PASS (13/13)
- no-aggregate-verdict: PASS
- no-raw-sensitive-material: PASS
- pytest: 11 passed

## Claims supported
- The vocabulary parses, self-validates, and rejects malformed/mutated instances
  for the intended path-scoped reason.
- No schema enum value or fixture outcome field emits an aggregate
  trusted/safe/compliant/verified/governed verdict (enforced by a gate check).
- No positive fixture carries raw sensitive material under a sensitive-named
  field (enforced by a gate check).
- All 13 `.ecosystem/*.yaml` declarations validate against their vendored schema.

## Claims explicitly NOT supported
- No aggregate trusted/safe/compliant/verified/governed verdict of any object.
- No commerce protocol, payment rail, chain, PSP, merchant, wallet, or DAGR
  transport is required by any contract.
- No new DAGR binding, ARCS receipt format, verifier verdict, or Counterpedia
  record semantics is introduced. The evidence envelope references native
  payloads by digest/custody; it does not impersonate an ARCS receipt.
- This vocabulary is a local, versioned convention — not an upstream standard.

## Provenance note
This report was produced by re-running the full gate from a clean venv after the
lane's build step; results above are from actual execution, not hand-authored.

## Draft-PR readiness
Ready for a **draft** PR. Not pushed, no PR opened, not merged (operator action).
