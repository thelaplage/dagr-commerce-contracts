#!/usr/bin/env python3
"""Generate Python TypedDict convenience types from commerce JSON Schemas.

The generated src/dagr_commerce_contracts/types.py provides a typed Python
interface for working with contract objects. The JSON Schemas remain the
authoritative source of truth; types.py is a derived projection.

Every class in types.py is generated directly from the schema's `properties`
and `required` arrays — the generator runs against the on-disk schema files so
the output is execution-derived, not hand-authored.

Usage:
    python scripts/gen_types.py           # write types.py
    python scripts/gen_types.py --check   # exit 1 if committed != fresh

The check in tests/test_contracts.py fails if the committed types.py is stale.
"""
from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
COMMERCE_DIR = REPO_ROOT / "schemas" / "commerce" / "v0.1"
OUT = REPO_ROOT / "src" / "dagr_commerce_contracts" / "types.py"

# JSON Schema type → Python annotation (simplified; nested objects map to Any)
_JS_TO_PY = {
    "string": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
    "null": "None",
    "array": "List[Any]",
    "object": "Dict[str, Any]",
}

# Top-level schemas with their TypedDict class names and object_type const values.
SCHEMAS = [
    ("agent-identity.schema.json", "AgentIdentityT", "agent_identity"),
    ("cart.schema.json", "CartT", "cart"),
    ("check-observation.schema.json", "CheckObservationSetT", "check_observation_set"),
    ("evidence-envelope.schema.json", "EvidenceEnvelopeT", "evidence_envelope"),
    ("fulfillment.schema.json", "FulfillmentT", "fulfillment"),
    ("intent.schema.json", "IntentT", "intent"),
    ("merchant.schema.json", "MerchantT", "merchant"),
    ("native-evidence.schema.json", "NativeEvidenceT", "native_evidence"),
    ("offer.schema.json", "OfferT", "offer"),
    ("order.schema.json", "OrderT", "order"),
    ("payment-authorization.schema.json", "PaymentAuthorizationT", "payment_authorization"),
    ("payment-requirement.schema.json", "PaymentRequirementT", "payment_requirement"),
    ("principal-authorization.schema.json", "PrincipalAuthorizationT", "principal_authorization"),
    ("refund.schema.json", "RefundT", "refund"),
    ("settlement.schema.json", "SettlementT", "settlement"),
    ("spend-constraints.schema.json", "SpendConstraintsT", "spend_constraints"),
]


def _py_type(prop: dict) -> str:
    """Return a Python type annotation for a JSON Schema property definition."""
    if "$ref" in prop:
        return "Any"
    t = prop.get("type")
    if isinstance(t, list):
        types = [_JS_TO_PY.get(x, "Any") for x in t if x != "null"]
        base = types[0] if len(types) == 1 else f"Union[{', '.join(types)}]"
        return f"Optional[{base}]" if "null" in t else base
    return _JS_TO_PY.get(t, "Any") if t else "Any"


def _generate_class(schema_file: str, class_name: str) -> str:
    schema = json.loads((COMMERCE_DIR / schema_file).read_text())
    props = schema.get("properties", {})
    required = set(schema.get("required", []))
    title = schema.get("title", schema_file)
    doc = schema.get("description", "")

    lines = [f'class {class_name}(TypedDict, total=False):']
    doc_lines = textwrap.wrap(
        f"Convenience type for ``{schema_file}``. "
        f"Source of truth: the JSON Schema. Authoritative constraint enforcement "
        f"is performed by the reference validator, not this type. {doc}",
        width=72,
    )
    lines.append(f'    """')
    for dl in doc_lines:
        lines.append(f"    {dl}")
    lines.append(f'    """')
    lines.append(f"    # Required fields: {', '.join(sorted(required)) or '(none)'}")

    for prop_name, prop_def in props.items():
        py_t = _py_type(prop_def)
        req_marker = "  # required" if prop_name in required else ""
        lines.append(f"    {prop_name}: {py_t}{req_marker}")

    return "\n".join(lines)


def render() -> str:
    header = '''\
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

'''
    class_blocks = []
    for schema_file, class_name, _ in SCHEMAS:
        class_blocks.append(_generate_class(schema_file, class_name))

    schema_to_type_lines = ["SCHEMA_TO_TYPE: Dict[str, type] = {"]
    for schema_file, class_name, _ in SCHEMAS:
        schema_to_type_lines.append(f'    "{schema_file}": {class_name},')
    schema_to_type_lines.append("}")

    return header + "\n\n\n".join(class_blocks) + "\n\n\n" + "\n".join(schema_to_type_lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="exit 1 if committed types.py does not match fresh output")
    args = parser.parse_args(argv)

    fresh = render()

    if args.check:
        committed = OUT.read_text() if OUT.exists() else ""
        if committed != fresh:
            print("types.py is stale — run: python scripts/gen_types.py", flush=True)
            return 1
        print("types.py is current.")
        return 0

    OUT.write_text(fresh)
    print(f"wrote {OUT} ({len(fresh)} bytes, {len(SCHEMAS)} TypedDicts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
