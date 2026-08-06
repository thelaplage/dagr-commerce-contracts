# Quickstart

## Requirements

- Python 3.11+
- `jsonschema`, `referencing`, `PyYAML` (and `pytest` to run the test suite)

```
pip install jsonschema referencing PyYAML pytest
```

## Run the gate

From a clean clone, no network access required:

```
# Reference validator (per-check, path-scoped output — C0+C1 gate):
PYTHONPATH=src python3 -m dagr_commerce_contracts.validate

# Machine-readable output:
PYTHONPATH=src python3 -m dagr_commerce_contracts.validate --json

# Full test suite (23 tests, C0+C1):
python3 -m pytest -q
```

Exit codes for the reference validator:

- `0` — all checks passed.
- `1` — at least one content failure (a schema, fixture, declaration, or lint
  check failed).
- `2` — a required dependency was missing, so the gate could not run. A missing
  dependency is never reported as a pass.

## C0 checks (schemas + fixtures + declarations)

1. `schemas-parse` — every commerce and ecosystem schema is valid Draft 2020-12.
2. `positive-fixtures` — every positive fixture validates against its schema.
3. `negative-fixtures` — every negative fixture fails at the intended path/keyword.
4. `mutation-fixtures` — every mutation fixture fails at the intended path/keyword.
5. `ecosystem-declarations` — every `.ecosystem/*.yaml` validates against its vendored schema.
6. `no-aggregate-verdict` — no schema enum or fixture outcome uses an aggregate-verdict token.
7. `no-raw-sensitive-material` — no positive fixture carries a sensitive-looking key.

## C1 checks (conformance + compatibility + release assurance)

8. `consumer-fixtures` — all consumer fixtures (x402/ACP/AP2/UCP/Visa-TAP) validate
   using only protocol-neutral fields.
9. `version-policy-current` — schema digests in `compatibility/version-policy.v0.1.json`
   match on-disk files; a mismatch signals an undocumented breaking change.
10. `compat-report-current` — the committed compatibility report was generated from
    actual execution and is not stale.
11. `release-manifest-current` — schema digests in `release/release-manifest.v0.2.0.json`
    match on-disk files.
12. `types-round-trip` — every positive fixture survives a lossless JSON → TypedDict → JSON
    round-trip and the result still validates.

## Regenerate derived files

```
# Re-derive the machine-readable version policy from the committed schemas:
python3 scripts/gen_version_policy.py

# Re-generate the compat report from execution:
python3 scripts/gen_compat_report.py

# Re-generate Python TypedDict convenience types from schemas:
python3 scripts/gen_types.py

# Re-generate the release manifest (schema digests only; no package build):
python3 scripts/gen_release_manifest.py

# Re-generate the release manifest with built package artifact digests:
pip install build
python3 scripts/gen_release_manifest.py --build

# Re-vendor the ecosystem schemas from a local arcs-ecosystem-kit checkout:
SRC=~/Developer/repos/arcs-ecosystem-kit scripts/vendor_ecosystem_schemas.sh
```

## Consumer fixtures

Consumer fixtures in `fixtures/consumer/` show how each protocol maps to the
protocol-neutral commerce vocabulary. They exercise only the shared fields;
protocol-specific adapters remain in their own repositories.

| Protocol   | Fixtures |
|------------|----------|
| x402       | payment-requirement, payment-authorization, settlement |
| ACP        | intent, payment-authorization, order |
| AP2        | intent, payment-authorization |
| UCP        | payment-requirement, payment-authorization |
| Visa TAP   | payment-authorization |

Consumer fixture index: `fixtures/consumer/INDEX.consumer.json`.

## Add a new object schema

1. Add `schemas/commerce/v0.1/<name>.schema.json` with a stable `$id` and
   `additionalProperties: false`.
2. Add a positive fixture and register it in `fixtures/INDEX.json`; add at least
   one negative and/or mutation fixture with an `expect` block.
3. Run the derived-file generators:
   ```
   python3 scripts/gen_version_policy.py
   python3 scripts/gen_compat_report.py
   python3 scripts/gen_types.py
   python3 scripts/gen_release_manifest.py
   ```
4. Run `python3 -m pytest -q`.

## Python convenience types

`src/dagr_commerce_contracts/types.py` provides generated Python TypedDicts for
each commerce contract object type:

```python
from dagr_commerce_contracts.types import IntentT, PaymentRequirementT

intent: IntentT = json.loads(payload)
```

These types are projections of the JSON Schemas — the schemas remain the
authoritative source of truth. Re-generate after schema changes with
`python3 scripts/gen_types.py`.
