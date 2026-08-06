# Redaction and sensitive-material rules

The commerce vocabulary must never carry sensitive native material as a raw
value. This document states the rule and shows how the schemas enforce it.

## Sensitive material classes

The following classes must never appear as a raw value in any object of this
vocabulary (`common.schema.json#/$defs/sensitive_material_class`):

- `private_key`
- `bearer_token`
- `payment_credential`
- `pan_equivalent` (primary account number or equivalent)
- `reusable_mandate`
- `raw_secret`
- `personal_data`
- `other`

## How sensitive material is carried

Sensitive material is only ever carried by **reference**, using one of:

1. **`redaction_marker`** — records that material was removed, its
   `material_class`, and the `method` (`omitted`, `digest_only`,
   `custody_reference`, `masked`, or `tokenized_reference`). It carries
   `redacted: true` (a fixed `const`), never the material itself. A `masked`
   marker may expose at most an 8-character, non-reconstructable `hint`.
2. **`digest`** — a cryptographic digest of the material (algorithm, encoding,
   value). The material is not present.
3. **`custody_reference`** — a pointer to where the native object is held
   (`caller_retained`, `external_store`, `not_retained`, or `inline_redacted`),
   with an optional non-secret `location_hint`. The `location_hint` must be an
   opaque store key, never a URL that embeds a credential.

## Structural enforcement

The rule is enforced by the schema shapes, not merely by convention:

- Fields that would carry authorizing material — `authorization_material` on
  `principal-authorization` and `payment-authorization` — are typed as
  `oneOf: [redaction_marker, protocol_native_reference]`. A raw string is
  rejected (`negative/payment-authorization.raw-material.json`).
- Key material on `agent-identity` is a `public_key_digest` (a `digest`) only;
  there is no field that accepts a private key.
- All core objects are **closed** (`additionalProperties: false`) with a single
  additive `extensions` bucket, so a field such as `card_number` cannot be
  smuggled in at the top level
  (`negative/payment-authorization.smuggled-pan-field.json`).
- The `extensions` bucket is itself closed against sensitive material. It is a
  `safe_extension_object`: its property names are validated by
  `propertyNames → safe_extension_key`, which **rejects** names that resemble
  sensitive fields (card/pan/cvv/cvc/bearer/secret/password/private_key/
  mandate_token/account_number/iban/routing/ssn/api_key/token/…). The match is
  case-insensitive and boundary-aware (so `pan` is rejected but `japan`/`span`
  are not), and because each nested value is itself a `safe_extension_object`,
  a sensitive key is rejected at **any nesting depth**. Proof:
  `negative/intent.smuggled-extension-key.json` (top-level `extensions.card_number`)
  and `mutation/intent.nested-smuggled-extension.json`
  (nested `extensions.detail.bearer_token`).
- A `redaction_marker`'s `method` is bound to its evidence: `digest_only`
  requires a `digest`, `custody_reference` requires a `custody`, and `masked`
  requires a `hint` (`mutation/evidence-envelope.digest-only-no-digest.json`).
- A `digest` value's shape is bound to its `algorithm` and `encoding` (a hex
  digest must be hexadecimal and the length the algorithm implies), so a stub
  value such as `"x"` is rejected
  (`mutation/native-evidence.nonhex-digest-value.json`).
- `protocol_native_reference` carries the native payload by `digest` + `custody`
  and an optional list of `redaction_marker`s; the payload is never embedded.

## Fixture policy

- No committed fixture contains a reusable credential, a real financial
  identifier, or a PAN-equivalent value. Placeholders used in intentionally
  invalid fixtures are obviously non-real (e.g. `PLACEHOLDER-NOT-A-REAL-PAN`).
- The `no-raw-sensitive-material` check in the reference validator scans every
  committed fixture (positive, negative, and mutation) for sensitive-looking
  property names at any nesting depth. A hit in a positive fixture fails the
  gate; the intentional smuggle keys in the negative/mutation fixtures are
  expected and are rejected by schema validation itself (defense in depth).
