# BUILD_REPORT — Lane C0 hardening (dagr-commerce-contracts)

Post-merge hardening of the protocol-neutral commerce evidence vocabulary. This
head turns constraints that were previously described in prose into constraints
enforced structurally by the schemas and the reference validator, and makes CI
hermetic. Every result below is from actual execution in this worktree.

## Base
- Branch: `fix/commerce-contracts-hardening-v0-1`
- Base (merged `main`): `147a1159ed0e3997775a30401b2f894848a24c6f`

## What changed
- **C0-1 — extensions can no longer smuggle sensitive material.**
  `common.schema.json` adds `safe_extension_key` (a string whose `not.pattern`
  rejects sensitive-looking names, boundary-aware and case-insensitive),
  `safe_value` (scalar/null | array of safe_value | safe_extension_object), and
  `safe_extension_object` (`propertyNames → safe_extension_key`,
  `additionalProperties → safe_value`). `extensions` now points at
  `safe_extension_object`, so sensitive keys are rejected at any nesting depth.
- **C0-2 — described-but-unenforced constraints are now enforced.**
  1. `date-time` (and `uri`) are checked by a strict `FormatChecker` in
     `validate.py`, passed to every validator (no optional libraries used).
  2. `digest` binds value shape to `algorithm`+`encoding` via `allOf`/if-then.
  3. `redaction_marker` binds `method` to required evidence (`digest_only` ⇒
     `digest`, `custody_reference` ⇒ `custody`, `masked` ⇒ `hint`).
  4. `non_negative_monetary_amount` is used for all price/charge/cap amounts.
  5. cart line `quantity` is `integer, minimum: 1`.
  6. every top-level object requires `contract_version`.
- **C0-3 — hermetic CI.** `constraints-ci.txt` pins exact `==` versions;
  `.github/workflows/ci.yml` installs `-r constraints-ci.txt` then `-e .`.
- **Validator defense-in-depth.** `check_no_raw_sensitive_material` now scans all
  fixtures for sensitive-looking property names at any depth (fails only on
  positive fixtures).

## Gate — exact commands and real results

Environment: isolated venv, CPython 3.14, pinned deps from `constraints-ci.txt`
(`jsonschema==4.26.0`, `referencing==0.37.0`, `PyYAML==6.0.3`, `pytest==9.1.1`
plus transitive pins). CI additionally runs the 3.9/3.12 matrix.

### 1. Reference validator (`PYTHONPATH=src python -m dagr_commerce_contracts.validate`) — exit 0
```
[PASS] schemas-parse: 30/30 schema files parse and are valid Draft 2020-12
[PASS] positive-fixtures: 16/16 positive fixtures validate against their schema
[PASS] negative-fixtures: 13/13 negative fixtures fail for the intended path-scoped reason
[PASS] mutation-fixtures: 11/11 mutation fixtures fail for the intended path-scoped reason
[PASS] ecosystem-declarations: 13/13 .ecosystem declarations validate against vendored schemas
[PASS] no-aggregate-verdict: scanned 17 schemas and all fixtures for aggregate-verdict outcome values
[PASS] no-raw-sensitive-material: scanned 40 fixtures (all classes) for sensitive-looking keys at any depth; 0 in positive fixtures, 3 expected smuggle key(s) in negative/mutation fixtures (rejected by schema validation)
exit_code=0 (all checks passed)
```

### 2. Version policy is not stale
```
python scripts/gen_version_policy.py   # wrote compatibility/version-policy.v0.1.json with 17 schema digests
git diff --exit-code compatibility/version-policy.v0.1.json   # no diff -> not stale (gen is idempotent)
```

### 3. Test suite (`python -m pytest -q`)
```
11 passed
```

### 4. Whitespace / conflict-marker check
```
git diff --check   # clean
```

## New negative/mutation fixtures (each fails at the intended path/keyword)
| Fixture | keyword | path |
| --- | --- | --- |
| `negative/intent.smuggled-extension-key.json` | `not` | `$.extensions` |
| `mutation/intent.nested-smuggled-extension.json` | `anyOf` | `$.extensions.detail` |
| `negative/intent.bad-timestamp.json` | `format` | `$.created_at` |
| `mutation/native-evidence.nonhex-digest-value.json` | `pattern` | `$.native.digest.value` |
| `mutation/evidence-envelope.digest-only-no-digest.json` | `required` | `$.redactions[0]` |
| `mutation/settlement.negative-amount.json` | `pattern` | `$.amount.value` |
| `mutation/cart.zero-quantity-line.json` | `minimum` | `$.lines[0].quantity` |
| `negative/order.missing-contract-version.json` | `required` | `$` |

## Claims supported (this head)
- The vocabulary parses, self-validates, and rejects malformed/mutated instances
  for the intended path-scoped reason.
- Sensitive material cannot be smuggled through `extensions` at any nesting
  depth; timestamps, digest shapes, redaction-marker evidence, non-negative
  amounts, positive cart quantities, and `contract_version` presence are all
  enforced structurally, each with a failing fixture.
- No schema enum value or fixture outcome field emits an aggregate
  trusted/safe/compliant/verified/governed verdict.
- CI installs a pinned dependency set rather than floating to latest.

## Claims explicitly NOT supported
- No aggregate trusted/safe/compliant/verified/governed verdict of any object.
- No commerce protocol, payment rail, chain, PSP, merchant, wallet, or DAGR
  transport is required by any contract.
- No new DAGR binding, ARCS receipt format, verifier verdict, or Counterpedia
  record semantics is introduced.
- `constraints-ci.txt` pins exact versions but does not yet use
  `--require-hashes`; artifact-hash verification is a documented follow-up.
- This vocabulary is a local, versioned convention — not an upstream standard.

## Provenance note
This report was produced by re-running the full gate from a clean venv after the
hardening edits; results above are from actual execution, not hand-authored.

## Draft-PR readiness
Ready for a **draft correction PR**. Not pushed, no PR opened, not merged
(operator action).
