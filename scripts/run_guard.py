"""Read-only CLI entry point; no installation or environment activation needed."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
try:
    from privacy_guard.cli import main

    raise SystemExit(main())
except Exception:
    print("Privacy review incomplete; details suppressed", file=sys.stderr)
    raise SystemExit(1)
