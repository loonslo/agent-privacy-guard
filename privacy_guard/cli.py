import argparse
import json
from pathlib import Path

from .advisory import (
    error_report,
    report,
    review_files,
    review_history,
    review_push_plan,
    review_staged,
)
from .model import GuardError
from .scanner import scan


class SafeParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise GuardError("Invalid review arguments; input suppressed")


def main(argv: list[str] | None = None) -> int:
    parser = SafeParser(prog="privacy-guard", allow_abbrev=False)
    parser.add_argument(
        "mode", choices=["files", "staged", "push", "pre-push", "claude-hook", "doctor"]
    )
    parser.add_argument("--paths", nargs="+", help="Explicit relative files for read-only review")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument(
        "--all-tracked", action="store_true", help="Include tracked worktree for commit -a"
    )
    parser.add_argument("--base", help="Push lower-bound commit; default scans all HEAD history")
    parser.add_argument("--tip", default="HEAD")
    parser.add_argument("--source", choices=["auto", "memory", "chat_history"], default="auto")
    parser.add_argument(
        "--semantic", action="store_true", help="Use configured offline local classifier"
    )
    parser.add_argument(
        "--push-range",
        nargs=2,
        action="append",
        metavar=("TIP", "BASE"),
        help="Repeat for each planned ref; BASE '-' means all local tip history",
    )
    try:
        args = parser.parse_args(argv)
        if args.push_range and (args.mode != "push" or args.base or args.tip != "HEAD"):
            raise GuardError("Push ranges require push mode without base or tip options")
        if args.source != "auto" and args.mode != "files":
            raise GuardError("Source type requires files mode")
        if args.semantic and args.mode not in {"files", "staged", "push"}:
            raise GuardError("Semantic review requires a review mode")
    except GuardError as exc:
        print(json.dumps(error_report(exc), ensure_ascii=True))
        return 1
    if args.mode == "claude-hook":
        print("{}")  # retired compatibility: no permission decision, no command inspection
        return 0
    if args.mode == "pre-push":
        output = error_report(GuardError("Hook integration retired; use advisory review"))
        print(json.dumps(output, ensure_ascii=True))
        return 0
    if args.mode == "files":
        output = review_files(str(args.repo), args.paths or [], args.source, args.semantic)
    elif args.mode == "staged":
        output = review_staged(str(args.repo), args.all_tracked, args.semantic)
    elif args.mode == "push":
        if args.push_range:
            output = review_push_plan(
                str(args.repo),
                [
                    {"tip": tip, "base": None if base == "-" else base}
                    for tip, base in args.push_range
                ],
                args.semantic,
            )
        else:
            output = review_history(str(args.repo), args.base, args.tip, args.semantic)
    else:
        try:
            output = report(scan([]))
        except Exception as exc:
            output = error_report(exc)
    print(json.dumps(output, ensure_ascii=True))
    # Findings are advice, not a rejection. Only technical incompleteness is nonzero.
    return 0 if output["review_complete"] else 1
