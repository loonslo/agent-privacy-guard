import json
import os
from pathlib import Path
import subprocess
import shutil
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from conftest import run
from privacy_guard.advisory import review_files, review_push_plan, review_staged
from privacy_guard.cli import main
from privacy_guard.gitio import validate_oid
from privacy_guard.model import Blob, GuardError
from privacy_guard.rules import inspect
from privacy_guard.semantic_worker import classify
from test_advisory import snapshot
from test_guard import commit, put, synthetic_secret


@pytest.mark.parametrize(
    "name,source,content,rule",
    [
        ("agent_memory.md", "auto", "Private project facts", "agent-memory"),
        ("chat_history.json", "auto", "{}", "chat-history"),
        ("export.txt", "memory", "Private project facts", "agent-memory"),
        ("export.txt", "chat_history", "Plain transcript", "chat-history"),
        ("export.json", "auto", '{"role":"user","content":"Private fact"}', "chat-history"),
    ],
)
def test_memory_and_history_exports_are_scanned(repo, name, source, content, rule):
    put(repo, name, content + "\n" + synthetic_secret())
    before = snapshot(repo)
    output = review_files(str(repo), [name], source)
    assert output["review_complete"]
    assert rule in {hit["rule"] for hit in output["findings"]}
    assert any(hit["rule"].startswith("secret:") for hit in output["findings"])
    assert content not in json.dumps(output) and synthetic_secret() not in json.dumps(output)
    assert snapshot(repo) == before


@pytest.mark.parametrize(
    "value",
    [
        "C:/Users/SyntheticPerson/private/report.txt",
        r"D:\workspace\synthetic\private.txt",
        r"\\synthetic-host\private\report.txt",
        "/home/synthetic-person/private/report.txt",
        "~/private/report.txt",
    ],
)
def test_content_paths_return_only_masked_findings(repo, value):
    put(repo, "note.md", "Location: " + value)
    output = review_files(str(repo), ["note.md"])
    assert output["review_complete"]
    assert any(hit["rule"] == "local-path" and hit["line"] == 1 for hit in output["findings"])
    assert value not in json.dumps(output)


def test_relative_paths_and_web_links_do_not_trigger_path_rule():
    hits = inspect(Blob("note.md", b"src/example.py https://example.com/home/test"))
    assert not hits


@pytest.mark.parametrize("dirname", [".codex", ".claude", ".ssh"])
def test_protected_root_never_reads_or_runs_git(tmp_path, dirname):
    root = tmp_path / dirname
    root.mkdir()
    (root / "memory.md").write_text("Synthetic data", encoding="utf-8")
    with (
        patch.object(Path, "read_bytes", side_effect=AssertionError()),
        patch("privacy_guard.gitio.git", side_effect=AssertionError()),
    ):
        output = review_files(str(root), ["memory.md"])
        staged = review_staged(str(root))
        push = review_push_plan(str(root), [{"tip": "HEAD", "base": None}])
    assert all(not result["review_complete"] for result in (output, staged, push))
    assert all("Protected review root" in result["errors"][0] for result in (output, staged, push))


def test_credential_basename_never_opened(repo):
    put(repo, "auth.json", synthetic_secret())
    with patch.object(Path, "read_bytes", side_effect=AssertionError()):
        output = review_files(str(repo), ["auth.json"])
    assert output["findings"][0]["rule"] == "credential-path"
    assert not output["review_complete"]


def test_resolved_target_in_protected_directory_never_opened(repo):
    put(repo, ".codex/memory.md", "Synthetic data")
    protected = repo / ".codex" / "memory.md"
    original = Path.resolve

    def redirect(path, *args, **kwargs):
        return protected if path.name == "export.md" else original(path, *args, **kwargs)

    with (
        patch.object(Path, "resolve", redirect),
        patch.object(Path, "read_bytes", side_effect=AssertionError()),
    ):
        output = review_files(str(repo), ["export.md"])
    assert output["errors"] == ["Protected review target; contents were not read"]


@pytest.mark.parametrize(
    "arguments",
    [
        ["files", "--unknown=SYNTHETIC_PRIVATE_ARGUMENT"],
        ["SYNTHETIC_PRIVATE_ARGUMENT"],
        ["files", "--source", "SYNTHETIC_PRIVATE_ARGUMENT"],
        ["push", "--push-range", "SYNTHETIC_PRIVATE_ARGUMENT"],
    ],
)
def test_cli_parse_failures_are_static(arguments, capsys):
    assert main(arguments) == 1
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert not output["review_complete"]
    assert "SYNTHETIC_PRIVATE_ARGUMENT" not in captured.out + captured.err
    assert captured.err == ""


def test_skill_parse_failure_is_masked():
    script = Path(__file__).resolve().parents[1] / "skills/privacy-review/scripts/review.py"
    marker = "SYNTHETIC_PRIVATE_ARGUMENT"
    proc = subprocess.run(
        [sys.executable, "-B", str(script), "files", "--unknown=" + marker], capture_output=True
    )
    assert proc.returncode == 1
    assert not json.loads(proc.stdout)["review_complete"]
    assert marker.encode() not in proc.stdout + proc.stderr


def test_push_plan_reviews_multiple_branches_and_deleted_secret(repo):
    put(repo, "safe.txt", "clean")
    base = commit(repo)
    run(repo, "branch", "clean")
    put(repo, "leak.txt", synthetic_secret())
    leak = commit(repo)
    run(repo, "rm", "leak.txt")
    tip = commit(repo)
    before = snapshot(repo)
    output = review_push_plan(
        str(repo),
        [
            {"tip": "clean", "base": None},
            {"tip": "main", "base": base},
        ],
    )
    assert output["review_complete"] and output["risk_level"] == "critical"
    assert len(output["scope"]) == 2
    assert output["scope"][1]["tip_commit"] == tip
    assert output["scope"][1]["base_commit"] == base
    assert any(hit["commit"] == leak for hit in output["findings"])
    assert synthetic_secret() not in json.dumps(output)
    assert snapshot(repo) == before


def test_push_plan_invalid_ref_has_static_error(repo):
    put(repo, "safe.txt", "clean")
    commit(repo)
    output = review_push_plan(str(repo), [{"tip": "SYNTHETIC_PRIVATE_ARGUMENT", "base": None}])
    assert not output["review_complete"]
    assert "SYNTHETIC_PRIVATE_ARGUMENT" not in json.dumps(output)


def test_annotated_tag_payload_is_not_silently_marked_complete(repo):
    put(repo, "safe.txt", "clean")
    commit(repo)
    run(repo, "tag", "-a", "synthetic-tag", "-m", synthetic_secret())
    output = review_push_plan(str(repo), [{"tip": "refs/tags/synthetic-tag", "base": None}])
    assert not output["review_complete"]
    assert "tag payload" in output["errors"][0]
    assert synthetic_secret() not in json.dumps(output)


def test_untrusted_git_object_identifier_cannot_escape_to_scope(repo):
    put(repo, "safe.txt", "clean")
    commit(repo)
    marker = "SYNTHETIC_PRIVATE_ARGUMENT"
    with patch("privacy_guard.advisory.git", return_value=marker.encode()):
        output = review_push_plan(str(repo), [{"tip": "HEAD", "base": None}])
    assert not output["review_complete"] and output["scope"] == []
    assert marker not in json.dumps(output)
    with pytest.raises(GuardError):
        validate_oid(marker)


def test_cli_multiple_push_ranges(repo, capsys):
    put(repo, "safe.txt", "clean")
    tip = commit(repo)
    assert (
        main(
            ["push", "--repo", str(repo), "--push-range", "main", "-", "--push-range", "HEAD", tip]
        )
        == 0
    )
    output = json.loads(capsys.readouterr().out)
    assert len(output["scope"]) == 2 and output["risk_level"] == "none"


def test_semantic_missing_model_preserves_rule_findings(repo, monkeypatch):
    monkeypatch.delenv("PRIVACY_GUARD_SEMANTIC_MODEL", raising=False)
    put(repo, "note.md", synthetic_secret())
    output = review_files(str(repo), ["note.md"], semantic=True)
    assert not output["review_complete"] and output["semantic_status"] == "incomplete"
    assert output["risk_level"] == "critical"
    assert synthetic_secret() not in json.dumps(output)


@pytest.mark.parametrize(
    "label,expected",
    [
        ("private", "semantic-private"),
        ("uncertain", "semantic-uncertain"),
        ("public", None),
    ],
)
def test_local_semantics_is_masked_monotonic_and_read_only(repo, monkeypatch, label, expected):
    model = repo / "local-model"
    model.mkdir()
    monkeypatch.setenv("PRIVACY_GUARD_SEMANTIC_MODEL", str(model))
    secret = synthetic_secret()
    put(repo, "note.md", secret + "\nPrivate company plans")
    before = snapshot(repo)

    def worker(argv, **kwargs):
        payload = json.loads(kwargs["input"])
        assert secret not in payload["texts"][0]
        assert "Private company plans" in payload["texts"][0]
        assert kwargs["env"]["HF_HUB_OFFLINE"] == "1"
        assert "-I" in argv and kwargs["timeout"] == 60
        return subprocess.CompletedProcess(argv, 0, json.dumps([label]).encode(), b"")

    with patch("privacy_guard.semantic.subprocess.run", worker):
        # The patch shares subprocess module: isolate the rules scanner first.
        from privacy_guard.model import Result, finding

        blob = Blob("note.md", (secret + "\nPrivate company plans").encode())
        fixed = Result([finding(blob, "secret:synthetic", "critical", 1, blob.content)], scanned=1)
        with patch("privacy_guard.advisory.scan", return_value=fixed):
            output = review_files(str(repo), ["note.md"], semantic=True)
    assert output["review_complete"] and output["semantic_status"] == "complete"
    assert output["risk_level"] == "critical"
    if expected:
        assert expected in {hit["rule"] for hit in output["findings"]}
    assert "Private company plans" not in json.dumps(output)
    assert snapshot(repo) == before


@pytest.mark.parametrize("failure", ["timeout", "raw-output", "invalid-label"])
def test_semantic_worker_failures_suppress_diagnostics(repo, monkeypatch, failure):
    model = repo / "local-model"
    model.mkdir()
    monkeypatch.setenv("PRIVACY_GUARD_SEMANTIC_MODEL", str(model))
    put(repo, "note.md", "clean")
    marker = "SYNTHETIC_PRIVATE_ARGUMENT"

    def worker(argv, **kwargs):
        if failure == "timeout":
            raise subprocess.TimeoutExpired(marker, 60, output=marker)
        return subprocess.CompletedProcess(
            argv,
            0,
            marker.encode() if failure == "raw-output" else json.dumps([marker]).encode(),
            marker.encode(),
        )

    from privacy_guard.model import Result

    with (
        patch("privacy_guard.advisory.scan", return_value=Result(scanned=1)),
        patch("privacy_guard.semantic.subprocess.run", worker),
    ):
        output = review_files(str(repo), ["note.md"], semantic=True)
    assert not output["review_complete"] and output["semantic_status"] == "incomplete"
    assert marker not in json.dumps(output)


def test_semantic_real_worker_without_model_is_static(repo, monkeypatch):
    model = repo / "empty-model"
    model.mkdir()
    monkeypatch.setenv("PRIVACY_GUARD_SEMANTIC_MODEL", str(model))
    put(repo, "note.md", "clean")
    output = review_files(str(repo), ["note.md"], semantic=True)
    assert not output["review_complete"] and output["semantic_status"] == "incomplete"
    assert str(model) not in json.dumps(output)


def test_worker_loads_only_local_safetensors_without_custom_code(monkeypatch):
    tokenizer = MagicMock()
    tokenizer.model_max_length = 512
    tokens = {"input_ids": SimpleNamespace(shape=(1, 4))}
    tokenizer.return_value = tokens
    model = MagicMock()
    model.config.id2label = {0: "public", 1: "private", 2: "uncertain"}
    model.config.max_position_embeddings = 512
    model.to.return_value = model
    factories = SimpleNamespace(
        AutoTokenizer=MagicMock(), AutoModelForSequenceClassification=MagicMock()
    )
    factories.AutoTokenizer.from_pretrained.return_value = tokenizer
    factories.AutoModelForSequenceClassification.from_pretrained.return_value = model
    probabilities = MagicMock()
    probabilities.shape = (3,)
    probabilities.argmax.return_value = 1
    probabilities.__getitem__.return_value = 0.95
    torch = MagicMock()
    torch.softmax.return_value.__getitem__.return_value = probabilities
    torch.isfinite.return_value.all.return_value = True
    monkeypatch.setitem(sys.modules, "torch", torch)
    monkeypatch.setitem(sys.modules, "transformers", factories)
    assert classify({"model": "synthetic-model", "texts": ["Private company plans"]}) == ["private"]
    options = factories.AutoModelForSequenceClassification.from_pretrained.call_args.kwargs
    assert options == {
        "local_files_only": True,
        "trust_remote_code": False,
        "use_safetensors": True,
    }
    assert tokenizer.call_args.kwargs["truncation"] is False
    tokens["input_ids"].shape = (1, 513)
    with pytest.raises(ValueError, match="context"):
        classify({"model": "synthetic-model", "texts": ["long"]})


def test_built_skill_runs_without_project_imports(repo, tmp_path):
    project = Path(__file__).resolve().parents[1]
    isolated = tmp_path / "distribution-source"
    (isolated / "scripts").mkdir(parents=True)
    shutil.copy2(project / "scripts/build_skill.py", isolated / "scripts/build_skill.py")
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
    shutil.copytree(
        project / "skills/privacy-review", isolated / "skills/privacy-review", ignore=ignore
    )
    shutil.copytree(project / "privacy_guard", isolated / "privacy_guard", ignore=ignore)
    (isolated / ".tools").mkdir()
    shutil.copy2(project / ".tools/gitleaks.exe", isolated / ".tools/gitleaks.exe")
    shutil.copy2(project / ".tools/LICENSE", isolated / ".tools/LICENSE")
    proc = subprocess.run(
        [sys.executable, "-B", str(isolated / "scripts/build_skill.py"), "--include-gitleaks"],
        capture_output=True,
    )
    assert proc.returncode == 0
    bundle = isolated / "dist/privacy-review"
    assert (bundle / "scripts/vendor/.tools/LICENSE").is_file()
    target = tmp_path / "standalone-copy"
    shutil.copytree(bundle, target)
    # Remove source from import candidates; -I also excludes CWD/PYTHONPATH/site user paths.
    env = {
        key: value
        for key, value in os.environ.items()
        if key
        not in {
            "PRIVACY_GUARD_HOME",
            "PRIVACY_GUARD_GITLEAKS",
            "PYTHONPATH",
        }
    }
    put(repo, "portable.txt", synthetic_secret())
    before = snapshot(repo)
    proc = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            str(target / "scripts/review.py"),
            "files",
            "--repo",
            str(repo),
            "--paths",
            "portable.txt",
        ],
        capture_output=True,
        env=env,
        cwd=tmp_path,
    )
    assert proc.returncode == 0
    output = json.loads(proc.stdout)
    assert output["review_complete"] and output["risk_level"] == "critical"
    assert synthetic_secret().encode() not in proc.stdout + proc.stderr
    assert snapshot(repo) == before
    repeated = subprocess.run(
        [sys.executable, "-B", str(isolated / "scripts/build_skill.py")], capture_output=True
    )
    assert repeated.returncode == 1
