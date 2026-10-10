"""Real frozen executable checks against synthetic, isolated targets."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

import pytest

from privacy_guard import __version__
from test_advisory import snapshot
from test_guard import commit, put, synthetic_secret


def bundle_directory():
    configured = os.environ.get("PRIVACY_GUARD_TEST_BUNDLE")
    return (
        Path(configured)
        if configured
        else (
            Path(__file__).resolve().parents[1]
            / "dist"
            / f"privacy-guard-{__version__}-windows-x64"
        )
    )


@pytest.fixture
def executable(tmp_path):
    bundle = bundle_directory()
    if not (bundle / "privacy-guard.exe").is_file():
        pytest.skip("Build Windows standalone bundle before executable acceptance")
    target = tmp_path / "独立 executable" / "privacy-guard.exe"
    target.parent.mkdir()
    shutil.copy2(bundle / "privacy-guard.exe", target)
    return target


def invoke(executable, repo, *args, without_tools=True):
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("PRIVACY_GUARD_", "PYTHON", "GITLEAKS_"))
    }
    if without_tools:
        env["PATH"] = ""
    env["PRIVACY_GUARD_GITLEAKS"] = "missing-scanner"
    proc = subprocess.run(
        [str(executable), *args], cwd=repo, env=env, capture_output=True, timeout=90
    )
    return proc, json.loads(proc.stdout)


@pytest.mark.parametrize("secret", [False, True])
def test_single_exe_without_installed_tools_is_read_only(executable, repo, secret):
    content = synthetic_secret() if secret else "ordinary public documentation"
    put(repo, "sample.txt", content)
    before = snapshot(repo)
    proc, output = invoke(executable, repo, "files", "--repo", str(repo), "--paths", "sample.txt")
    assert proc.returncode == 0 and output["review_complete"]
    assert output["scanned"] == 1 and output["semantic_status"] == "disabled"
    assert output["risk_level"] == ("critical" if secret else "none")
    if secret:
        assert output["findings"][0]["suggestion"]
    assert content.encode() not in proc.stdout + proc.stderr
    assert str(repo).encode() not in proc.stdout + proc.stderr
    assert snapshot(repo) == before


def test_single_exe_errors_are_masked(executable, repo):
    before = snapshot(repo)
    marker = "SYNTHETIC_UNKNOWN_PRIVATE_INPUT"
    proc, output = invoke(executable, repo, "files", "--repo", str(repo), "--" + marker)
    assert proc.returncode == 1 and not output["review_complete"]
    assert marker.encode() not in proc.stdout + proc.stderr
    proc, output = invoke(
        executable, repo, "files", "--repo", str(repo), "--paths", marker + ".txt"
    )
    assert proc.returncode == 1 and not output["review_complete"]
    assert marker.encode() not in proc.stdout + proc.stderr
    assert snapshot(repo) == before


def test_frozen_semantic_fails_without_relaunching_executable(executable, repo):
    put(repo, "sample.txt", synthetic_secret())
    before = snapshot(repo)
    proc, output = invoke(
        executable, repo, "files", "--repo", str(repo), "--paths", "sample.txt", "--semantic"
    )
    assert proc.returncode == 1 and not output["review_complete"]
    assert output["semantic_status"] == "incomplete" and output["risk_level"] == "critical"
    assert snapshot(repo) == before


def test_git_modes_reuse_existing_git_and_report_missing_git(executable, repo):
    put(repo, "sample.txt", synthetic_secret())
    before = snapshot(repo)
    proc, output = invoke(executable, repo, "staged", "--repo", str(repo), without_tools=False)
    assert proc.returncode == 0 and output["risk_level"] == "critical"
    assert snapshot(repo) == before
    commit(repo)
    before = snapshot(repo)
    proc, output = invoke(
        executable,
        repo,
        "push",
        "--repo",
        str(repo),
        "--push-range",
        "HEAD",
        "-",
        without_tools=False,
    )
    assert proc.returncode == 0 and output["scope"] and output["risk_level"] == "critical"
    proc, output = invoke(executable, repo, "staged", "--repo", str(repo))
    assert proc.returncode == 1 and not output["review_complete"]
    assert snapshot(repo) == before


def test_bundle_archive_and_manifest():
    bundle = bundle_directory()
    if not bundle.is_dir():
        pytest.skip("Build bundle before archive acceptance")
    archive = bundle / f"privacy-guard-{__version__}-windows-x64.zip"
    expected, name = (bundle / "SHA256SUMS.txt").read_text().strip().split()
    assert name == archive.name and hashlib.sha256(archive.read_bytes()).hexdigest() == expected
    with zipfile.ZipFile(archive) as package:
        assert package.testzip() is None
        assert set(package.namelist()) == {
            "privacy-guard.exe",
            "README.md",
            "THIRD_PARTY_NOTICES.md",
            "licenses/gitleaks.txt",
            "licenses/python.txt",
            "licenses/pyinstaller.txt",
        }
        assert package.read("licenses/gitleaks.txt").startswith(b"MIT License")


def test_builder_refuses_overwrite():
    bundle = bundle_directory()
    if not bundle.is_dir():
        pytest.skip("Build bundle before builder acceptance")
    before = {p.name: p.read_bytes() for p in bundle.iterdir() if p.is_file()}
    proc = subprocess.run(
        [sys.executable, "-B", "scripts/build_standalone.py", "--output", str(bundle)],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        timeout=30,
    )
    assert proc.returncode == 1 and b"no files overwritten" in proc.stdout
    assert {p.name: p.read_bytes() for p in bundle.iterdir() if p.is_file()} == before
