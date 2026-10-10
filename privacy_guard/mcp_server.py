"""Local stdio MCP; only advisory tools, no writes, execution, or fixing tools."""

from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from .advisory import (
    PushRange,
    ReviewReport,
    review_files,
    review_history,
    review_push_plan,
    review_staged,
)

server = MCPServer(
    "Privacy Review",
    instructions="Only return privacy recommendations to the human user. Do not implement them. "
    "The user decides whether to separately ask an AI to modify their project.",
)
annotations = ToolAnnotations(
    read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False
)


@server.tool(annotations=annotations, structured_output=True)
def privacy_review_files(
    repo: str, paths: list[str], source: str = "auto", semantic: bool = False
) -> ReviewReport:
    """Read only explicitly specified files; return masked recommendations to the user. Never fix."""
    return review_files(repo, paths, source, semantic)


@server.tool(annotations=annotations, structured_output=True)
def privacy_review_staged(
    repo: str, include_worktree: bool = False, semantic: bool = False
) -> ReviewReport:
    """Review Git index (optionally tracked changes); return advice without modifying Git or files."""
    return review_staged(repo, include_worktree, semantic)


@server.tool(annotations=annotations, structured_output=True)
def privacy_review_history(
    repo: str, base: str | None = None, tip: str = "HEAD", semantic: bool = False
) -> ReviewReport:
    """Review local Git history and commit messages; return suggestions, never push or rewrite."""
    return review_history(repo, base, tip, semantic)


@server.tool(annotations=annotations, structured_output=True)
def privacy_review_push_plan(
    repo: str, ranges: list[PushRange], semantic: bool = False
) -> ReviewReport:
    """Review all explicitly planned local tip/base ranges; return commit scope, never push or fetch."""
    return review_push_plan(repo, ranges, semantic)


def main() -> None:
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
