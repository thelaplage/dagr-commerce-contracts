# Compatibility report — dagr-commerce-contracts

Prior version: `0.1.0` → this version: `0.2.0`.

This hardening **shrinks the accepted-instance set**, so it is a corrective
change, not a backward-compatible extension. It is published under a new
version rather than silently under the prior compatibility claim. Each row
below is proven by running the reference validator against a committed
fixture (see `scripts/gen_compat_report.py`), so this report cannot drift
from the schemas.

- breaking corrections: **9**
- newly required fields: **1**

Because these repositories were created at Initial commit and C0 merged
exactly once, there are no external consumers to migrate; the schema `$id`
namespace stays at `v0.1` while the accepted set is corrected in place and
recorded here.

| id | boundary | classification | rejected at | proof fixture | migration |
|----|----------|----------------|-------------|---------------|-----------|
| extensions-credential | Raw credential key in `extensions` | breaking-correction | `not` @ `$.extensions` | `negative/intent.smuggled-extension-key.json` | Move the credential out of `extensions`; reference it by redaction_marker/digest/custody. |
| extensions-credential-nested | Nested credential key in `extensions` | breaking-correction | `anyOf` @ `$.extensions.detail` | `mutation/intent.nested-smuggled-extension.json` | Same as above; the restriction now applies at any nesting depth. |
| extensions-verdict | Aggregate-verdict key in `extensions` | breaking-correction | `not` @ `$.extensions` | `mutation/intent.verdict-extension-key.json` | Do not carry a verdict/trusted/safe/compliant/verified/governed field; observations are per-path only. |
| extensions-authority | Native/ARCS-authority-impersonating key in `extensions` | breaking-correction | `anyOf` @ `$.extensions.meta` | `mutation/intent.nested-authority-extension.json` | Do not place object_type/envelope_kind/arcs_receipt/verifier_verdict in extensions; use protocol_native_reference. |
| timestamp-format | Non-RFC3339 timestamp | breaking-correction | `format` @ `$.created_at` | `negative/intent.bad-timestamp.json` | Emit RFC 3339 date-time (e.g. 2026-08-05T12:00:00Z). |
| digest-shape | Digest value not bound to algorithm/encoding | breaking-correction | `pattern` @ `$.native.digest.value` | `mutation/native-evidence.nonhex-digest-value.json` | Provide a digest value matching the declared encoding/length (hex sha-256 = 64 hex chars). |
| redaction-conditional | `digest_only` redaction marker without a digest | breaking-correction | `required` @ `$.redactions[0]` | `mutation/evidence-envelope.digest-only-no-digest.json` | digest_only requires digest; custody_reference requires custody; masked requires hint. |
| non-negative-amount | Negative monetary amount | breaking-correction | `pattern` @ `$.amount.value` | `mutation/settlement.negative-amount.json` | Use a non-negative amount for price/charge/cap fields. |
| positive-quantity | Zero-quantity line | breaking-correction | `minimum` @ `$.lines[0].quantity` | `mutation/cart.zero-quantity-line.json` | Line quantity must be an integer >= 1. |
| required-contract-version | Missing root `contract_version` | newly-required | `required` @ `$` | `negative/order.missing-contract-version.json` | Add `contract_version` (e.g. "0.2.0") to every top-level object. |
