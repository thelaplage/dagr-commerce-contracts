"""Test wrapper over the reference validator.

Each C0+C1 gate check becomes an individual, independently reported test so a
failure names exactly which gate failed. A missing dependency surfaces as a
distinct error rather than a silent pass.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dagr_commerce_contracts import validate as V  # noqa: E402


@pytest.fixture(scope="module")
def gate():
    try:
        registry, Draft = V._build_registry()
    except V.DependencyMissing as exc:  # pragma: no cover
        pytest.fail(f"dependency missing, gate could not run: {exc}")
    index = json.loads(V.FIXTURES_INDEX.read_text())
    return registry, Draft, index


def _assert_check(result: V.CheckResult):
    assert result.passed, f"{result.check_id} failed: {result.summary}\n" + "\n".join(result.details)


def test_schemas_parse():
    _assert_check(V.check_schemas_parse())


def test_positive_fixtures(gate):
    registry, Draft, index = gate
    _assert_check(V.check_positive_fixtures(index, registry, Draft))


def test_negative_fixtures(gate):
    registry, Draft, index = gate
    _assert_check(V._check_negative_like("negative", "negative-fixtures", index, registry, Draft))


def test_mutation_fixtures(gate):
    registry, Draft, index = gate
    _assert_check(V._check_negative_like("mutation", "mutation-fixtures", index, registry, Draft))


def test_ecosystem_declarations(gate):
    registry, Draft, _ = gate
    _assert_check(V.check_ecosystem_declarations(registry, Draft))


def test_no_aggregate_verdict():
    _assert_check(V.check_no_aggregate_verdict())


def test_no_raw_sensitive_material():
    _assert_check(V.check_no_raw_sensitive_material())


def test_full_gate_exit_code_zero():
    results, exit_code = V.run_all()
    failed = [r.check_id for r in results if not r.passed]
    assert exit_code == 0, f"gate exit_code={exit_code}, failed checks: {failed}"


def test_cli_runs_and_exits_zero():
    proc = subprocess.run(
        [sys.executable, "-m", "dagr_commerce_contracts.validate"],
        cwd=REPO_ROOT,
        env={"PYTHONPATH": str(SRC), "PATH": __import__("os").environ.get("PATH", "")},
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_version_policy_digests_match_committed_schemas():
    policy = json.loads((REPO_ROOT / "compatibility" / "version-policy.v0.1.json").read_text())
    for entry in policy["schemas"]:
        raw = (REPO_ROOT / entry["file"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == entry["sha256"], (
            f"stale digest for {entry['file']}; re-run scripts/gen_version_policy.py"
        )
        assert len(raw) == entry["byte_length"]


def test_vendored_ecosystem_schema_provenance():
    yaml = V._load_yaml()
    prov = yaml.safe_load((REPO_ROOT / "schemas" / "ecosystem" / "PROVENANCE.yaml").read_text())
    for entry in prov["files"]:
        raw = (REPO_ROOT / entry["path"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == entry["sha256"], (
            f"vendored schema {entry['path']} does not match recorded provenance digest"
        )


def test_compat_report_is_fresh():
    """The committed compatibility artifacts must match a fresh regeneration, so a
    schema tightening cannot land without its compatibility classification being
    (re)generated from execution."""
    import importlib.util

    gen_path = REPO_ROOT / "scripts" / "gen_compat_report.py"
    spec = importlib.util.spec_from_file_location("gen_compat_report", gen_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    data = mod.build()
    committed_json = (REPO_ROOT / "compatibility" / "compat-report.v0.1.json").read_text()
    committed_md = (REPO_ROOT / "compatibility" / "COMPATIBILITY_REPORT.md").read_text()
    assert committed_json == mod.render_json(data), "compat-report.v0.1.json is stale; run scripts/gen_compat_report.py"
    assert committed_md == mod.render_md(data), "COMPATIBILITY_REPORT.md is stale; run scripts/gen_compat_report.py"


# ---------------------------------------------------------------------------
# C1 gate tests
# ---------------------------------------------------------------------------

def test_consumer_fixtures(gate):
    registry, Draft, _ = gate
    _assert_check(V.check_consumer_fixtures(registry, Draft))


def test_version_policy_current():
    _assert_check(V.check_version_policy_current())


def test_compat_report_current():
    _assert_check(V.check_compat_report_current())


def test_release_manifest_current():
    _assert_check(V.check_release_manifest_current())


def test_types_round_trip(gate):
    registry, Draft, index = gate
    _assert_check(V.check_types_round_trip(index, registry, Draft))


def test_types_module_importable():
    """The generated types.py must be importable and must export SCHEMA_TO_TYPE."""
    from dagr_commerce_contracts import types as T
    assert hasattr(T, "SCHEMA_TO_TYPE"), "types.py missing SCHEMA_TO_TYPE dict"
    assert len(T.SCHEMA_TO_TYPE) >= 16, "SCHEMA_TO_TYPE should have at least 16 entries"


def test_types_cover_positive_fixture_schemas(gate):
    """Every schema referenced by a positive fixture must have a TypedDict in types.py."""
    from dagr_commerce_contracts import types as T
    _, _, index = gate
    missing = [
        entry["schema"]
        for entry in index.get("positive", [])
        if entry["schema"] not in T.SCHEMA_TO_TYPE
    ]
    assert not missing, f"No TypedDict for schemas: {missing}"


def test_gen_types_is_current():
    """The committed types.py must match what gen_types.py would produce today."""
    import importlib.util

    gen_path = REPO_ROOT / "scripts" / "gen_types.py"
    spec = importlib.util.spec_from_file_location("gen_types", gen_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fresh = mod.render()
    committed = (REPO_ROOT / "src" / "dagr_commerce_contracts" / "types.py").read_text()
    assert committed == fresh, "types.py is stale; run: python scripts/gen_types.py"


def test_release_manifest_schema_digests():
    """Schema digests in the release manifest match the on-disk schema files."""
    import hashlib
    manifest = json.loads(
        (REPO_ROOT / "release" / "release-manifest.v0.2.0.json").read_text()
    )
    for entry in manifest["schemas"]:
        raw = (REPO_ROOT / entry["file"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == entry["sha256"], (
            f"stale digest for {entry['file']}; run: python scripts/gen_release_manifest.py"
        )
        assert len(raw) == entry["byte_length"]


def test_consumer_fixture_digests_valid():
    """All sha-256 hex digests in consumer fixtures must be exactly 64 hex chars."""
    import re
    hex_re = re.compile(r"^[0-9a-fA-F]{64}$")
    index = json.loads(V.CONSUMER_INDEX.read_text())
    failures = []
    for entry in index.get("consumer", []):
        fp = V.FIXTURES_DIR / entry["file"]
        instance = json.loads(fp.read_text())

        def _check(obj, path="$"):
            if isinstance(obj, dict):
                if (obj.get("algorithm") == "sha-256"
                        and obj.get("encoding") == "hex"
                        and "value" in obj):
                    v = obj["value"]
                    if not hex_re.match(v):
                        failures.append(
                            f"{entry['file']}{path}.value: invalid sha-256 hex digest "
                            f"(len={len(v)}, value={v!r})"
                        )
                for k, v2 in obj.items():
                    _check(v2, f"{path}.{k}")
            elif isinstance(obj, list):
                for i, v2 in enumerate(obj):
                    _check(v2, f"{path}[{i}]")

        _check(instance)
    assert not failures, "\n".join(failures)


def test_full_gate_c1_exit_code_zero():
    """The full C0+C1 gate must pass with exit_code=0."""
    results, exit_code = V.run_all()
    failed = [r.check_id for r in results if not r.passed]
    assert exit_code == 0, f"gate exit_code={exit_code}, failed checks: {failed}"
