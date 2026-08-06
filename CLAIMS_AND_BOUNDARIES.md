# Claims and boundaries

This document states exactly what `dagr-commerce-contracts` claims and, just as
importantly, what it does not. Every claim is tied to an artifact in this
repository and to the reference-validator gate that checks it.

## What this repository provides

A protocol-neutral, language-neutral **commerce evidence vocabulary** (v0.1.0):

1. JSON Schema Draft 2020-12 contracts under `schemas/commerce/v0.1/` with
   stable, versioned schema identifiers.
2. Core reference objects: intent, principal authorization, agent identity,
   merchant, offer, cart, spend constraints, payment requirement, payment
   authorization, settlement, order, fulfillment, refund, native evidence, and a
   path-scoped check-observation set.
3. A protocol-neutral evidence projection/envelope
   (`evidence-envelope.schema.json`) that references native payloads by digest
   and custody.
4. Redaction and sensitive-material rules (`REDACTION.md`) enforced structurally
   by the schemas.
5. Positive, negative, and mutation fixtures (`fixtures/`) and a reference
   validator (`src/dagr_commerce_contracts/validate.py`).
6. A machine-readable compatibility/version policy
   (`compatibility/version-policy.v0.1.json`).
7. The 13 `.ecosystem/` coordination declarations, schema-valid against the
   vendored arcs-ecosystem-kit v0.1 schemas.

## What this repository does not provide

- It does not implement an x402, ACP, AP2, UCP, or Visa TAP adapter.
- It does not define a new DAGR binding, a new ARCS receipt format, a new
  verifier verdict, Counterpedia record semantics, or any coordination authority.
- It does not make ACP and UCP interchangeable and expresses no cross-protocol
  equivalence.
- It is not an upstream standard. The `contracts.dagr-commerce.dev` schema `$id`
  namespace is a stable, repository-local, versioned identifier space only.

## Claim discipline

Every positive statement in or about this repository must be tied to:

1. an exact artifact path in this repository (or a pinned upstream reference);
2. a named check or fixture;
3. an actual reference-validator or test run; and
4. an explicit statement of what remains out of scope.

Per-check and per-path results are the only results this vocabulary produces.
**Aggregate verdicts are prohibited.** No object and no report defined here
emits an aggregate trusted / safe / compliant / verified / governed result. The
observation vocabulary is deliberately limited to `satisfied`, `not_satisfied`,
`not_applicable`, and `indeterminate`, and the `no-aggregate-verdict` check
scans the schemas and fixtures to enforce this.

## Native evidence and shared projections

Protocol-native objects remain authoritative for their own protocol meaning.
The shared contracts here are **projections/references only**. A
`protocol_native_reference` preserves the native protocol family, version,
object type, content digest, custody disposition, and redaction status. It does
not replace, and must not be serialized as, a native mandate, checkout session,
payment challenge, signed request, settlement response, order event, ARCS
receipt, or verifier verdict.

The `evidence_envelope` carries a fixed `envelope_kind` of
`protocol_neutral_evidence_projection` and has no verdict field, precisely so it
cannot be mistaken for a receipt or a governance decision.

## Financial and credential safety

No committed fixture contains a reusable credential, a real financial
identifier, a PAN-equivalent value, a private key, a bearer token, or a raw
secret. Sensitive native material is only ever referenced by a
`redaction_marker`, a `digest`, or a `custody_reference`. See `REDACTION.md`.
The `no-raw-sensitive-material` check scans positive fixtures for raw values
under sensitive-looking fields.

## Verified gates (this head)

The reference validator (`python3 -m dagr_commerce_contracts.validate`) runs
these independent, path-scoped checks; exact commands and counts are recorded in
`BUILD_REPORT.md`:

- `schemas-parse` — every schema is a valid Draft 2020-12 schema.
- `positive-fixtures` — every positive fixture validates against its schema.
- `negative-fixtures` / `mutation-fixtures` — every invalid fixture fails at the
  intended path/keyword.
- `ecosystem-declarations` — all 13 `.ecosystem/*.yaml` validate against the
  vendored schemas.
- `no-aggregate-verdict` — no aggregate-verdict token is used as an outcome value.
- `no-raw-sensitive-material` — no raw sensitive value in a positive fixture.
