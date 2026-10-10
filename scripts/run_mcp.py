"""Start only the external stdio review service; does not register it with any client."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
try:
    from privacy_guard.mcp_server import main

    main()
except Exception:
    print("Privacy review MCP unavailable; details suppressed", file=sys.stderr)
    raise SystemExit(1)
