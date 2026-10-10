"""Build Windows x64 rule bundle in a new directory; never install or overwrite."""

import argparse
import hashlib
import importlib.util
from importlib.metadata import distribution
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import tomllib
import zipfile


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, help="New output directory outside target projects")
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    version = tomllib.loads((project / "pyproject.toml").read_text(encoding="utf-8"))["project"][
        "version"
    ]
    name = f"privacy-guard-{version}-windows-x64"
    output = args.output or project / "dist" / name
    if sys.platform != "win32" or platform.machine().lower() not in {"amd64", "x86_64"}:
        print("Build requires Windows x64")
        return 1
    if output.exists():
        print("Build output already exists; no files overwritten")
        return 1
    binary = project / ".tools" / "gitleaks.exe"
    scanner_license = project / ".tools" / "LICENSE"
    python_license = Path(sys.base_prefix) / "LICENSE.txt"
    if not all(p.is_file() for p in (binary, scanner_license, python_license)):
        print("Build inputs unavailable; scanner and licenses required")
        return 1
    if importlib.util.find_spec("PyInstaller") is None:
        print("Build dependency unavailable; prepare bundle extra in build environment")
        return 1
    builder = distribution("pyinstaller")
    builder_license = next(
        (Path(builder.locate_file(p)) for p in builder.files or [] if p.name == "COPYING.txt"),
        None,
    )
    if builder_license is None or not builder_license.is_file():
        print("Build license unavailable; build not started")
        return 1
    # Only trusted project inputs are bundled; target materials are never build inputs.
    with tempfile.TemporaryDirectory(prefix="privacy-bundle-build-") as temporary:
        work = Path(temporary)
        proc = subprocess.run(
            [
                sys.executable,
                "-B",
                "-m",
                "PyInstaller",
                "--onefile",
                "--console",
                "--noupx",
                "--name",
                "privacy-guard",
                "--distpath",
                str(work / "dist"),
                "--workpath",
                str(work / "work"),
                "--specpath",
                str(work),
                "--paths",
                str(project),
                "--add-binary",
                f"{binary}:.tools",
                "--add-data",
                f"{scanner_license}:licenses/gitleaks",
                "--exclude-module",
                "mcp",
                "--exclude-module",
                "torch",
                "--exclude-module",
                "transformers",
                str(project / "scripts" / "standalone_entry.py"),
            ],
            cwd=project,
            capture_output=True,
            check=False,
        )
        if proc.returncode:
            print("Standalone build failed; raw diagnostics suppressed")
            return 1
        output.mkdir(parents=True, exist_ok=False)
        shutil.copy2(work / "dist" / "privacy-guard.exe", output / "privacy-guard.exe")
    licenses = output / "licenses"
    licenses.mkdir()
    shutil.copy2(scanner_license, licenses / "gitleaks.txt")
    shutil.copy2(python_license, licenses / "python.txt")
    shutil.copy2(builder_license, licenses / "pyinstaller.txt")
    shutil.copy2(project / "docs" / "standalone.md", output / "README.md")
    shutil.copy2(project / "docs" / "third-party-notices.md", output / "THIRD_PARTY_NOTICES.md")
    archive = output / f"{name}.zip"
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as package:
        for path in sorted(output.rglob("*")):
            if path.is_file() and path != archive:
                package.write(path, path.relative_to(output).as_posix())
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (output / "SHA256SUMS.txt").write_text(f"{digest}  {archive.name}\n", encoding="ascii")
    print("Standalone bundle and SHA256 manifest built; no installation performed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
