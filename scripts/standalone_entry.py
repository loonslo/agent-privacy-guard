"""Frozen CLI entry; no environment activation or client registration."""

import json

from privacy_guard.advisory import error_report
from privacy_guard.cli import main
from privacy_guard.model import GuardError

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        print(json.dumps(error_report(GuardError("Review incomplete; details suppressed"))))
        raise SystemExit(1)
