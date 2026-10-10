import json
from pathlib import Path
import subprocess
from unittest.mock import patch

import pytest

from conftest import run
from privacy_guard.adapters import claude_hook, command_check, pre_push
from privacy_guard.cli import main
from privacy_guard.gitio import history, staged
from privacy_guard.model import Blob, GuardError, Result
from privacy_guard.rules import inspect, valid_id
from privacy_guard.scanner import scan


def synthetic_secret() -> str:
    # Non-production fixture created at runtime; no user credentials are ever read.
    return "ghp_" + "Ab3dEf7hIj9kLm2nOp4qRs6tUv8wXy0zABCD"


def put(repo: Path, name: str, content: str) -> None:
    path = repo / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    run(repo, "add", "--", name)


def commit(repo: Path) -> str:
    run(repo, "commit", "-m", "synthetic fixture")
    return run(repo, "rev-parse", "HEAD")


def test_reads_index_not_worktree(repo):
    put(repo, "safe.txt", synthetic_secret())
    (repo / "safe.txt").write_text("clean", encoding="utf-8")
    assert synthetic_secret().encode() in staged(repo)[0].content
    assert scan(staged(repo)).action == "deny"


def test_commit_all_includes_unstaged_tracked(repo):
    put(repo, "safe.txt", "clean")
    commit(repo)
    (repo / "safe.txt").write_text(synthetic_secret(), encoding="utf-8")
    assert staged(repo) == []
    assert command_check('git commit -a -m "test"', repo).action == "deny"


def test_push_catches_deleted_secret_and_range(repo):
    put(repo, "safe.txt", "clean")
    base = commit(repo)
    put(repo, "leak.txt", synthetic_secret())
    leak_commit = commit(repo)
    run(repo, "rm", "leak.txt")
    tip = commit(repo)
    result = scan(history(repo, tip, base))
    assert result.action == "deny"
    assert any(f.commit == leak_commit for f in result.findings)


def test_initial_commit_and_initial_push(repo):
    put(repo, "safe.txt", "hello")
    tip = commit(repo)
    assert scan(history(repo)).action == "allow"
    assert pre_push(repo, f"refs/heads/main {tip} refs/heads/main {'0' * 40}").action == "allow"


def test_push_multiple_refs_and_deletion(repo):
    put(repo, "safe.txt", "hello")
    clean = commit(repo)
    put(repo, "leak.txt", synthetic_secret())
    tip = commit(repo)
    result = pre_push(repo, f"a {tip} a {clean}\nb {'0' * 40} b {clean}")
    assert result.action == "deny"


def test_deleted_index_file_skipped(repo):
    put(repo, "safe.txt", "hello")
    commit(repo)
    run(repo, "rm", "safe.txt")
    assert staged(repo) == []


@pytest.mark.parametrize(
    "command",
    [
        "git commit --no-verify",
        "git -c core.hooksPath=x commit",
        "git config core.hooksPath x",
        "git add . && git commit",
        "git commit -am test",
        "git commit file.txt",
        "git push --all",
        "cd elsewhere; git push",
        "powershell -Command 'git push'",
        "git custom-alias",
        "git push origin other-branch",
        "git commit $(echo -a)",
        "SKIP=gitleaks git commit",
    ],
)
def test_bypass_and_opaque_forms_denied(command, repo):
    with pytest.raises(GuardError):
        command_check(command, repo)


@pytest.mark.parametrize(
    "path",
    [
        ".codex/auth.json",
        ".workbuddy-ai/state.txt",
        "src/.unknown/data",
        "settings.local.json",
        ".env",
        "key.pem",
    ],
)
def test_sensitive_paths(path):
    assert Result(inspect(Blob(path, b"clean"))).action == "deny"


def test_safe_dot_directory_is_still_secret_scanned():
    assert scan([Blob(".github/workflows/check.yml", synthetic_secret().encode())]).action == "deny"


@pytest.mark.parametrize(
    "text",
    [
        "订单 123456789012345678",
        "收入 13812345678",
        "ghp_helper",
        "xx@2x.png",
        "git@github.com",
        "demo@example.com",
        "每月定投纳指，用 IBKR",
    ],
)
def test_negative_samples(text):
    assert scan([Blob("note.md", text.encode())]).action == "allow"


def test_phone_and_email_policy():
    assert Result(inspect(Blob("note.md", "联系电话 13812345678".encode()))).action == "deny"
    assert Result(inspect(Blob("note.md", b"person@private.test"))).action == "ask"
    assert Result(inspect(Blob("note.md", (b"person@private.test\n" * 3)))).action == "ask"


def test_id_checksum():
    body = "11010119900101001"
    weights = (7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2)
    check = "10X98765432"[sum(int(n) * w for n, w in zip(body, weights)) % 11]
    assert valid_id(body + check)
    assert not valid_id(body + ("0" if check != "0" else "1"))


def test_report_never_echoes_secret_or_path():
    value = synthetic_secret()
    report = json.dumps(scan([Blob(value + ".txt", value.encode())]).report())
    assert value not in report
    assert "REDACTED" in report


def test_embedded_allow_comment_cannot_suppress():
    assert (
        scan([Blob("note.md", (synthetic_secret() + " # gitleaks:allow").encode())]).action
        == "deny"
    )


def test_repository_config_not_used(repo):
    (repo / ".gitleaks.toml").write_text('title = "no rules"', encoding="utf-8")
    assert scan([Blob("note.md", synthetic_secret().encode())]).action == "deny"


def test_binary_and_unknown_encoding_require_review():
    assert Result(inspect(Blob("blob.bin", b"\0data"))).action == "deny"
    assert Result(inspect(Blob("blob.txt", b"\xff"))).action == "deny"


def test_missing_dependency_fails_closed(monkeypatch, capsys):
    monkeypatch.setenv("PRIVACY_GUARD_GITLEAKS", "nonexistent-gitleaks-binary")
    assert main(["doctor"]) == 1
    assert json.loads(capsys.readouterr().out)["review_complete"] is False


def test_scanner_failure_does_not_echo_diagnostics(capsys):
    with patch(
        "privacy_guard.scanner.subprocess.run",
        return_value=subprocess.CompletedProcess([], 99, b"", synthetic_secret().encode()),
    ):
        assert main(["doctor"]) == 1
    assert synthetic_secret() not in capsys.readouterr().out


def test_hook_json_and_error_exit(repo, monkeypatch, capsys):
    put(repo, "note.md", synthetic_secret())
    event = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "cwd": str(repo),
        "tool_input": {"command": 'git commit -m "safe"'},
    }
    assert claude_hook(json.dumps(event))["hookSpecificOutput"]["permissionDecision"] == "deny"
    event["tool_input"]["command"] = "git status"
    assert claude_hook(json.dumps(event)) == {}
    import io

    monkeypatch.setattr("sys.stdin", io.StringIO("not json"))
    assert main(["claude-hook"]) == 0
    assert "not json" not in capsys.readouterr().err


def test_retired_native_precommit_is_inert(repo):
    hooks = Path(__file__).resolve().parents[1] / "hooks"
    run(repo, "config", "core.hooksPath", str(hooks))
    put(repo, "note.md", synthetic_secret())
    proc = subprocess.run(
        ["git", "-C", str(repo), "commit", "-m", "synthetic"], capture_output=True
    )
    assert proc.returncode == 0
    assert synthetic_secret().encode() not in proc.stdout + proc.stderr


def test_commit_message_secret(repo):
    put(repo, "safe.txt", "clean")
    assert command_check(f'git commit -m "{synthetic_secret()}"', repo).action == "deny"
    run(repo, "commit", "-m", synthetic_secret())
    assert scan(history(repo)).action == "deny"


def test_retired_native_precommit_all_is_inert(repo):
    put(repo, "note.md", "clean")
    commit(repo)
    (repo / "note.md").write_text(synthetic_secret(), encoding="utf-8")
    hooks = Path(__file__).resolve().parents[1] / "hooks"
    run(repo, "config", "core.hooksPath", str(hooks))
    proc = subprocess.run(
        ["git", "-C", str(repo), "commit", "-a", "-m", "synthetic"], capture_output=True
    )
    assert proc.returncode == 0


def test_native_precommit_clean_allows(repo):
    hooks = Path(__file__).resolve().parents[1] / "hooks"
    run(repo, "config", "core.hooksPath", str(hooks))
    put(repo, "note.md", "clean")
    commit(repo)


def test_retired_native_push_is_inert(repo, tmp_path):
    bare = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(bare)], capture_output=True, check=True)
    put(repo, "leak.txt", synthetic_secret())
    commit(repo)
    run(repo, "rm", "leak.txt")
    commit(repo)
    run(repo, "remote", "add", "origin", str(bare))
    hooks = Path(__file__).resolve().parents[1] / "hooks"
    run(repo, "config", "core.hooksPath", str(hooks))
    proc = subprocess.run(["git", "-C", str(repo), "push", "origin", "HEAD"], capture_output=True)
    assert proc.returncode == 0
    remote = subprocess.run(
        ["git", "-C", str(bare), "rev-parse", "--verify", "refs/heads/main"], capture_output=True
    )
    assert remote.returncode == 0


def test_timeout_is_closed(capsys):
    with patch(
        "privacy_guard.scanner.subprocess.run", side_effect=subprocess.TimeoutExpired("test", 1)
    ):
        assert main(["doctor"]) == 1
    assert json.loads(capsys.readouterr().out)["review_complete"] is False


def test_invalid_report_is_closed(capsys):
    def bad_report(argv, **kwargs):
        Path(argv[argv.index("--report-path") + 1]).write_text("{}", encoding="utf-8")
        return subprocess.CompletedProcess(argv, 0, b"", b"")

    with patch("privacy_guard.scanner.subprocess.run", side_effect=bad_report):
        assert main(["doctor"]) == 1
    assert json.loads(capsys.readouterr().out)["review_complete"] is False


def test_gitlink_requires_child_scan(repo):
    put(repo, "safe.txt", "clean")
    oid = commit(repo)
    run(repo, "update-index", "--add", "--cacheinfo", f"160000,{oid},child")
    with pytest.raises(GuardError, match="Gitlink"):
        staged(repo)


def test_base64_secret_detected():
    import base64

    assert (
        scan([Blob("encoded.txt", base64.b64encode(synthetic_secret().encode()))]).action == "deny"
    )
