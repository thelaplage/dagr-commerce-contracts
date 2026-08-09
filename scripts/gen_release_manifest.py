#!/usr/bin/env python3
"""Generate the release manifest FROM EXECUTION.

The release manifest records, all from execution (never hand-authored):

  - ``source_base_commit`` — the branch BASE commit the release is built on top
    of (the hardened C0 merge). This is honestly labelled a *base*, NOT the
    exact source commit: a generated file that is itself committed cannot name
    the commit that introduces it. See ``release_commit`` / ``release_commit_binding``.
  - ``release_source_tree`` — a deterministic content digest over the packaged
    release payload (schemas + package source + fixtures + pyproject + README),
    excluding this manifest, so the manifest can bind the release content it
    describes without circularly referencing itself.
  - ``release_commit`` — ``null`` at generation time; the commit that adds this
    manifest is recorded externally (tag / release metadata) *after* commit.
  - ``build_binding`` — the SOURCE_DATE_EPOCH and toolchain versions the package
    artifacts were built under, so artifact digests are interpretable and
    (for the wheel) reproducible.
  - ``schemas`` — sha256 + byte_length of every committed commerce schema file.
  - ``package_artifacts`` — sha256 + byte_length of the built wheel and sdist,
    populated when ``--build`` is supplied.

Reproducibility note: the wheel is byte-reproducible under a fixed
SOURCE_DATE_EPOCH and toolchain. The sdist is a gzip container whose header
carries a timestamp, so its digest is an integrity digest of the artifact this
build produced, verified by presence (``--verify`` / the validator's
``package-artifacts`` check), not a claim that every rebuild yields identical
sdist bytes across toolchains.

Usage:
    python scripts/gen_release_manifest.py            # schema digests only
    python scripts/gen_release_manifest.py --build    # also build + hash artifacts
    python scripts/gen_release_manifest.py --check     # exit 1 if committed schema digests != fresh
    python scripts/gen_release_manifest.py --verify    # build + verify committed artifact digests
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
COMMERCE_DIR = REPO_ROOT / "schemas" / "commerce" / "v0.1"
OUT = REPO_ROOT / "release" / "release-manifest.v0.2.0.json"
DIST_DIR = REPO_ROOT / "dist"

# Paths whose committed content constitutes the release payload. The manifest
# itself is deliberately excluded so release_source_tree is non-circular.
PAYLOAD_PATHS = ["schemas", "src", "fixtures", "pyproject.toml", "README.md"]

# The hardened C0 (shared commerce contract) merge this lane is built on. It is
# the authoritative base whose schemas this release consumes; recording it — and
# NOT git HEAD — keeps the manifest from self-referencing a lane commit and keeps
# SOURCE_DATE_EPOCH stable across lane commits so the wheel stays reproducible.
HARDENED_C0_BASE = "43cdd1d9ab8c040e046f83e8173dec3425919ccb"


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _base_commit() -> str:
    """The hardened C0 shared-contract merge this release is built on.

    Honest label: this is the BASE (the consumed shared contract), NOT the
    release's own commit. Its ancestry to HEAD is verified so a wrong base can
    never be recorded silently.
    """
    try:
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", HARDENED_C0_BASE, "HEAD"],
            cwd=REPO_ROOT, check=True, capture_output=True,
        )
        return HARDENED_C0_BASE
    except Exception as exc:  # pragma: no cover - environment guard
        return f"UNVERIFIED:{HARDENED_C0_BASE}:{exc}"


def _source_date_epoch() -> int:
    """Deterministic SOURCE_DATE_EPOCH: commit time of the hardened C0 base.

    Tied to the base (not HEAD) so it does not move when a lane commit lands,
    keeping the recorded wheel digest reproducible.
    """
    try:
        return int(_git("show", "-s", "--format=%ct", HARDENED_C0_BASE))
    except Exception:
        return 0


def _toolchain() -> dict:
    import platform
    versions: dict[str, str] = {
        "python": platform.python_version(),
        "source_date_epoch": _source_date_epoch(),
    }
    for mod in ("build", "setuptools", "wheel"):
        try:
            import importlib.metadata as md
            versions[mod] = md.version(mod)
        except Exception:
            versions[mod] = "unavailable"
    return versions


def _release_source_tree() -> str:
    """Deterministic content digest of the packaged release payload.

    Hashes ``git hash-object`` of the working-tree content of every tracked file
    under PAYLOAD_PATHS (which excludes this manifest). The value is stable given
    the committed content and is re-verified by test_release_source_tree_matches.
    """
    try:
        listed = _git("ls-files", "--", *PAYLOAD_PATHS)
    except Exception as exc:  # pragma: no cover
        return f"UNKNOWN:{exc}"
    files = sorted(p for p in listed.splitlines() if p)
    h = hashlib.sha256()
    for rel in files:
        blob = _git("hash-object", "--", rel)
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(blob.encode("ascii"))
        h.update(b"\n")
    return "sha256:" + h.hexdigest()


def _schema_digests() -> list[dict]:
    entries = []
    for schema_file in sorted(COMMERCE_DIR.glob("*.json")):
        raw = schema_file.read_bytes()
        doc = json.loads(raw)
        entries.append({
            "file": f"schemas/commerce/v0.1/{schema_file.name}",
            "id": doc.get("$id"),
            "title": doc.get("title"),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "byte_length": len(raw),
        })
    return entries


def _kind_for(name: str) -> str:
    if name.endswith(".whl"):
        return "wheel"
    if name.endswith(".tar.gz"):
        return "sdist"
    return "unknown"


def build_artifacts() -> list[dict]:
    """Build the package hermetically and hash the artifacts.

    Uses ``--no-isolation`` so no build dependency is fetched from the network
    (the toolchain is already pinned in the environment), and a fixed
    SOURCE_DATE_EPOCH so the wheel is byte-reproducible.
    """
    import shutil
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    env = dict(os.environ)
    env["SOURCE_DATE_EPOCH"] = str(_source_date_epoch())
    try:
        subprocess.run(
            [sys.executable, "-m", "build", "--no-isolation", "--outdir", str(DIST_DIR)],
            cwd=REPO_ROOT,
            check=True,
            env=env,
        )
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"Package build failed: {exc}") from exc

    entries = []
    for artifact in sorted(DIST_DIR.glob("dagr_commerce_contracts-*")):
        raw = artifact.read_bytes()
        entries.append({
            "file": str(artifact.relative_to(REPO_ROOT)),
            "kind": _kind_for(artifact.name),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "byte_length": len(raw),
        })
    if not entries:
        raise SystemExit(f"No artifacts found in {DIST_DIR}")
    return entries


def build(include_artifacts: bool = False) -> dict:
    manifest: dict = {
        "artifact": "dagr-commerce-contracts release manifest",
        "version": "0.2.0",
        "source_base_commit": _base_commit(),
        "release_source_tree": _release_source_tree(),
        "release_commit": None,
        "release_commit_binding": (
            "This manifest is generated and committed as part of the release commit, so it "
            "cannot name that commit inside itself. source_base_commit is the BASE the release "
            "is built on (the hardened C0 merge), NOT the exact source commit. The release "
            "commit id is recorded externally (git tag / release metadata) after commit; verify "
            "the binding by confirming this file's payload matches release_source_tree."
        ),
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "build_binding": _toolchain(),
        "note": (
            "Schema digests are computed from on-disk schema files at generation time and "
            "verified on every CI run by the release-manifest-current check. Package artifact "
            "digests are populated when --build is supplied and verified by --verify / the "
            "validator's package-artifacts check. The wheel is byte-reproducible under the "
            "recorded build_binding; the sdist digest is an integrity digest of the artifact "
            "this build produced. This file is generated by scripts/gen_release_manifest.py."
        ),
        "schemas": _schema_digests(),
        "package_artifacts": build_artifacts() if include_artifacts else [],
    }
    return manifest


def render(manifest: dict) -> str:
    return json.dumps(manifest, indent=2) + "\n"


def _committed() -> dict | None:
    if not OUT.exists():
        return None
    return json.loads(OUT.read_text())


def _cmd_check() -> int:
    fresh = build(include_artifacts=False)
    committed = _committed()
    if committed is None:
        print("release manifest missing — run: python scripts/gen_release_manifest.py", flush=True)
        return 1
    if committed.get("schemas") != fresh["schemas"]:
        print(
            "release manifest schema-digests are stale — run: python scripts/gen_release_manifest.py",
            flush=True,
        )
        return 1
    print("release manifest schema-digests are current.")
    return 0


def _cmd_verify() -> int:
    """Build fresh and verify committed package-artifact digests.

    - Reproduces the build twice and asserts the wheel is byte-identical (build
      determinism in this environment).
    - Compares the freshly built digests to the committed manifest. The wheel
      digest must match when the recorded toolchain matches the current one; a
      toolchain difference is reported as a non-fatal notice (digests are
      toolchain-bound) rather than a spurious failure. A mismatch under an
      IDENTICAL toolchain is a hard failure.
    """
    committed = _committed()
    if committed is None:
        print("release manifest missing — run: python scripts/gen_release_manifest.py --build")
        return 1
    recorded = {a["file"]: a for a in committed.get("package_artifacts", [])}
    if not recorded:
        print("VERIFY FAIL: committed manifest has no package_artifacts — run --build")
        return 1

    first = build_artifacts()
    second = build_artifacts()
    fresh = {a["file"]: a for a in first}
    problems: list[str] = []
    notices: list[str] = []

    # determinism: wheel must be byte-identical across two builds
    for a in first:
        if a["kind"] == "wheel":
            b = next((x for x in second if x["file"] == a["file"]), None)
            if b is None or b["sha256"] != a["sha256"]:
                problems.append(f"non-deterministic wheel build: {a['file']}")

    same_toolchain = committed.get("build_binding") == _toolchain()
    for name, rec in recorded.items():
        got = fresh.get(name)
        if got is None:
            problems.append(f"artifact recorded but not produced: {name}")
            continue
        if got["sha256"] == rec["sha256"]:
            continue
        if rec.get("kind") == "wheel" and same_toolchain:
            problems.append(
                f"wheel digest mismatch under identical toolchain: {name} "
                f"(manifest={rec['sha256'][:16]}... fresh={got['sha256'][:16]}...)"
            )
        else:
            notices.append(
                f"{name}: digest differs from committed ({rec.get('kind')}); "
                f"toolchain {'identical' if same_toolchain else 'differs'} — "
                "artifact digests are build_binding-bound"
            )
    for n in notices:
        print(f"NOTICE: {n}")
    if problems:
        for p in problems:
            print(f"VERIFY FAIL: {p}")
        return 1
    print(f"release artifact digests verified ({len(recorded)} artifact(s)); wheel build is deterministic.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true",
                        help="also build the package and record artifact digests")
    parser.add_argument("--check", action="store_true",
                        help="exit 1 if committed schema-digests != fresh; ignores generated_at/source/package_artifacts")
    parser.add_argument("--verify", action="store_true",
                        help="build and verify committed package-artifact digests (release gate)")
    args = parser.parse_args(argv)

    if args.check:
        return _cmd_check()
    if args.verify:
        return _cmd_verify()

    fresh = build(include_artifacts=args.build)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(fresh))
    n = len(fresh["schemas"])
    na = len(fresh["package_artifacts"])
    print(f"wrote {OUT.relative_to(REPO_ROOT)} ({n} schema digests, {na} artifact digest(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
