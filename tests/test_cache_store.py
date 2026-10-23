"""Regressions for persistent malformed cache failures and interrupted writes."""

import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import cache_store  # noqa: E402


@pytest.mark.parametrize("contents", [b"", b'{"partial":', b"\xff", b"null", b"[]"])
def test_invalid_cache_is_rebuildable_without_deleting_evidence(tmp_path, contents):
    path = tmp_path / "cache.json"
    path.write_bytes(contents)
    assert cache_store.load_cache(str(path)) == {}
    assert path.read_bytes() == contents
    cache_store.save_cache(str(path), {"recovered": None})
    assert cache_store.load_cache(str(path)) == {"recovered": None}


@pytest.mark.parametrize("failure", ["serialize", "replace"])
def test_failed_write_preserves_previous_cache(tmp_path, monkeypatch, failure):
    path = tmp_path / "cache.json"
    path.write_text('{"previous": null}')
    original = path.read_bytes()
    if failure == "serialize":
        data = {"first": 1, "bad": object()}
        error = TypeError
    else:
        data = {"new": 2}
        error = OSError

        def fail_replace(*args):
            raise OSError("injected failure")

        monkeypatch.setattr(cache_store.os, "replace", fail_replace)
    with pytest.raises(error):
        cache_store.save_cache(str(path), data)
    assert path.read_bytes() == original
    assert list(tmp_path.iterdir()) == [path]


def test_replacement_exposes_complete_json_only(tmp_path, monkeypatch):
    path = tmp_path / "cache.json"
    path.write_text('{"previous": 1}')
    replace = cache_store.os.replace

    def check_replace(source, destination):
        assert json.loads(path.read_text()) == {"previous": 1}
        assert Path(source).parent == path.parent
        assert json.loads(Path(source).read_text()) == {"next": [1, 2]}
        replace(source, destination)

    monkeypatch.setattr(cache_store.os, "replace", check_replace)
    cache_store.save_cache(str(path), {"next": [1, 2]})
    assert cache_store.load_cache(str(path)) == {"next": [1, 2]}


def test_permission_errors_are_not_mistaken_for_empty_cache(tmp_path, monkeypatch):
    def denied(*args, **kwargs):
        raise PermissionError("injected failure")

    monkeypatch.setattr("builtins.open", denied)
    with pytest.raises(PermissionError):
        cache_store.load_cache(str(tmp_path / "cache.json"))
