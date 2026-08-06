# Compatibility and version policy

The machine-readable policy is `compatibility/version-policy.v0.1.json`. This
document is the human-readable companion. The JSON is generated from the
committed schema bytes by `scripts/gen_version_policy.py`; the digests it records
are never hand-authored, and `tests/test_contracts.py` fails if they go stale.

## Versioning

The vocabulary uses semantic versioning (`major.minor.patch`):

- **patch** — editorial or additive-optional changes. Positive fixtures remain
  valid.
- **minor** — additive changes (new optional fields, new object types). Positive
  fixtures remain valid.
- **major** — breaking changes. Requires a new versioned directory
  (`schemas/commerce/vX.Y/`) and a documented migration.

**Compatibility guarantee:** within a `major.minor` line, changes are additive
and non-breaking to the committed positive fixtures.

**Deprecation:** deprecated fields are marked in the schema `description` and
retained for at least one minor version before removal in a major version.

## Schema identifiers

Schema `$id` URIs use the `https://contracts.dagr-commerce.dev/schema/v0.1/`
namespace. These are **stable, repository-local, versioned identifiers only**.
They are not a published, registered, or upstream standard, and resolving them
over the network is neither required nor guaranteed. All validation is offline
against the files in this repository.

## Vendored ecosystem schemas

The 13 coordination schemas under `schemas/ecosystem/` are vendored verbatim
from `arcs-ecosystem-kit` at the commit recorded in
`schemas/ecosystem/PROVENANCE.yaml`, with per-file SHA-256 digests. They govern
the shape of the `.ecosystem/` declarations and let validation run offline from
a clean clone. Re-vendoring is a maintenance action via
`scripts/vendor_ecosystem_schemas.sh`.

## Claim discipline (carried into every version)

- No object or report emits an aggregate trusted/safe/compliant/verified/governed
  verdict.
- No contract requires a specific commerce protocol, payment rail, chain, PSP,
  merchant, wallet, or DAGR transport.
- The evidence-envelope is a projection that references native payloads by
  digest/custody; it is not an ARCS receipt or a verifier verdict.
