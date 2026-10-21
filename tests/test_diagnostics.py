"""Failure evidence survives pod loss without publishing private exception data."""

import os
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import diagnostics


def test_wrapped_failure_preserves_root_type_and_frames_not_sensitive_data():
    try:
        try:
            raise TimeoutError("Authorization: secret-token; private response body")
        except TimeoutError as exc:
            raise RuntimeError("private-database-url") from exc
    except RuntimeError as exc:
        report = diagnostics.format_failure(exc)
    assert "RuntimeError" in report
    assert "TimeoutError" in report
    assert "test_diagnostics.py:" in report
    assert "secret-token" not in report
    assert "private" not in report
    assert "raise TimeoutError" not in report


def test_chain_cycles_and_deep_stacks_are_bounded():
    def recurse(depth):
        if depth:
            return recurse(depth - 1)
        raise ValueError("secret")

    try:
        recurse(50)
    except ValueError as exc:
        exc.__cause__ = exc
        report = diagnostics.format_failure(exc)
    assert report.count("  at ") == 32
    assert "earlier frames omitted" in report
    assert "chain truncated" in report
    assert "secret" not in report


def test_archive_retention_does_not_touch_unrelated_files(monkeypatch, tmp_path):
    monkeypatch.setenv("SCRAPER_FAILURE_DIR", str(tmp_path))
    monkeypatch.setattr(diagnostics, "MAX_RECORDS", 2)
    unrelated = tmp_path / "profile_output.pstat"
    unrelated.write_text("keep")
    old = tmp_path / "failure-20000101T000000Z-old.log"
    old.write_text("old diagnostic")
    expired = time.time() - diagnostics.MAX_AGE_SECONDS - 1
    os.utime(old, (expired, expired))
    paths = [diagnostics.persist_failure(f"TimeoutError {i}") for i in range(3)]
    assert not old.exists()
    assert not paths[0].exists()
    assert paths[1].exists() and paths[2].exists()
    assert paths[2].stat().st_mode & 0o777 == 0o600
    assert "TimeoutError 2" in paths[2].read_text()
    assert unrelated.read_text() == "keep"


def test_archive_error_does_not_mask_original_failure(monkeypatch, tmp_path, capsys):
    not_directory = tmp_path / "file"
    not_directory.write_text("keep")
    monkeypatch.setenv("SCRAPER_FAILURE_DIR", str(not_directory / "failures"))
    assert diagnostics.persist_failure("TimeoutError") is None
    assert "Could not persist failure diagnostic" in capsys.readouterr().out
