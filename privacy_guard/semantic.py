"""Optional bounded local classification; no model prose crosses the output boundary."""

import json
import os
from pathlib import Path
import subprocess
import sys

from .model import Blob, GuardError, Result, digest, finding
from .paths import check_root, protected_path


def semantic_review(blobs: list[Blob], result: Result) -> None:
    try:
        configured = os.environ.get("PRIVACY_GUARD_SEMANTIC_MODEL")
        if not configured:
            raise GuardError("Local semantic model not configured; semantic review incomplete")
        model = check_root(Path(configured))
        candidates = [
            blob
            for blob in blobs
            if blob.content and blob.mode != "120000" and not protected_path(blob.path)
        ]
        if len(candidates) > 32:
            raise GuardError("Semantic file limit exceeded; semantic review incomplete")
        texts = []
        for blob in candidates:
            text = blob.content.decode("utf-8-sig")
            ref = digest(blob.path.encode("utf-8", "surrogateescape"))
            sensitive_lines = {
                hit.line
                for hit in result.findings
                if hit.file_ref == ref and hit.commit == blob.commit and hit.line > 0
            }
            # Mask whole rule-hit lines, including gitleaks decoded secrets, before inference.
            text = "\n".join(
                "[REDACTED]" if number in sensitive_lines else line
                for number, line in enumerate(text.splitlines(), 1)
            )
            texts.append(text)
        if sum(len(text.encode()) for text in texts) > 256 * 1024:
            raise GuardError("Semantic input limit exceeded; semantic review incomplete")
        env = dict(os.environ)
        env.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1")
        proc = subprocess.run(
            [sys.executable, "-I", "-B", str(Path(__file__).with_name("semantic_worker.py"))],
            input=json.dumps({"model": str(model), "texts": texts}).encode(),
            capture_output=True,
            timeout=60,
            check=False,
            env=env,
        )
        if proc.returncode or len(proc.stdout) > 4096:
            raise GuardError("Local semantic inference failed; details suppressed")
        labels = json.loads(proc.stdout)
        if (
            not isinstance(labels, list)
            or len(labels) != len(candidates)
            or any(label not in {"public", "private", "uncertain"} for label in labels)
        ):
            raise GuardError("Invalid local semantic result; details suppressed")
        for blob, label in zip(candidates, labels):
            if label != "public":
                result.findings.append(
                    finding(
                        blob,
                        "semantic-private" if label == "private" else "semantic-uncertain",
                        "high" if label == "private" else "medium",
                        0,
                        blob.content,
                    )
                )
    except Exception:
        # Never surface library exceptions, model paths, input, or subprocess diagnostics.
        result.errors.append("Local semantic review incomplete; check local model and limits")
