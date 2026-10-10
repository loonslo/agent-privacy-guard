from pathlib import Path
import subprocess

import pytest


def run(repo: Path, *args: str) -> str:
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=True)
    return p.stdout.decode().strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    run(tmp_path, "init", "-b", "main")
    run(tmp_path, "config", "user.name", "Synthetic Test")
    run(tmp_path, "config", "user.email", "test@example.com")
    # Isolate tests from inherited global hooks without touching user repositories.
    run(tmp_path, "config", "core.hooksPath", str(tmp_path / "empty-hooks"))
    return tmp_path
