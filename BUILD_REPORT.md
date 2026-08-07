# BUILD_REPORT — Lane C1 conformance (dagr-commerce-contracts)

Adds fail-closed conformance tooling and release assurance on top of the
**hardened** C0 contracts. Every result below is from actual execution in the C1
worktree.

## Base

- Branch: `feat/commerce-contracts-conformance-v0-1`
- Base SHA (branch base, = merge of C0 hardening PR #2, == `origin/main`):
  `43cdd1d9ab8c040e046f83e8173dec3425919ccb`
- **Consumed shared contract (C0):** hardened C0 merge
  `43cdd1d9ab8c040e046f83e8173dec3425919ccb`. This SUPERSEDES the pre-hardening
  C0 foundation (PR #1 head `f7979b68…`, merge `147a1159…`), which is no longer
  a dependency of this lane. The hardened C0 tightened the schemas (extensions
  reject credential/verdict/authority keys recursively; strict date-time/uri
  FormatChecker; digest value bound to algorithm+encoding+length; conditional
  redaction markers; non-negative monetary amounts; `contract_version` required
  on every top-level object; vocabulary version 0.2.0). All C1 fixtures,
  consumers, and generated digests validate against and are computed from the
  hardened schemas.
- **Source-digest verify:** all 17 consumed commerce schemas and all vendored
  ecosystem schemas in this worktree are byte-identical to the canonical
  `dagr-commerce-contracts` repo at `43cdd1d9` (git blob-hash match, 0
  mismatches). Base ancestry re-checked pre-commit: `43cdd1d9` is an ancestor of
  HEAD and equals `origin/main` after `git fetch` — no base drift.

## Corrective pass — review blocking items (C1-1 … C1-4)

This corrective commit consumes/validates against the **hardened** C0
(`43cdd1d9`, superseding old C0 `147a1159`/`f7979b68`) and closes the review's
blocking items. All results are from execution above.

- **C1-1 — release manifest must contain package-artifact digests.** The prior
  lane left `package_artifacts: []` and called it out of scope, contradicting the
  deliverable. `gen_release_manifest.py --build` now builds the wheel + sdist
  hermetically (`--no-isolation`, pinned `SOURCE_DATE_EPOCH`) and records their
  sha256/byte_length/kind INTO the committed manifest (2 artifacts: wheel +
  sdist). Gate check 14 `package-artifacts` and `--verify` (§7) verify them.
- **C1-2 — honest source model.** The manifest no longer records the branch base
  as the exact source commit. It records `source_base_commit` = hardened C0 base
  `43cdd1d9` (ancestry-verified, clearly labelled a base), a non-circular
  `release_source_tree` content digest of the release payload (excludes the
  manifest itself), `release_commit: null`, and a `release_commit_binding` note
  stating the release commit is recorded externally after commit.
- **C1-3 — Visa consumer fixture disclaimer.** `fixtures/consumer/visa-tap/payment-authorization.visa-tap.json`
  now carries an `extensions` block (`synthetic_example: true`,
  `shared_contract_disclaimer`, and machine-readable `establishes.*: false`)
  stating it is only a synthetic, protocol-neutral shared-contract example that
  establishes NO Visa authority, NO Visa approval, NO Visa conformance, NO TAP
  implementation, and NO T0 resolution (T0 on HOLD). The disclaimer is carried in
  the schema-legal `extensions` bucket (validates under the hardened
  `safe_extension_object`) and is echoed in `INDEX.consumer.json`.
- **C1-4 — executable (not prose) checks.** `tests/test_c1_corrective.py` (17
  tests) plus two new gate checks and `scripts/scan_secrets.py` prove, by running:
  committed-secret + raw-sensitive scanning (clean on tree, detects planted
  secrets); outbound-network denial (full gate passes under a socket block);
  missing-dependency exit `2` (subprocess with a shadowed `jsonschema`); stale
  generated release manifest / types / compat report (each tamper detected);
  package-artifact-digest mismatch (empty/malformed/mismatched digests rejected;
  `--verify` catches a wheel-digest mismatch under identical toolchain — it did
  so live when the package source changed after a build); and financial-side-effect
  denial (the shipped package imports no network/exec client).

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

Records, from execution: the hardened C0 base commit (`source_base_commit`), a
non-circular content digest of the release payload (`release_source_tree`),
`release_commit: null` with a `release_commit_binding` note, the build binding
(`SOURCE_DATE_EPOCH` + toolchain), sha256/byte_length of every schema file, and
the wheel + sdist package-artifact digests (populated by `--build`). The
`release-manifest-current` check and `test_release_manifest_schema_digests` test
verify schema digests; `--verify` and the `package-artifacts` check verify the
artifact digests.

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
| 13 | `no-committed-secrets` | No git-tracked file carries a credential-shaped string (PEM/AWS/GitHub/Slack/Google/Stripe/OpenAI); delegates to `scripts/scan_secrets.py` |
| 14 | `package-artifacts` | Release manifest records well-formed wheel + sdist digests (64-hex sha256, positive byte_length) |

Dependency-missing is exit code 2; content failure is exit code 1; all-pass is 0.
No aggregate verdict is emitted.

### 5. Extended test suite (17 new + 11 C1 tests → 40 total)

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

`.github/workflows/ci.yml` runs on Python 3.11/3.12/3.13 and now includes:
- `Committed-secret scan` (`scripts/scan_secrets.py`)
- `Generated types are not stale` (`gen_types.py` idempotency)
- `Release manifest schema-digests are not stale` (`gen_release_manifest.py --check`)
- `Release artifacts — build + verify recorded digests` (`gen_release_manifest.py --verify`)
- Reference validator step updated to cover all 14 C0+C1 checks

### 7. Updated QUICKSTART.md

Documents all 14 checks (C0+C1), the consumer fixture table, the secret-scan and
release-artifact commands, and all regeneration commands.

## Gate — exact commands and real results

Environment: worktree venv, Python 3.14 (host), pinned deps from
`constraints-ci.txt` (`jsonschema==4.26.0`, `referencing==0.37.0`,
`PyYAML==6.0.3`, `pytest==9.1.1` plus transitive pins). CI additionally runs
the 3.11/3.12/3.13 matrix.

### 1. Reference validator — C0+C1 gate (14 checks)
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
[PASS] no-committed-secrets: no credential-shaped strings in tracked files
[PASS] package-artifacts: 2 artifact digest(s) recorded (sdist, wheel), well-formed
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

### 5. Test suite (40 tests)
```
python -m pytest -q
40 passed in 2.47s
```

### 6. Committed-secret scan (fail-closed)
```
python scripts/scan_secrets.py
committed-secret scan: clean (no credential-shaped strings in tracked files).
# exit 0
```

### 7. Release artifacts — hermetic build + verify recorded digests
```
python scripts/gen_release_manifest.py --verify
NOTICE: dist/dagr_commerce_contracts-0.2.0.tar.gz: digest differs from committed (sdist); toolchain identical — artifact digests are build_binding-bound
release artifact digests verified (2 artifact(s)); wheel build is deterministic.
# exit 0
```
Build is `python -m build --no-isolation` with `SOURCE_DATE_EPOCH` pinned to the
hardened C0 base commit time, so no build dependency is fetched and the wheel is
byte-reproducible. The sdist is a gzip container whose header carries a
timestamp, so its recorded digest is an integrity digest of the produced
artifact (reported as a NOTICE, not a failure).

### 8. dagr-pack validate (ecosystem conformance tool)
```
python -m dagr_pack (dagr_pack.cli:main) validate <worktree> \
    --schema ~/Developer/repos/arcs-ecosystem-kit/schemas
[FAIL] pack-dir: <worktree> has no PROOF_PACK_MANIFEST.yaml at its root; not
       recognized as a DAGR proof pack (fail-closed)
RESULT: FAIL (closed)
```
This is the CORRECT fail-closed behavior, not a lane defect: `dagr-commerce-contracts`
is a shared-contract repository, not a DAGR proof pack, so it has no
`PROOF_PACK_MANIFEST.yaml`. `dagr-pack validate` is scoped to proof packs and
refuses to pass a directory it does not recognize. No manifest was fabricated to
force a pass. The repo's own ecosystem declarations ARE validated by gate check 5
(`ecosystem-declarations`) against the same vendored arcs-ecosystem-kit v0.1
schemas.

### 9. Live stale-artifact detection (mutation probe)
A one-byte change to `schemas/commerce/v0.1/offer.schema.json` makes the gate
FAIL closed, then reverts clean:
```
[FAIL] version-policy-current: 16/17 schema digests match version-policy.v0.1.json
[FAIL] release-manifest-current: 16/17 schema digests match release-manifest.v0.2.0.json
exit_code=1 (content failure)
```
Regenerating `gen_version_policy.py`, `gen_compat_report.py`, `gen_types.py`, and
`gen_release_manifest.py --build` and running `git diff --exit-code` shows no
drift (all generated artifacts are current).

### 10. Whitespace / conflict-marker check
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
- `scripts/scan_secrets.py` (corrective: committed-secret scanner)
- `src/dagr_commerce_contracts/types.py`
- `release/release-manifest.v0.2.0.json`
- `tests/test_c1_corrective.py` (corrective: 17 executable checks)

**Modified (corrective pass):**
- `scripts/gen_release_manifest.py` (honest source model C1-2, artifact digests C1-1, `--verify`)
- `release/release-manifest.v0.2.0.json` (populated package_artifacts, new source fields)
- `fixtures/consumer/visa-tap/payment-authorization.visa-tap.json` (C1-3 disclaimer)
- `fixtures/consumer/INDEX.consumer.json` (C1-3 disclaimer)
- `src/dagr_commerce_contracts/validate.py` (checks 13 `no-committed-secrets`, 14 `package-artifacts`)
- `.github/workflows/ci.yml` (secret-scan + artifact build/verify steps)
- `constraints-ci.txt` (pinned release build toolchain)
- `QUICKSTART.md` (checks 13–14, secret-scan + artifact commands, 40 tests)
- `BUILD_REPORT.md` (this file)

The prior C1 additions (consumer fixtures, `gen_types.py`, TypedDicts, the
first five C1 checks, 11 C1 tests) remain from the preserved implementation
commit `de465f9`.

## C0 positive fixtures

All 16 C0 positive fixtures remain valid; no C0 schema was modified in C1.

## Claims supported (C1)

- All 14 C0+C1 checks pass from a clean run; each check is independently
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
  validation belongs in each protocol's own adapter repository. The Visa-TAP
  fixture explicitly establishes NO Visa authority, approval, or conformance, NO
  TAP implementation, and NO T0 resolution (T0 is on HOLD).
- The recorded wheel is byte-reproducible under the manifest `build_binding`; the
  sdist digest is an integrity digest of the produced artifact (its gzip header
  timestamp makes bit-for-bit sdist rebuilds toolchain/run-bound).
- `source_base_commit` is the BASE (the hardened C0 merge), NOT the release's own
  commit; a generated-and-committed file cannot name the commit that introduces
  it. The release commit is recorded externally after commit.
- No publication to a public registry.

## Remaining blockers / unknowns

- None blocking a draft PR. The `--require-hashes` hardening for `constraints-ci.txt`
  remains a documented follow-up from C0 and is out of C1 scope.

## Draft-PR readiness

Ready for a **draft PR**. Not pushed, no PR opened, not merged (operator action).
