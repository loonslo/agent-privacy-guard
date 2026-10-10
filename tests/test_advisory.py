import asyncio
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

from mcp import Client
from mcp.client.stdio import StdioServerParameters

from conftest import run
from privacy_guard.advisory import review_files, review_history, review_staged
from privacy_guard.cli import main
from test_guard import commit, put, synthetic_secret


def snapshot(repo: Path) -> tuple:
    files = {p.relative_to(repo).as_posix(): p.read_bytes() for p in repo.rglob("*") if p.is_file()}
    return files, run(repo, "status", "--porcelain"), run(repo, "config", "--local", "--list")


def test_secret_yields_advice_and_exit_zero(repo, capsys):
    put(repo, "sample.py", synthetic_secret())
    before = snapshot(repo)
    assert main(["staged", "--repo", str(repo)]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["mode"] == "advisory" and output["risk_level"] == "critical"
    assert "action" not in output and output["findings"][0]["suggestion"]
    assert output["next_step"] and snapshot(repo) == before


def test_all_review_modes_preserve_project(repo):
    put(repo, "sample.py", synthetic_secret())
    commit(repo)
    put(repo, "note.md", "clean")
    before = snapshot(repo)
    assert review_files(str(repo), ["sample.py"])["risk_level"] == "critical"
    assert review_staged(str(repo))["review_complete"]
    assert review_history(str(repo))["risk_level"] == "critical"
    assert snapshot(repo) == before


def test_credentials_path_is_not_opened(repo):
    put(repo, ".env", synthetic_secret())
    with patch.object(Path, "read_bytes", side_effect=AssertionError("must not open credentials")):
        result = review_files(str(repo), [".env"])
    assert result["findings"][0]["rule"] == "credential-path"
    assert not result["review_complete"]
    with patch(
        "privacy_guard.gitio.read_blob", side_effect=AssertionError("must not open credentials")
    ):
        assert review_staged(str(repo))["findings"][0]["rule"] == "credential-path"


def test_unknown_scope_or_failure_is_not_a_decision(repo, monkeypatch):
    assert not review_files(str(repo), ["../outside.txt"])["review_complete"]
    monkeypatch.setenv("PRIVACY_GUARD_GITLEAKS", "missing-binary")
    output = review_files(str(repo), [])
    assert not output["review_complete"] and "action" not in output


def test_skill_entry_runs(repo):
    put(repo, "sample.py", synthetic_secret())
    script = Path(__file__).resolve().parents[1] / "skills/privacy-review/scripts/review.py"
    output = subprocess.run(
        [sys.executable, "-B", str(script), "files", "--repo", str(repo), "--paths", "sample.py"],
        capture_output=True,
        check=True,
    )
    report = json.loads(output.stdout)
    assert report["mode"] == "advisory" and report["risk_level"] == "critical"
    assert synthetic_secret().encode() not in output.stdout + output.stderr


def test_real_mcp_stdio_is_read_only(repo, monkeypatch):
    monkeypatch.delenv("PRIVACY_GUARD_SEMANTIC_MODEL", raising=False)
    put(repo, "sample.py", synthetic_secret())
    commit(repo)
    before = snapshot(repo)
    script = Path(__file__).resolve().parents[1] / "scripts/run_mcp.py"

    async def verify():
        config = StdioServerParameters(command=sys.executable, args=["-B", str(script)])
        async with Client(config) as client:
            tools = (await client.list_tools()).tools
            assert {tool.name for tool in tools} == {
                "privacy_review_files",
                "privacy_review_staged",
                "privacy_review_history",
                "privacy_review_push_plan",
            }
            assert all(
                tool.annotations.read_only_hint and not tool.annotations.destructive_hint
                for tool in tools
            )
            result = await client.call_tool(
                "privacy_review_files", {"repo": str(repo), "paths": ["sample.py"]}
            )
            assert not result.is_error
            output = result.structured_content
            assert output["mode"] == "advisory" and output["risk_level"] == "critical"
            assert "action" not in output
            assert synthetic_secret() not in json.dumps(output)
            memory = await client.call_tool(
                "privacy_review_files",
                {"repo": str(repo), "paths": ["sample.py"], "source": "memory"},
            )
            assert any(
                hit["rule"] == "agent-memory" for hit in memory.structured_content["findings"]
            )
            plan = await client.call_tool(
                "privacy_review_push_plan",
                {"repo": str(repo), "ranges": [{"tip": "HEAD", "base": None}]},
            )
            assert not plan.is_error and plan.structured_content["scope"]
            semantic = await client.call_tool(
                "privacy_review_files",
                {"repo": str(repo), "paths": ["sample.py"], "semantic": True},
            )
            assert not semantic.is_error
            assert semantic.structured_content["semantic_status"] == "incomplete"
            assert not semantic.structured_content["review_complete"]

    asyncio.run(verify())
    assert snapshot(repo) == before
