"""Test wrapper over the reference validator.

Each C0 gate check becomes an individual, independently reported test so a
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
