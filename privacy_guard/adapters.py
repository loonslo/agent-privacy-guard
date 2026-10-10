import json
from pathlib import Path
import re
import shlex

from .gitio import history, staged
from .model import Blob, GuardError, Result
from .scanner import scan


def command_check(command: str, repo: Path) -> Result:
    """Conservative subset, never executes shell input. Unknown Git forms fail closed."""
    if re.search(
        r"--no-verify|--output|--exec|core\.hooksPath|\.git[/\\]hooks|"
        r"settings(?:\.local)?\.json|SKIP\s*=",
        command,
        re.I,
    ):
        raise GuardError("Guard bypass or protected configuration command denied")
    if not re.search(r"\bgit(?:\.exe)?\b", command, re.I):
        return Result()
    if any(c in command for c in ";&|`\n\r<>$"):
        raise GuardError("Compound or expanded Git command requires separate simple commands")
    tokens = shlex.split(command, posix=True)
    if len(tokens) < 2 or tokens[0].lower() not in {"git", "git.exe"}:
        raise GuardError("Wrapped or indirect Git command requires manual review")
    operation, args = tokens[1], tokens[2:]
    if operation in {"status", "diff", "log", "show", "add", "ls-files", "rev-parse"}:
        return Result()
    if operation == "commit":
        all_tracked = False
        messages = []
        i = 0
        while i < len(args):
            arg = args[i]
            if arg in {"-a", "--all"}:
                all_tracked = True
            elif arg in {"-q", "--quiet"}:
                pass
            elif arg in {"-m", "--message"}:
                i += 1
                if i >= len(args):
                    raise GuardError("Missing commit message")
                messages.append(args[i])
            elif arg.startswith("--message="):
                messages.append(arg.split("=", 1)[1])
            else:
                raise GuardError("Unsupported commit option or path; stage then use simple commit")
            i += 1
        candidates = staged(repo, all_tracked)
        if messages:
            candidates.append(Blob("commit-message.txt", "\n\n".join(messages).encode()))
        return scan(candidates)
    if operation == "push":
        # Scan ALL reachable history, independent of remote/upstream visibility. Actual refs are
        # checked again by pre-push. Only current HEAD push forms are accepted by this adapter.
        if args not in ([], ["origin"], ["origin", "HEAD"]):
            raise GuardError("Unsupported push form; use simple HEAD push and pre-push hook")
        return scan(history(repo))
    raise GuardError("Unsupported Git command requires manual review")


def claude_hook(payload: str) -> dict:
    event = json.loads(payload)
    if event.get("hook_event_name") != "PreToolUse" or event.get("tool_name") != "Bash":
        raise GuardError("Unexpected hook event")
    command = event["tool_input"]["command"]
    cwd = event["cwd"]
    if not isinstance(command, str) or not isinstance(cwd, str):
        raise GuardError("Invalid hook command or cwd")
    result = command_check(command, Path(cwd))
    if result.action == "allow":
        return {}  # retain normal Claude permission checks; do not grant permission ourselves
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": result.action,
            "permissionDecisionReason": json.dumps(result.report(), ensure_ascii=True),
        }
    }


def pre_push(repo: Path, payload: str) -> Result:
    blobs = []
    lines = payload.splitlines()
    for line in lines:
        fields = line.split()
        if len(fields) != 4:
            raise GuardError("Invalid pre-push input")
        _, local_oid, _, remote_oid = fields
        if not all(re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", x) for x in (local_oid, remote_oid)):
            raise GuardError("Invalid pre-push object id")
        if set(local_oid) == {"0"}:
            continue  # remote deletion, no content leaves the machine
        base = None if set(remote_oid) == {"0"} else remote_oid
        # Missing old object blocks rather than claiming the range was scanned.
        blobs.extend(history(repo, local_oid, base))
    return scan(blobs)
