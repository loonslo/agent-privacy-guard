"""PowerShell download launcher with isolated synthetic targets and network doubles."""

import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest

from test_advisory import snapshot
from test_guard import put, synthetic_secret
from test_standalone import bundle_directory


def quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def launcher_archive() -> Path:
    configured = os.environ.get("PRIVACY_GUARD_TEST_LAUNCHER_ARCHIVE")
    return (
        Path(configured)
        if configured
        else (bundle_directory() / "privacy-guard-0.4.0-windows-x64.zip")
    )


@pytest.mark.parametrize("scenario", ["clean", "risk", "checksum", "network", "bad-args", "temp"])
def test_launcher_is_read_only_and_masks_failures(repo, tmp_path, scenario):
    powershell = shutil.which("powershell")
    archive = launcher_archive()
    if not powershell or not archive.is_file():
        pytest.skip("Build Windows standalone bundle before launcher acceptance")
    script = Path(__file__).resolve().parents[1] / "scripts/review.ps1"
    marker = "SYNTHETIC_PRIVATE_LAUNCHER_ERROR"
    put(repo, "sample.txt", synthetic_secret() if scenario == "risk" else "ordinary public note")
    before = snapshot(repo)
    if scenario == "checksum":
        download = "[IO.File]::WriteAllText($OutFile, 'not a release')"
    elif scenario == "network":
        download = f"throw {quote(marker)}"
    else:
        download = f"Copy-Item -LiteralPath {quote(str(archive))} -Destination $OutFile"
    arguments = f"-Repo {quote(str(repo))} -Paths sample.txt"
    if scenario == "bad-args":
        arguments += f" -Unknown {quote(marker)}"
    temporary = repo if scenario == "temp" else tmp_path.parent
    command = (
        "function Invoke-WebRequest { param($Uri,$OutFile,[switch]$UseBasicParsing) "
        + download
        + " }; "
        + f"$env:TEMP={quote(str(temporary))}; $env:TMP=$env:TEMP; "
        + f"& {quote(str(script))} {arguments}; exit $LASTEXITCODE"
    )
    proc = subprocess.run(
        [powershell, "-NoProfile", "-NonInteractive", "-Command", command],
        capture_output=True,
        timeout=120,
    )
    output = json.loads(proc.stdout)
    complete = scenario in {"clean", "risk"}
    assert proc.returncode == (0 if complete else 1)
    assert output["review_complete"] is complete
    if complete:
        assert output["risk_level"] == ("critical" if scenario == "risk" else "none")
    assert marker.encode() not in proc.stdout + proc.stderr
    assert synthetic_secret().encode() not in proc.stdout + proc.stderr
    assert str(repo).encode() not in proc.stdout + proc.stderr
    assert snapshot(repo) == before


def test_launcher_hash_matches_release_archive():
    archive = launcher_archive()
    if not archive.is_file():
        pytest.skip("Build release before launcher integrity acceptance")
    import hashlib

    script = Path(__file__).resolve().parents[1] / "scripts/review.ps1"
    assert hashlib.sha256(archive.read_bytes()).hexdigest() in script.read_text(encoding="utf-8")
