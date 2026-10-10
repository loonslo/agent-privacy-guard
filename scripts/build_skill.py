"""Build a standalone Skill under this project's dist; never install into a client."""

import argparse
from pathlib import Path
import shutil


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-gitleaks", action="store_true")
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    target = project / "dist" / "privacy-review"
    if target.exists():
        print("Build target already exists; choose a new checkout or preserve it before rebuilding")
        return 1
    binary = project / ".tools" / "gitleaks.exe"
    license_file = project / ".tools" / "LICENSE"
    if args.include_gitleaks and (not binary.is_file() or not license_file.is_file()):
        print("Local gitleaks binary or license unavailable; build not started")
        return 1
    shutil.copytree(
        project / "skills" / "privacy-review",
        target,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    vendor = target / "scripts" / "vendor"
    vendor.mkdir()
    shutil.copytree(
        project / "privacy_guard",
        vendor / "privacy_guard",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    if args.include_gitleaks:
        (vendor / ".tools").mkdir()
        shutil.copy2(binary, vendor / ".tools" / "gitleaks.exe")
        shutil.copy2(license_file, vendor / ".tools" / "LICENSE")
    print("Standalone Skill built in project dist; no client installation performed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
