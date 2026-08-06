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
# Reference validator (per-check, path-scoped output):
PYTHONPATH=src python3 -m dagr_commerce_contracts.validate

# Machine-readable output:
PYTHONPATH=src python3 -m dagr_commerce_contracts.validate --json

# Full test suite:
python3 -m pytest -q
```

Exit codes for the reference validator:

- `0` — all checks passed.
- `1` — at least one content failure (a schema, fixture, declaration, or lint
  check failed).
- `2` — a required dependency was missing, so the gate could not run. A missing
  dependency is never reported as a pass.

## Regenerate derived files

```
# Re-derive the machine-readable version policy from the committed schemas:
python3 scripts/gen_version_policy.py

# Re-vendor the ecosystem schemas from a local arcs-ecosystem-kit checkout:
SRC=~/Developer/repos/arcs-ecosystem-kit scripts/vendor_ecosystem_schemas.sh
```

## Add a new object schema

1. Add `schemas/commerce/v0.1/<name>.schema.json` with a stable `$id` and
   `additionalProperties: false`.
2. Add a positive fixture and register it in `fixtures/INDEX.json`; add at least
   one negative and/or mutation fixture with an `expect` block.
3. Run `python3 scripts/gen_version_policy.py` and `python3 -m pytest -q`.
