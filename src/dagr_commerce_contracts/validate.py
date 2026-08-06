"""Reference validator for dagr-commerce-contracts.

Runs the C0 gate as a set of independent, path-scoped checks and prints a
per-check report. It makes NO aggregate trusted/safe/compliant/verified/governed
claim: it reports per-check pass/fail only.

Checks
------
1. ``schemas-parse``        — every commerce and ecosystem schema parses and is a
                              structurally valid JSON Schema (Draft 2020-12).
2. ``positive-fixtures``    — every positive fixture validates against its schema.
3. ``negative-fixtures``    — every negative fixture FAILS, and the failure occurs
                              at the intended path/keyword (path-scoped reason).
4. ``mutation-fixtures``    — every mutation fixture FAILS at the intended
                              path/keyword.
5. ``ecosystem-declarations`` — every ``.ecosystem/*.yaml`` validates against its
                              vendored ecosystem coordination schema.
6. ``no-aggregate-verdict`` — no schema enum and no fixture outcome field uses an
                              aggregate-verdict token as a value.
7. ``no-raw-sensitive-material`` — no committed fixture carries a raw value under a
                              field whose name implies sensitive material.

Exit codes
----------
0  all checks passed.
1  at least one check produced a content failure.
2  a dependency was missing (e.g. jsonschema/referencing/PyYAML), so the gate
   could not run. A missing dependency is never reported as a pass.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMERCE_DIR = REPO_ROOT / "schemas" / "commerce" / "v0.1"
ECOSYSTEM_SCHEMA_DIR = REPO_ROOT / "schemas" / "ecosystem"
ECOSYSTEM_DECL_DIR = REPO_ROOT / ".ecosystem"
FIXTURES_DIR = REPO_ROOT / "fixtures"
FIXTURES_INDEX = FIXTURES_DIR / "INDEX.json"

# Aggregate-verdict tokens that must never appear as an outcome VALUE.
AGGREGATE_VERDICT_TOKENS = {"trusted", "safe", "compliant", "verified", "governed"}

# .ecosystem file -> vendored schema filename.
ECOSYSTEM_FILE_TO_SCHEMA = {
    "REPOSITORY.yaml": "ecosystem.repository.v0.1.schema.json",
    "AUTHORITY_REFERENCES.yaml": "ecosystem.authority-references.v0.1.schema.json",
    "ARCHITECTURE_PASSPORT.yaml": "ecosystem.architecture-passport.v0.1.schema.json",
    "BOUNDARIES.yaml": "ecosystem.boundaries.v0.1.schema.json",
    "RESPONSIBILITIES.yaml": "ecosystem.responsibilities.v0.1.schema.json",
    "CAPABILITY_BINDINGS.yaml": "ecosystem.capability-bindings.v0.1.schema.json",
    "CONTRACT_BINDINGS.yaml": "ecosystem.contract-bindings.v0.1.schema.json",
    "DEPENDENCIES.yaml": "ecosystem.dependencies.v0.1.schema.json",
    "LANES.yaml": "ecosystem.lanes.v0.1.schema.json",
    "COMPATIBILITY_PROJECTION.yaml": "ecosystem.compatibility-projection.v0.1.schema.json",
    "CONFORMANCE_PROJECTION.yaml": "ecosystem.conformance-projection.v0.1.schema.json",
    "EXCEPTIONS.yaml": "ecosystem.exceptions.v0.1.schema.json",
    "RELEASE_STATE.yaml": "ecosystem.release-state.v0.1.schema.json",
}

# Boundary-aware, case-insensitive matcher for property names that resemble
# sensitive CREDENTIAL material. Word boundaries are the start/end of the key or
# an underscore/hyphen, so "pan" matches but "japan"/"span" do not.
#
# NOTE (intentional divergence): this is a DEFENSE-IN-DEPTH scan over EVERY key at
# any depth in a fixture, so it lists credentials ONLY. The schema's
# common.schema.json#/$defs/safe_extension_key is broader — it ALSO rejects
# aggregate-verdict and native/ARCS-authority keys (verdict/trusted/object_type/
# envelope_kind/...) — but that restriction is scoped to the `extensions` bucket.
# Those tokens MUST NOT be added here: every top-level object legitimately carries
# a root `object_type`, so a global scan for it would fail valid fixtures. Keep the
# verdict/authority restriction in the schema (extensions-scoped) only.
SENSITIVE_KEY_RE = re.compile(
    r"(?i)(^|[_-])("
    r"card|pan|cvv|cvc|bearer|secret|client_secret|password|passwd|"
    r"private_key|privatekey|mandate_token|account_number|iban|routing|ssn|"
    r"api_key|apikey|access_token|refresh_token|token"
    r")($|[_-])"
)

# RFC 3339 date-time, e.g. 2026-08-05T12:00:00Z or 2026-08-05T12:00:00.5+02:00.
_RFC3339_DATE_TIME_RE = re.compile(
    r"^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})"
    r"[Tt](?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})(\.\d+)?"
    r"([Zz]|[+-]\d{2}:\d{2})$"
)


def _is_rfc3339_date_time(value: Any) -> bool:
    """Strict RFC 3339 date-time check.

    Rejects non-timestamps such as "not-a-timestamp" and impossible calendar
    dates; accepts "2026-08-05T12:00:00Z". Implemented without optional libraries
    (no rfc3339-validator dependency), so the gate is hermetic.
    """
    if not isinstance(value, str):
        return True
    m = _RFC3339_DATE_TIME_RE.match(value)
    if not m:
        return False
    year, month, day = int(m["year"]), int(m["month"]), int(m["day"])
    hour, minute, second = int(m["hour"]), int(m["minute"]), int(m["second"])
    if not (1 <= month <= 12 and 1 <= day <= 31):
        return False
    if hour > 23 or minute > 59 or second > 60:  # allow leap second :60
        return False
    try:
        _dt.date(year, month, day)  # rejects e.g. 2026-02-30
    except ValueError:
        return False
    return True


def _is_uri(value: Any) -> bool:
    """Minimal strict URI check: require a scheme and an authority or path.

    Rejects bare strings without a scheme; accepts e.g.
    https://github.com/owner/repo. No optional libraries required.
    """
    if not isinstance(value, str):
        return True
    try:
        parts = urlsplit(value)
    except Exception:
        return False
    if not parts.scheme:
        return False
    return bool(parts.netloc or parts.path)


_FORMAT_CHECKER = None


def _get_format_checker():
    """Build (once) a strict jsonschema FormatChecker for date-time and uri.

    Passed to every Draft202012Validator so the described `format: date-time`
    and `format: uri` constraints are actually enforced, not merely annotated.
    """
    global _FORMAT_CHECKER
    if _FORMAT_CHECKER is not None:
        return _FORMAT_CHECKER
    try:
        from jsonschema import FormatChecker
    except Exception as exc:  # pragma: no cover - environment guard
        raise DependencyMissing(f"jsonschema missing: {exc!r}") from exc
    checker = FormatChecker()
    checker.checks("date-time")(_is_rfc3339_date_time)
    checker.checks("uri")(_is_uri)
    _FORMAT_CHECKER = checker
    return checker


class DependencyMissing(Exception):
    """Raised when a required dependency is absent so the gate cannot run."""


class CheckResult:
    def __init__(self, check_id: str, passed: bool, summary: str,
                 details: list[str] | None = None):
        self.check_id = check_id
        self.passed = passed
        self.summary = summary
        self.details = details or []

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "passed": self.passed,
            "summary": self.summary,
            "details": self.details,
        }


def _import_deps():
    try:
        import jsonschema  # noqa: F401
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
        from referencing.jsonschema import DRAFT202012
    except Exception as exc:  # pragma: no cover - environment guard
        raise DependencyMissing(
            f"required validation dependency missing: {exc!r}. "
            "Install with: pip install jsonschema referencing PyYAML"
        ) from exc
    return Draft202012Validator, Registry, Resource, DRAFT202012


def _load_yaml():
    try:
        import yaml
    except Exception as exc:  # pragma: no cover
        raise DependencyMissing(f"PyYAML missing: {exc!r}") from exc
    return yaml


def _iter_json_schema_files(directory: Path) -> Iterable[Path]:
    return sorted(directory.glob("*.json"))


def _build_registry():
    Draft202012Validator, Registry, Resource, DRAFT202012 = _import_deps()
    registry = Registry()
    for schema_file in list(_iter_json_schema_files(COMMERCE_DIR)) + list(
        _iter_json_schema_files(ECOSYSTEM_SCHEMA_DIR)
    ):
        schema = json.loads(schema_file.read_text())
        resource = Resource.from_contents(schema, default_specification=DRAFT202012)
        sid = schema.get("$id")
        if sid:
            registry = registry.with_resource(uri=sid, resource=resource)
    return registry, Draft202012Validator


def check_schemas_parse() -> CheckResult:
    Draft202012Validator, _, _, _ = _import_deps()
    failures: list[str] = []
    count = 0
    for schema_file in list(_iter_json_schema_files(COMMERCE_DIR)) + list(
        _iter_json_schema_files(ECOSYSTEM_SCHEMA_DIR)
    ):
        count += 1
        try:
            schema = json.loads(schema_file.read_text())
        except Exception as exc:
            failures.append(f"{schema_file.name}: not valid JSON ({exc})")
            continue
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:
            failures.append(f"{schema_file.name}: not a valid Draft 2020-12 schema ({exc})")
    passed = not failures
    return CheckResult(
        "schemas-parse",
        passed,
        f"{count - len(failures)}/{count} schema files parse and are valid Draft 2020-12",
        failures,
    )


def _validator_for(schema_name: str, registry, Draft202012Validator):
    schema_path = COMMERCE_DIR / schema_name
    schema = json.loads(schema_path.read_text())
    return Draft202012Validator(
        schema, registry=registry, format_checker=_get_format_checker()
    )


def check_positive_fixtures(index: dict, registry, Draft202012Validator) -> CheckResult:
    failures: list[str] = []
    count = 0
    for entry in index.get("positive", []):
        count += 1
        fixture_path = FIXTURES_DIR / entry["file"]
        try:
            instance = json.loads(fixture_path.read_text())
        except Exception as exc:
            failures.append(f"{entry['file']}: not valid JSON ({exc})")
            continue
        validator = _validator_for(entry["schema"], registry, Draft202012Validator)
        errors = sorted(validator.iter_errors(instance), key=lambda e: e.json_path)
        if errors:
            msgs = "; ".join(f"{e.json_path}: {e.message}" for e in errors[:3])
            failures.append(f"{entry['file']} should be valid but failed: {msgs}")
    passed = not failures
    return CheckResult(
        "positive-fixtures",
        passed,
        f"{count - len(failures)}/{count} positive fixtures validate against their schema",
        failures,
    )


def _assert_expected_failure(entry: dict, errors: list) -> str | None:
    """Return an error string if the expected path-scoped failure was NOT observed."""
    if not errors:
        return f"{entry['file']} was expected to FAIL but validated cleanly"
    expect = entry.get("expect", {})
    want_keyword = expect.get("keyword")
    want_path = expect.get("path")
    want_msg = expect.get("message_contains")
    for e in errors:
        if want_keyword is not None and e.validator != want_keyword:
            continue
        if want_path is not None and want_path not in e.json_path:
            continue
        if want_msg is not None and want_msg not in e.message:
            continue
        return None  # matched
    observed = "; ".join(
        f"[keyword={e.validator} path={e.json_path}] {e.message}" for e in errors[:4]
    )
    return (
        f"{entry['file']} failed, but not for the intended path-scoped reason "
        f"(want keyword={want_keyword} path={want_path} msg~={want_msg}). "
        f"Observed: {observed}"
    )


def _check_negative_like(index_key: str, check_id: str, index: dict,
                         registry, Draft202012Validator) -> CheckResult:
    failures: list[str] = []
    count = 0
    for entry in index.get(index_key, []):
        count += 1
        fixture_path = FIXTURES_DIR / entry["file"]
        try:
            instance = json.loads(fixture_path.read_text())
        except Exception as exc:
            failures.append(f"{entry['file']}: not valid JSON ({exc})")
            continue
        validator = _validator_for(entry["schema"], registry, Draft202012Validator)
        errors = sorted(validator.iter_errors(instance), key=lambda e: e.json_path)
        problem = _assert_expected_failure(entry, errors)
        if problem:
            failures.append(problem)
    passed = not failures
    return CheckResult(
        check_id,
        passed,
        f"{count - len(failures)}/{count} {index_key} fixtures fail for the intended path-scoped reason",
        failures,
    )


def check_ecosystem_declarations(registry, Draft202012Validator) -> CheckResult:
    yaml = _load_yaml()
    failures: list[str] = []
    count = 0
    if not ECOSYSTEM_DECL_DIR.is_dir():
        return CheckResult("ecosystem-declarations", False,
                           ".ecosystem/ directory missing", ["expected .ecosystem/"])
    for decl_name, schema_name in ECOSYSTEM_FILE_TO_SCHEMA.items():
        count += 1
        decl_path = ECOSYSTEM_DECL_DIR / decl_name
        schema_path = ECOSYSTEM_SCHEMA_DIR / schema_name
        if not decl_path.is_file():
            failures.append(f"{decl_name}: missing")
            continue
        if not schema_path.is_file():
            failures.append(f"{schema_name}: vendored schema missing")
            continue
        try:
            instance = yaml.safe_load(decl_path.read_text())
        except Exception as exc:
            failures.append(f"{decl_name}: not valid YAML ({exc})")
            continue
        schema = json.loads(schema_path.read_text())
        validator = Draft202012Validator(
            schema, registry=registry, format_checker=_get_format_checker()
        )
        errors = sorted(validator.iter_errors(instance), key=lambda e: e.json_path)
        if errors:
            msgs = "; ".join(f"{e.json_path}: {e.message}" for e in errors[:3])
            failures.append(f"{decl_name}: {msgs}")
    passed = not failures
    return CheckResult(
        "ecosystem-declarations",
        passed,
        f"{count - len(failures)}/{count} .ecosystem declarations validate against vendored schemas",
        failures,
    )


def _walk(value: Any, path: str = "$"):
    yield path, value
    if isinstance(value, dict):
        for k, v in value.items():
            yield from _walk(v, f"{path}.{k}")
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from _walk(v, f"{path}[{i}]")


def check_no_aggregate_verdict() -> CheckResult:
    """No schema enum value and no fixture outcome value is an aggregate verdict."""
    failures: list[str] = []
    checked = 0
    # Schemas: no enum/const VALUE may be an aggregate verdict token.
    for schema_file in _iter_json_schema_files(COMMERCE_DIR):
        checked += 1
        schema = json.loads(schema_file.read_text())
        for path, value in _walk(schema):
            if path.endswith(".enum") and isinstance(value, list):
                for v in value:
                    if isinstance(v, str) and v.lower() in AGGREGATE_VERDICT_TOKENS:
                        failures.append(f"{schema_file.name}{path}: enum value '{v}' is an aggregate verdict")
    # Fixtures: no state/outcome-ish field may hold an aggregate verdict token.
    outcome_field_re = re.compile(r"\.(state|status|verdict|result|outcome|observation)$")
    for fixture_file in sorted(FIXTURES_DIR.rglob("*.json")):
        if fixture_file.name == "INDEX.json":
            continue
        try:
            instance = json.loads(fixture_file.read_text())
        except Exception:
            continue
        rel = fixture_file.relative_to(FIXTURES_DIR)
        for path, value in _walk(instance):
            if isinstance(value, str) and value.lower() in AGGREGATE_VERDICT_TOKENS:
                if outcome_field_re.search(path):
                    # Allowed only inside intentionally-invalid negative/mutation fixtures.
                    if rel.parts and rel.parts[0] == "positive":
                        failures.append(
                            f"{rel}{path}: positive fixture uses aggregate verdict '{value}'"
                        )
    passed = not failures
    return CheckResult(
        "no-aggregate-verdict",
        passed,
        f"scanned {checked} schemas and all fixtures for aggregate-verdict outcome values",
        failures,
    )


def _walk_keys(value: Any, path: str = "$"):
    """Yield (parent_path, key) for every object property name at any depth."""
    if isinstance(value, dict):
        for k, v in value.items():
            yield path, k
            yield from _walk_keys(v, f"{path}.{k}")
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from _walk_keys(v, f"{path}[{i}]")


def check_no_raw_sensitive_material() -> CheckResult:
    """Defense-in-depth: no sensitive-looking KEY name at any depth in a positive fixture.

    Scans ALL committed fixtures (positive, negative, mutation) and flags any
    property name that resembles sensitive material (card/pan/cvv/bearer/secret/
    password/private_key/token/...) at ANY nesting depth, not only leaf values
    under sensitive field names. A hit in a positive fixture fails the gate. A hit
    in a negative/mutation fixture is an intentional smuggle fixture whose
    rejection is proven by SCHEMA validation (the negative/mutation checks), so it
    is reported for visibility but does not fail this defense-in-depth scan.
    """
    positive_failures: list[str] = []
    smuggle_hits: list[str] = []
    files = 0
    for fixture_file in sorted(FIXTURES_DIR.rglob("*.json")):
        if fixture_file.name == "INDEX.json":
            continue
        files += 1
        try:
            instance = json.loads(fixture_file.read_text())
        except Exception:
            continue
        rel = fixture_file.relative_to(FIXTURES_DIR)
        is_positive = bool(rel.parts) and rel.parts[0] == "positive"
        for parent_path, key in _walk_keys(instance):
            if SENSITIVE_KEY_RE.search(key):
                loc = f"{rel}{parent_path}.{key}"
                if is_positive:
                    positive_failures.append(
                        f"{loc}: sensitive-looking key in a positive fixture; "
                        "use a redaction_marker or digest"
                    )
                else:
                    smuggle_hits.append(loc)
    passed = not positive_failures
    if passed:
        summary = (
            f"scanned {files} fixtures (all classes) for sensitive-looking keys at any "
            f"depth; 0 in positive fixtures, {len(smuggle_hits)} expected smuggle key(s) "
            "in negative/mutation fixtures (rejected by schema validation)"
        )
    else:
        summary = (
            f"scanned {files} fixtures; found {len(positive_failures)} sensitive-looking "
            "key(s) in positive fixtures"
        )
    return CheckResult(
        "no-raw-sensitive-material",
        passed,
        summary,
        positive_failures,
    )


def run_all() -> tuple[list[CheckResult], int]:
    """Run every check. Returns (results, exit_code)."""
    try:
        registry, Draft202012Validator = _build_registry()
        index = json.loads(FIXTURES_INDEX.read_text())
    except DependencyMissing as exc:
        return ([CheckResult("dependencies", False, str(exc))], 2)

    results = [
        check_schemas_parse(),
        check_positive_fixtures(index, registry, Draft202012Validator),
        _check_negative_like("negative", "negative-fixtures", index, registry, Draft202012Validator),
        _check_negative_like("mutation", "mutation-fixtures", index, registry, Draft202012Validator),
        check_ecosystem_declarations(registry, Draft202012Validator),
        check_no_aggregate_verdict(),
        check_no_raw_sensitive_material(),
    ]
    exit_code = 0 if all(r.passed for r in results) else 1
    return results, exit_code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="dagr-commerce-contracts reference validator")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)

    try:
        results, exit_code = run_all()
    except DependencyMissing as exc:
        print(f"DEPENDENCY-MISSING: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({
            "checks": [r.to_dict() for r in results],
            "exit_code": exit_code,
        }, indent=2))
    else:
        for r in results:
            status = "PASS" if r.passed else "FAIL"
            print(f"[{status}] {r.check_id}: {r.summary}")
            for d in r.details:
                print(f"        - {d}")
        print(f"\nexit_code={exit_code} "
              f"({'all checks passed' if exit_code == 0 else 'content failure' if exit_code == 1 else 'dependency missing'})")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
