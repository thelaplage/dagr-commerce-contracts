# BUILD_REPORT — Lane C1 conformance (dagr-commerce-contracts)

Adds fail-closed conformance tooling and release assurance on top of the merged
C0 contracts. Every result below is from actual execution in the C1 worktree.

## Base

- Branch: `feat/commerce-contracts-conformance-v0-1`
- Base SHA (HEAD at C1 start, = merge of C0 hardening PR #2):
  `43cdd1d9ab8c040e046f83e8173dec3425919ccb`
- C0 dependency: PR #1 head `f7979b68b97e904c8a7ffbae3f166d6674b2d834`,
  merge `147a1159ed0e3997775a30401b2f894848a24c6f`

## What changed (C1 additions)

### 1. Consumer fixtures (11 fixtures, 5 protocols)

`fixtures/consumer/` — protocol-neutral consumer projections for x402, ACP,
AP2, UCP, and Visa TAP. Each fixture exercises only shared contract fields;
native protocol objects are referenced by digest. Protocol-specific adapters
remain in their own repositories.

| Protocol  | Fixtures                                          |
|-----------|---------------------------------------------------|
| x402      | payment-requirement, payment-authorization, settlement |
| ACP       | intent, payment-authorization, order              |
| AP2       | intent, payment-authorization                     |
| UCP       | payment-requirement, payment-authorization        |
| Visa TAP  | payment-authorization                             |

Index: `fixtures/consumer/INDEX.consumer.json`.

### 2. Python TypedDict convenience types (generated)

`scripts/gen_types.py` → `src/dagr_commerce_contracts/types.py`.

Generates a TypedDict class for each of the 16 top-level commerce schemas,
plus a `SCHEMA_TO_TYPE` dispatch dict. The types are projections of the JSON
Schemas; the schemas remain authoritative. Freshness is enforced by
`test_gen_types_is_current`.

### 3. Release manifest (generated)

`scripts/gen_release_manifest.py` → `release/release-manifest.v0.2.0.json`.

Records the exact source commit and sha256/byte_length of every schema file.
A `--build` flag also records built package artifact digests. The
`release-manifest-current` CLI check and `test_release_manifest_schema_digests`
test verify that committed digests match on-disk files.

### 4. Extended CLI validator (5 new C1 checks)

`src/dagr_commerce_contracts/validate.py` gains five new independent,
path-scoped checks (checks #8–12):

| # | Check ID | What it verifies |
|---|----------|-----------------|
| 8 | `consumer-fixtures` | All 11 consumer fixtures validate against their commerce schema |
| 9 | `version-policy-current` | Schema digests in version-policy.v0.1.json match on-disk files; mismatch = undocumented breaking change |
| 10 | `compat-report-current` | Committed compat report matches fresh execution (no stale compatibility claim) |
| 11 | `release-manifest-current` | Schema digests in release manifest match on-disk files |
| 12 | `types-round-trip` | JSON → TypedDict → JSON is lossless for all 16 positive fixtures; round-tripped instances still validate |

Dependency-missing is exit code 2; content failure is exit code 1; all-pass is 0.
No aggregate verdict is emitted.

### 5. Extended test suite (11 new C1 tests → 23 total)

`tests/test_contracts.py` gains:
- `test_consumer_fixtures`
- `test_version_policy_current`
- `test_compat_report_current`
- `test_release_manifest_current`
- `test_types_round_trip`
- `test_types_module_importable`
- `test_types_cover_positive_fixture_schemas`
- `test_gen_types_is_current`
- `test_release_manifest_schema_digests`
- `test_consumer_fixture_digests_valid`
- `test_full_gate_c1_exit_code_zero`

### 6. Updated CI

`.github/workflows/ci.yml` adds three new gate steps that run on Python
3.11/3.12/3.13:
- `Generated types are not stale` (`gen_types.py` idempotency)
- `Release manifest schema-digests are not stale` (`gen_release_manifest.py --check`)
- Reference validator step updated to cover all 12 C0+C1 checks

### 7. Updated QUICKSTART.md

Documents all 12 checks (C0+C1), the consumer fixture table, and all
regeneration commands.

## Gate — exact commands and real results

Environment: worktree venv, Python 3.14 (host), pinned deps from
`constraints-ci.txt` (`jsonschema==4.26.0`, `referencing==0.37.0`,
`PyYAML==6.0.3`, `pytest==9.1.1` plus transitive pins). CI additionally runs
the 3.11/3.12/3.13 matrix.

### 1. Reference validator — C0+C1 gate (12 checks)
```
PYTHONPATH=src python -m dagr_commerce_contracts.validate
[PASS] schemas-parse: 30/30 schema files parse and are valid Draft 2020-12
[PASS] positive-fixtures: 16/16 positive fixtures validate against their schema
[PASS] negative-fixtures: 13/13 negative fixtures fail for the intended path-scoped reason
[PASS] mutation-fixtures: 13/13 mutation fixtures fail for the intended path-scoped reason
[PASS] ecosystem-declarations: 13/13 .ecosystem declarations validate against vendored schemas
[PASS] no-aggregate-verdict: scanned 17 schemas and all fixtures for aggregate-verdict outcome values
[PASS] no-raw-sensitive-material: scanned 54 fixtures (all classes) for sensitive-looking keys at any depth; 0 in positive fixtures, 3 expected smuggle key(s) in negative/mutation fixtures (rejected by schema validation)
[PASS] consumer-fixtures: 11/11 consumer fixtures validate against their schema
[PASS] version-policy-current: 17/17 schema digests match version-policy.v0.1.json
[PASS] compat-report-current: committed compat report matches fresh execution
[PASS] release-manifest-current: 17/17 schema digests match release-manifest.v0.2.0.json
[PASS] types-round-trip: 16/16 positive fixtures survive a lossless JSON round-trip
exit_code=0 (all checks passed)
```

### 2. Version policy is not stale
```
python scripts/gen_version_policy.py
# wrote compatibility/version-policy.v0.1.json with 17 schema digests
git diff --exit-code compatibility/version-policy.v0.1.json
# no diff → not stale
```

### 3. Generated types are not stale
```
python scripts/gen_types.py
# wrote src/dagr_commerce_contracts/types.py (16503 bytes, 16 TypedDicts)
git diff --exit-code src/dagr_commerce_contracts/types.py
# no diff → not stale
```

### 4. Release manifest schema-digests are not stale
```
python scripts/gen_release_manifest.py --check
release manifest schema-digests are current.
```

### 5. Test suite (23 tests)
```
python -m pytest -q
23 passed in 1.12s
```

### 6. Whitespace / conflict-marker check
```
git diff --check   # clean
```

## Files changed (C1)

**New:**
- `fixtures/consumer/INDEX.consumer.json`
- `fixtures/consumer/x402/payment-requirement.x402.json`
- `fixtures/consumer/x402/payment-authorization.x402.json`
- `fixtures/consumer/x402/settlement.x402.json`
- `fixtures/consumer/acp/intent.acp.json`
- `fixtures/consumer/acp/payment-authorization.acp.json`
- `fixtures/consumer/acp/order.acp.json`
- `fixtures/consumer/ap2/intent.ap2.json`
- `fixtures/consumer/ap2/payment-authorization.ap2.json`
- `fixtures/consumer/ucp/payment-requirement.ucp.json`
- `fixtures/consumer/ucp/payment-authorization.ucp.json`
- `fixtures/consumer/visa-tap/payment-authorization.visa-tap.json`
- `scripts/gen_types.py`
- `scripts/gen_release_manifest.py`
- `src/dagr_commerce_contracts/types.py`
- `release/release-manifest.v0.2.0.json`

**Modified:**
- `src/dagr_commerce_contracts/validate.py` (5 new C1 checks, updated docstring)
- `tests/test_contracts.py` (11 new C1 tests)
- `.github/workflows/ci.yml` (3 new gate steps)
- `QUICKSTART.md` (C1 sections, consumer fixture table)
- `BUILD_REPORT.md` (this file)

## C0 positive fixtures

All 16 C0 positive fixtures remain valid; no C0 schema was modified in C1.

## Claims supported (C1)

- All 12 C0+C1 checks pass from a clean run; each check is independently
  reported per-path/per-check with no aggregate verdict.
- Consumer fixtures for x402, ACP, AP2, UCP, and Visa TAP validate against
  the protocol-neutral commerce schemas using only shared fields.
- Python TypedDicts faithfully represent all 16 top-level schemas; every
  positive fixture survives a lossless JSON round-trip through the TypedDicts.
- Release manifest records the exact source commit and schema digests,
  generated from execution, never hand-authored; digests are verified on every
  CI run.
- Schema digests in version-policy and release manifest match on-disk files
  (missing-tool or content-failure distinguished by exit code).
- Mutation detection: the `version-policy-current` check would fail if any
  schema changed without regenerating the policy (potential breaking change).

## Claims explicitly NOT supported

- No aggregate trusted/safe/compliant/verified/governed verdict of any object.
- No commerce protocol, payment rail, chain, PSP, merchant, wallet, or DAGR
  transport is required by any contract.
- No new DAGR binding, ARCS receipt format, verifier verdict, or Counterpedia
  record semantics.
- Consumer fixtures prove protocol-neutral field coverage only; protocol-specific
  validation belongs in each protocol's own adapter repository.
- Release manifest package artifact digests are not populated (requires an
  explicit `--build` flag and the `build` package); schema digests only are
  committed.
- No publication to a public registry.

## Remaining blockers / unknowns

- None blocking a draft PR. The `--require-hashes` hardening for `constraints-ci.txt`
  remains a documented follow-up from C0 and is out of C1 scope.

## Draft-PR readiness

Ready for a **draft PR**. Not pushed, no PR opened, not merged (operator action).
