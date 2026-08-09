# THIS FILE IS GENERATED — do not edit by hand.
# Re-generate with: python scripts/gen_types.py
# Source of truth: schemas/commerce/v0.1/*.schema.json
"""Python TypedDict convenience types for dagr-commerce-contracts objects.

These types are projections of the JSON Schema definitions into Python type
hints. They are NOT authoritative — the JSON Schemas are. Runtime constraint
enforcement is performed by the reference validator (dagr-commerce-validate /
dagr_commerce_contracts.validate), not by these TypedDicts.

Intended use: type-annotate dict variables that are known to hold a commerce
contract object, e.g.::

    from dagr_commerce_contracts.types import IntentT
    intent: IntentT = json.loads(payload)

Round-trip guarantee: any instance that validates against the corresponding
JSON Schema can be serialized with ``json.dumps`` and deserialized back with
``json.loads`` without loss of data (proven by the types-round-trip gate check).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
try:
    from typing import TypedDict
except ImportError:  # Python < 3.8
    from typing_extensions import TypedDict  # type: ignore[assignment]

class AgentIdentityT(TypedDict, total=False):
    """
    Convenience type for ``agent-identity.schema.json``. Source of truth:
    the JSON Schema. Authoritative constraint enforcement is performed by
    the reference validator, not this type. A protocol-neutral projection of
    an acting agent's identity. Any key material is referenced by digest
    only (public-key reference); no private key is ever carried. Relative
    $ref values resolve against this $id.
    """
    # Required fields: agent_ref, contract_version, object_type
    object_type: Any  # required
    contract_version: Any  # required
    created_at: Any
    agent_ref: Any  # required
    display_name: str
    public_key_digest: Any
    attestations: List[Any]
    native: Any
    observations: List[Any]
    extensions: Any


class CartT(TypedDict, total=False):
    """
    Convenience type for ``cart.schema.json``. Source of truth: the JSON
    Schema. Authoritative constraint enforcement is performed by the
    reference validator, not this type. A protocol-neutral projection of a
    cart of selected lines with a revision counter. Relative $ref values
    resolve against this $id.
    """
    # Required fields: cart_id, contract_version, lines, object_type
    object_type: Any  # required
    contract_version: Any  # required
    created_at: Any
    cart_id: Any  # required
    merchant_ref: Any
    revision: int
    lines: List[Any]  # required
    subtotal: Any
    total: Any
    native: Any
    observations: List[Any]
    extensions: Any


class CheckObservationSetT(TypedDict, total=False):
    """
    Convenience type for ``check-observation.schema.json``. Source of truth:
    the JSON Schema. Authoritative constraint enforcement is performed by
    the reference validator, not this type. A set of path-scoped check
    observations about one subject. Each observation reports only what was
    observed on its single named path. This object deliberately has no
    aggregate rollup, score, or verdict field: it never emits an aggregate
    trusted/safe/compliant/verified/governed result. Relative $ref values
    resolve against this $id.
    """
    # Required fields: contract_version, object_type, observation_set_id, observations
    object_type: Any  # required
    contract_version: Any  # required
    created_at: Any
    observation_set_id: Any  # required
    subject_ref: Any
    observations: List[Any]  # required
    extensions: Any


class EvidenceEnvelopeT(TypedDict, total=False):
    """
    Convenience type for ``evidence-envelope.schema.json``. Source of truth:
    the JSON Schema. Authoritative constraint enforcement is performed by
    the reference validator, not this type. A protocol-neutral evidence
    projection. It bundles references to protocol-native payloads (by digest
    and custody), references to commerce objects, path-scoped check
    observations, and redaction markers. It is a projection/reference layer
    only. It is NOT an ARCS receipt, NOT a verifier verdict, and NOT a
    coordination record; it carries no aggregate
    trusted/safe/compliant/verified/governed result. Relative $ref values
    resolve against this $id.
    """
    # Required fields: contract_version, envelope_id, envelope_kind, object_type, projections
    object_type: Any  # required
    envelope_kind: Any  # required
    contract_version: Any  # required
    envelope_id: Any  # required
    created_at: Any
    subject_ref: Any
    projections: List[Any]  # required
    referenced_objects: List[Any]
    observations: List[Any]
    redactions: List[Any]
    extensions: Any


class FulfillmentT(TypedDict, total=False):
    """
    Convenience type for ``fulfillment.schema.json``. Source of truth: the
    JSON Schema. Authoritative constraint enforcement is performed by the
    reference validator, not this type. A protocol-neutral projection of an
    observed fulfillment/delivery event. State is an operational observation
    including an explicit uncertain state; delivery atomicity relative to
    settlement is preserved by keeping settlement and fulfillment as
    distinct objects. Relative $ref values resolve against this $id.
    """
    # Required fields: contract_version, fulfillment_id, fulfillment_state, object_type
    object_type: Any  # required
    contract_version: Any  # required
    created_at: Any
    fulfillment_id: Any  # required
    order_ref: Any
    fulfillment_state: str  # required
    delivery_ref: Any
    native: Any
    observations: List[Any]
    extensions: Any


class IntentT(TypedDict, total=False):
    """
    Convenience type for ``intent.schema.json``. Source of truth: the JSON
    Schema. Authoritative constraint enforcement is performed by the
    reference validator, not this type. A protocol-neutral projection of
    what a principal intends to do (e.g. purchase, subscribe, pay, refund).
    Does not bind any specific commerce protocol, payment rail, chain, PSP,
    merchant, or wallet. Relative $ref values resolve against this $id.
    """
    # Required fields: contract_version, intent_id, intent_kind, object_type
    object_type: Any  # required
    contract_version: Any  # required
    intent_id: Any  # required
    created_at: Any
    intent_kind: str  # required
    description: str
    principal_ref: Any
    subject_ref: Any
    amount_limit: Any
    constraints_ref: Any
    native: Any
    observations: List[Any]
    extensions: Any


class MerchantT(TypedDict, total=False):
    """
    Convenience type for ``merchant.schema.json``. Source of truth: the JSON
    Schema. Authoritative constraint enforcement is performed by the
    reference validator, not this type. A protocol-neutral projection of a
    merchant/seller party. Carries no merchant-of-record binding and
    requires no specific PSP, rail, or platform. Relative $ref values
    resolve against this $id.
    """
    # Required fields: contract_version, merchant_ref, object_type
    object_type: Any  # required
    contract_version: Any  # required
    created_at: Any
    merchant_ref: Any  # required
    display_name: str
    jurisdiction_hint: str
    native: Any
    observations: List[Any]
    extensions: Any


class NativeEvidenceT(TypedDict, total=False):
    """
    Convenience type for ``native-evidence.schema.json``. Source of truth:
    the JSON Schema. Authoritative constraint enforcement is performed by
    the reference validator, not this type. A protocol-neutral wrapper that
    references one protocol-native object by digest and custody, preserving
    its native protocol, version, and object type. It is a reference to
    native evidence, not a replacement for it, and it must not be treated as
    an ARCS receipt or any verifier verdict. Relative $ref values resolve
    against this $id.
    """
    # Required fields: contract_version, evidence_id, native, object_type
    object_type: Any  # required
    contract_version: Any  # required
    created_at: Any
    evidence_id: Any  # required
    native: Any  # required
    subject_ref: Any
    observations: List[Any]
    extensions: Any


class OfferT(TypedDict, total=False):
    """
    Convenience type for ``offer.schema.json``. Source of truth: the JSON
    Schema. Authoritative constraint enforcement is performed by the
    reference validator, not this type. A protocol-neutral projection of an
    offer of goods or services. Relative $ref values resolve against this
    $id.
    """
    # Required fields: contract_version, object_type, offer_id
    object_type: Any  # required
    contract_version: Any  # required
    created_at: Any
    offer_id: Any  # required
    merchant_ref: Any
    items: List[Any]
    total: Any
    valid_until: Any
    native: Any
    observations: List[Any]
    extensions: Any


class OrderT(TypedDict, total=False):
    """
    Convenience type for ``order.schema.json``. Source of truth: the JSON
    Schema. Authoritative constraint enforcement is performed by the
    reference validator, not this type. A protocol-neutral projection of an
    order record. Order state is an operational observation including an
    explicit uncertain state. Relative $ref values resolve against this $id.
    """
    # Required fields: contract_version, object_type, order_id, order_state
    object_type: Any  # required
    contract_version: Any  # required
    created_at: Any
    order_id: Any  # required
    merchant_ref: Any
    cart_ref: Any
    order_state: str  # required
    amount: Any
    native: Any
    observations: List[Any]
    extensions: Any


class PaymentAuthorizationT(TypedDict, total=False):
    """
    Convenience type for ``payment-authorization.schema.json``. Source of
    truth: the JSON Schema. Authoritative constraint enforcement is
    performed by the reference validator, not this type. A protocol-neutral
    projection of an authorization to pay. The authorizing material (signed
    payload, token, mandate) is never embedded raw: it is carried as a
    redaction marker or a protocol-native reference. Relative $ref values
    resolve against this $id.
    """
    # Required fields: authorization_id, authorization_material, contract_version, object_type
    object_type: Any  # required
    contract_version: Any  # required
    created_at: Any
    authorization_id: Any  # required
    amount: Any
    payer_ref: Any
    payee_ref: Any
    requirement_ref: Any
    constraints_ref: Any
    one_time: bool
    expires_at: Any
    authorization_material: Any  # required
    native: Any
    observations: List[Any]
    extensions: Any


class PaymentRequirementT(TypedDict, total=False):
    """
    Convenience type for ``payment-requirement.schema.json``. Source of
    truth: the JSON Schema. Authoritative constraint enforcement is
    performed by the reference validator, not this type. A protocol-neutral
    projection of a requirement to pay (e.g. the shared view of a native
    payment challenge or requirements object). The native requirement is
    preserved by reference. No specific rail, chain, PSP, or method is
    required. Relative $ref values resolve against this $id.
    """
    # Required fields: amount, contract_version, object_type, requirement_id
    object_type: Any  # required
    contract_version: Any  # required
    created_at: Any
    requirement_id: Any  # required
    amount: Any  # required
    payee_ref: Any
    resource_ref: Any
    accepted_methods: List[Any]
    expires_at: Any
    native: Any
    observations: List[Any]
    extensions: Any


class PrincipalAuthorizationT(TypedDict, total=False):
    """
    Convenience type for ``principal-authorization.schema.json``. Source of
    truth: the JSON Schema. Authoritative constraint enforcement is
    performed by the reference validator, not this type. A protocol-neutral
    projection of a principal authorizing an agent to act within a scope.
    The authorizing material itself (mandate, signed grant, token) is never
    embedded raw: it is carried as a redaction marker or a protocol-native
    reference. Relative $ref values resolve against this $id.
    """
    # Required fields: agent_ref, authorization_id, authorization_material, contract_version, object_type, principal_ref
    object_type: Any  # required
    contract_version: Any  # required
    authorization_id: Any  # required
    created_at: Any
    principal_ref: Any  # required
    agent_ref: Any  # required
    scope: List[Any]
    constraints_ref: Any
    not_before: Any
    not_after: Any
    one_time: bool
    authorization_material: Any  # required
    native: Any
    observations: List[Any]
    extensions: Any


class RefundT(TypedDict, total=False):
    """
    Convenience type for ``refund.schema.json``. Source of truth: the JSON
    Schema. Authoritative constraint enforcement is performed by the
    reference validator, not this type. A protocol-neutral projection of a
    refund or cancellation event. A refund references the original order and
    payment authorization by reference; it never rewrites or replaces the
    original authorization object. Relative $ref values resolve against this
    $id.
    """
    # Required fields: contract_version, object_type, refund_id, refund_state
    object_type: Any  # required
    contract_version: Any  # required
    created_at: Any
    refund_id: Any  # required
    order_ref: Any
    original_payment_ref: Any
    amount: Any
    refund_state: str  # required
    reason: str
    native: Any
    observations: List[Any]
    extensions: Any


class SettlementT(TypedDict, total=False):
    """
    Convenience type for ``settlement.schema.json``. Source of truth: the
    JSON Schema. Authoritative constraint enforcement is performed by the
    reference validator, not this type. A protocol-neutral projection of an
    observed settlement attempt. Settlement state is an operational
    observation, including an explicit uncertain state; it is never an
    aggregate trusted/safe/compliant/verified/governed verdict. Relative
    $ref values resolve against this $id.
    """
    # Required fields: contract_version, object_type, settlement_id, settlement_state
    object_type: Any  # required
    contract_version: Any  # required
    created_at: Any
    settlement_id: Any  # required
    settlement_state: str  # required
    amount: Any
    authorization_ref: Any
    requirement_ref: Any
    settlement_reference_digest: Any
    native: Any
    observations: List[Any]
    extensions: Any


class SpendConstraintsT(TypedDict, total=False):
    """
    Convenience type for ``spend-constraints.schema.json``. Source of truth:
    the JSON Schema. Authoritative constraint enforcement is performed by
    the reference validator, not this type. A protocol-neutral projection of
    constraints on spending (caps, scopes, time windows, execution limits).
    These are declarative constraints only; enforcement and any allow/deny
    decision belong to a consumer, not to this vocabulary. Relative $ref
    values resolve against this $id.
    """
    # Required fields: constraints_id, contract_version, object_type
    object_type: Any  # required
    contract_version: Any  # required
    created_at: Any
    constraints_id: Any  # required
    per_transaction_cap: Any
    cumulative_cap: Any
    currency_scope: List[Any]
    allowed_merchants: List[Any]
    category_scope: List[Any]
    time_window: Dict[str, Any]
    max_executions: int
    native: Any
    observations: List[Any]
    extensions: Any


SCHEMA_TO_TYPE: Dict[str, type] = {
    "agent-identity.schema.json": AgentIdentityT,
    "cart.schema.json": CartT,
    "check-observation.schema.json": CheckObservationSetT,
    "evidence-envelope.schema.json": EvidenceEnvelopeT,
    "fulfillment.schema.json": FulfillmentT,
    "intent.schema.json": IntentT,
    "merchant.schema.json": MerchantT,
    "native-evidence.schema.json": NativeEvidenceT,
    "offer.schema.json": OfferT,
    "order.schema.json": OrderT,
    "payment-authorization.schema.json": PaymentAuthorizationT,
    "payment-requirement.schema.json": PaymentRequirementT,
    "principal-authorization.schema.json": PrincipalAuthorizationT,
    "refund.schema.json": RefundT,
    "settlement.schema.json": SettlementT,
    "spend-constraints.schema.json": SpendConstraintsT,
}
