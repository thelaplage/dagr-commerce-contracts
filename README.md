# dagr-commerce-contracts

A protocol-neutral, language-neutral **commerce evidence vocabulary**: JSON
Schema Draft 2020-12 contracts, fixtures, and a small reference validator that
the protocol proof packs (x402, ACP, AP2, UCP, Visa TAP) can consume by
**projection** — without redefining DAGR, ARCS, protocol-native semantics, or
verifier verdicts.

License: Apache-2.0 (see `LICENSE` and `NOTICE`).

## What this is

- A shared set of **schema contracts** for the core commerce concepts: intent,
  principal authorization, agent identity, merchant, offer, cart, spend
  constraints, payment requirement, payment authorization, settlement, order,
  fulfillment, refund, native evidence, and path-scoped check observations.
- A protocol-neutral **evidence projection/envelope** that references native
  payloads by digest and custody. It is **not** an ARCS receipt and **not** a
  verifier verdict.
- **Redaction rules** (`REDACTION.md`) so private keys, bearer tokens, payment
  credentials, PAN-equivalent data, reusable mandates, and raw secrets are never
  carried as raw values.
- Positive, negative, and mutation **fixtures** plus a reference **validator**
  that reports per-check, path-scoped results.
- A machine-readable **compatibility/version policy**
  (`compatibility/version-policy.v0.1.json`) and a complete **claims/boundaries**
  document (`CLAIMS_AND_BOUNDARIES.md`).
- The 13 `.ecosystem/` coordination declarations, schema-valid against the
  vendored arcs-ecosystem-kit v0.1 schemas.

## What this is not

- Not an x402 / ACP / AP2 / UCP / Visa TAP adapter.
- Not a new DAGR binding, ARCS receipt format, verifier verdict, Counterpedia
  record semantics, or coordination authority.
- Not an upstream standard. Schema `$id` URIs in the
  `contracts.dagr-commerce.dev` namespace are stable, repository-local,
  versioned identifiers only; network resolution is neither required nor implied.
- No object or report emits an aggregate **trusted / safe / compliant /
  verified / governed** verdict. Every check is per-path/per-check.

## Layout

```
schemas/commerce/v0.1/   canonical JSON Schema Draft 2020-12 contracts
schemas/ecosystem/       vendored arcs-ecosystem-kit v0.1 schemas + PROVENANCE.yaml
.ecosystem/              13 coordination declarations for this repository
fixtures/                positive/ negative/ mutation/ + INDEX.json manifest
src/dagr_commerce_contracts/validate.py   reference validator (per-check, fail-closed)
compatibility/version-policy.v0.1.json    machine-readable version/compat policy
CLAIMS_AND_BOUNDARIES.md REDACTION.md VERSION_POLICY.md   docs
```

## Running the gate

```
pip install jsonschema referencing PyYAML pytest
python3 -m pytest -q
# or the raw reference validator:
PYTHONPATH=src python3 -m dagr_commerce_contracts.validate
```

The validator exits `0` when all checks pass, `1` on a content failure, and `2`
when a required dependency is missing (a missing dependency is never reported as
a pass). See `QUICKSTART.md`.
