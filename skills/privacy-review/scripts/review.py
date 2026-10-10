"""Portable advisory Skill entry point; never invokes legacy enforcement modes."""

import importlib.util
import json
import os
from pathlib import Path
import sys

args = sys.argv[1:]
if not args or args[0] not in {"files", "staged", "push", "doctor"} or "--legacy-hook" in args:
    print(json.dumps({"review_complete": False, "errors": ["Only advisory review is supported"]}))
    raise SystemExit(1)

try:
    configured = os.environ.get("PRIVACY_GUARD_HOME")
    candidates = (
        [Path(configured)]
        if configured
        else [
            Path(__file__).resolve().parent / "vendor",
            Path(__file__).resolve().parents[3],
        ]
    )
    for task_root in candidates:
        if (task_root / "privacy_guard" / "cli.py").is_file():
            sys.path.insert(0, str(task_root))
            break
    else:
        if configured or importlib.util.find_spec("privacy_guard") is None:
            raise ImportError()
    from privacy_guard.cli import main

    raise SystemExit(main(args))
except Exception:
    print(json.dumps({"review_complete": False, "errors": ["Review engine unavailable"]}))
    raise SystemExit(1)
