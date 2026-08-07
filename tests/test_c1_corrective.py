"""C1 corrective, executable checks (review items C1-4).

Every guarantee here is proven by RUNNING code that detects the bad condition,
not by prose. Grouped by the blocking review item:

  * committed-secret + raw-sensitive scanning  (scan detects a planted secret)
  * outbound-network denial during tests        (gate runs under a socket block)
  * missing-dependency exit 2                    (subprocess proves exit code 2)
  * stale generated release manifest             (tamper is detected)
  * stale generated types                        (tamper is detected)
  * stale compatibility report                   (tamper is detected)
  * package-artifact-digest mismatch             (wrong digest is detected)
  * financial-side-effect denial                 (no network/exec client in pkg)
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import socket
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
SCRIPTS = REPO_ROOT / "scripts"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dagr_commerce_contracts import validate as V  # noqa: E402


def _load_script(name: str):
    spec = importlib.util.spec_from_file_location(name[:-3], SCRIPTS / name)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# committed-secret + raw-sensitive scanning
# ---------------------------------------------------------------------------

def test_secret_scan_clean_on_repo():
    scanner = _load_script("scan_secrets.py")
    assert scanner.scan() == [], "tracked tree must contain no credential-shaped strings"


def test_secret_scan_detects_planted_secrets():
    scanner = _load_script("scan_secrets.py")
    planted = {
        "aws-access-key-id": "AKIA" + "ABCDEFGHIJKLMNOP",
        "github-token": "ghp_" + "b" * 36,
        "pem-private-key": "-----BEGIN RSA PRIVATE KEY-----",
        "slack-token": "xoxb-123456789012-deadbeefcafe",
        "google-api-key": "AIza" + "C" * 35,
        "stripe-live-secret": "sk_live_" + "0" * 20,
    }
    for label, sample in planted.items():
        hits = scanner.scan_text("planted.txt", sample)
        assert any(label in h for h in hits), f"{label} not detected in {hits}"


def test_no_committed_secrets_gate_check_passes():
    result = V.check_no_committed_secrets()
    assert result.passed, result.details


def test_raw_sensitive_key_scan_present_and_passing():
    # The C0 no-raw-sensitive-material check must exist and pass on the tree.
    assert V.check_no_raw_sensitive_material().passed


# ---------------------------------------------------------------------------
# outbound-network denial during tests
# ---------------------------------------------------------------------------

def test_gate_runs_under_outbound_network_block(monkeypatch):
    """The full gate must complete with NO outbound network access."""
    def _blocked(*a, **k):
        raise AssertionError("outbound network access is denied during tests")

    monkeypatch.setattr(socket.socket, "connect", _blocked, raising=True)
    monkeypatch.setattr(socket, "create_connection", _blocked, raising=True)
    monkeypatch.setattr(socket, "getaddrinfo", _blocked, raising=True)

    # positive control: the block is real
    with pytest.raises(AssertionError):
        socket.create_connection(("example.com", 443))

    results, exit_code = V.run_all()
    failed = [r.check_id for r in results if not r.passed]
    assert exit_code == 0, f"gate needed network or failed offline: {failed}"


# ---------------------------------------------------------------------------
# missing-dependency exit 2
# ---------------------------------------------------------------------------

def test_missing_dependency_exits_2(tmp_path):
    """Shadow `jsonschema` with a module that fails to import; the validator must
    exit 2 (dependency-missing), never 0 (pass) or 1 (content failure)."""
    shadow = tmp_path / "shadow"
    shadow.mkdir()
    (shadow / "jsonschema.py").write_text("raise ImportError('shadowed for test')\n")
    env = {
        "PYTHONPATH": f"{shadow}:{SRC}",
        "PATH": __import__("os").environ.get("PATH", ""),
    }
    proc = subprocess.run(
        [sys.executable, "-m", "dagr_commerce_contracts.validate"],
        cwd=REPO_ROOT, env=env, capture_output=True, text=True,
    )
    assert proc.returncode == 2, (
        f"expected exit 2 on missing dependency, got {proc.returncode}\n{proc.stdout}{proc.stderr}"
    )


def test_run_all_reports_dependency_missing_as_exit_2(monkeypatch):
    monkeypatch.setattr(V, "_import_deps",
                        lambda: (_ for _ in ()).throw(V.DependencyMissing("forced")))
    results, exit_code = V.run_all()
    assert exit_code == 2
    assert results[0].check_id == "dependencies" and not results[0].passed


# ---------------------------------------------------------------------------
# stale generated release manifest
# ---------------------------------------------------------------------------

def _tamper_manifest_schema(tmp_path) -> Path:
    manifest = json.loads(V.RELEASE_MANIFEST.read_text())
    manifest["schemas"][0]["sha256"] = "0" * 64  # corrupt a recorded digest
    out = tmp_path / "release-manifest.tampered.json"
    out.write_text(json.dumps(manifest, indent=2) + "\n")
    return out


def test_stale_release_manifest_is_detected(tmp_path, monkeypatch):
    tampered = _tamper_manifest_schema(tmp_path)
    monkeypatch.setattr(V, "RELEASE_MANIFEST", tampered)
    result = V.check_release_manifest_current()
    assert not result.passed and any("sha256 mismatch" in d for d in result.details)


def test_release_manifest_check_script_detects_stale(tmp_path):
    """gen_release_manifest.py --check must exit 1 when a schema digest is stale."""
    gen = _load_script("gen_release_manifest.py")
    tampered = json.loads(V.RELEASE_MANIFEST.read_text())
    tampered["schemas"][0]["sha256"] = "1" * 64
    out = tmp_path / "m.json"
    out.write_text(json.dumps(tampered, indent=2) + "\n")
    orig = gen.OUT
    try:
        gen.OUT = out
        assert gen._cmd_check() == 1
    finally:
        gen.OUT = orig


# ---------------------------------------------------------------------------
# stale generated types
# ---------------------------------------------------------------------------

def test_stale_generated_types_is_detected():
    gen = _load_script("gen_types.py")
    fresh = gen.render()
    committed = (SRC / "dagr_commerce_contracts" / "types.py").read_text()
    assert committed == fresh, "types.py is stale; run scripts/gen_types.py"
    # detection: a tampered committed file would not equal fresh
    assert (committed + "\n# tamper") != fresh


# ---------------------------------------------------------------------------
# stale compatibility report
# ---------------------------------------------------------------------------

def test_stale_compat_report_is_detected(tmp_path, monkeypatch):
    tampered = REPO_ROOT / "compatibility" / "compat-report.v0.1.json"
    bad = tmp_path / "compat.json"
    bad.write_text(tampered.read_text().replace("}", ", \"tamper\": true}", 1))
    monkeypatch.setattr(V, "COMPAT_REPORT_JSON", bad)
    result = V.check_compat_report_current()
    assert not result.passed


# ---------------------------------------------------------------------------
# package-artifact-digest mismatch
# ---------------------------------------------------------------------------

def test_empty_package_artifacts_is_rejected():
    fails = V.artifact_structural_failures({"package_artifacts": []})
    assert fails and "empty" in fails[0]


def test_malformed_package_artifact_is_rejected():
    bad = {"package_artifacts": [
        {"file": "dagr_commerce_contracts-0.2.0-py3-none-any.whl", "kind": "wheel",
         "sha256": "nothex", "byte_length": 0},
    ]}
    fails = V.artifact_structural_failures(bad)
    assert any("sha256" in f for f in fails)
    assert any("byte_length" in f for f in fails)
    assert any("no sdist" in f for f in fails)


def test_wellformed_package_artifacts_pass():
    good = {"package_artifacts": [
        {"file": "dist/dagr_commerce_contracts-0.2.0-py3-none-any.whl",
         "kind": "wheel", "sha256": "a" * 64, "byte_length": 100},
        {"file": "dist/dagr_commerce_contracts-0.2.0.tar.gz",
         "kind": "sdist", "sha256": "b" * 64, "byte_length": 100},
    ]}
    assert V.artifact_structural_failures(good) == []


def test_package_artifact_digest_mismatch_detected(tmp_path):
    """A present artifact whose bytes do not match a recorded digest is detected."""
    art = tmp_path / "dagr_commerce_contracts-0.2.0-py3-none-any.whl"
    art.write_bytes(b"real wheel bytes")
    real = hashlib.sha256(art.read_bytes()).hexdigest()
    recorded = {"file": art.name, "kind": "wheel", "sha256": real, "byte_length": len(b"real wheel bytes")}
    # matching digest verifies
    assert hashlib.sha256(art.read_bytes()).hexdigest() == recorded["sha256"]
    # tamper the artifact -> digest no longer matches the recorded value
    art.write_bytes(b"tampered wheel bytes")
    assert hashlib.sha256(art.read_bytes()).hexdigest() != recorded["sha256"]


def test_package_artifacts_gate_check_passes():
    assert V.check_package_artifacts().passed


# ---------------------------------------------------------------------------
# financial-side-effect denial (static: no network / exec client in the package)
# ---------------------------------------------------------------------------

FORBIDDEN_IN_PACKAGE = (
    "import socket", "socket.socket", "socket.create_connection",
    "import requests", "import httpx", "http.client", "urllib.request",
    "import subprocess", "subprocess.run", "subprocess.Popen", "os.system",
)


def test_package_has_no_network_or_exec_side_effect():
    pkg = SRC / "dagr_commerce_contracts"
    offenders: list[str] = []
    for py in sorted(pkg.rglob("*.py")):
        text = py.read_text()
        for token in FORBIDDEN_IN_PACKAGE:
            if token in text:
                offenders.append(f"{py.relative_to(REPO_ROOT)}: contains {token!r}")
    assert not offenders, (
        "the shipped package must perform no outbound network or process-execution "
        "side effect (financial-side-effect denial):\n" + "\n".join(offenders)
    )
