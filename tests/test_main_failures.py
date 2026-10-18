"""A failing quarter must not starve later quarters in a scheduled run."""

import argparse
import builtins
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

TERMS = ["202615", "202625", "202635"]


@pytest.fixture
def run_context(monkeypatch, tmp_path):
    monkeypatch.setenv("DREXEL_EMAIL", "test@example.test")
    monkeypatch.setenv("DREXEL_PASSWORD", "test")
    import main

    monkeypatch.setattr(main, "authenticated_session", lambda: object())
    monkeypatch.setattr(
        main, "send_request", lambda *args: SimpleNamespace(text="catalogue")
    )
    monkeypatch.setattr(
        main, "discover_terms", lambda html: dict.fromkeys(TERMS, "Quarter")
    )
    monkeypatch.setattr(main.db, "initialize", lambda *args: None)
    monkeypatch.setattr(main.db, "update_catalogue", lambda *args: None)
    args = argparse.Namespace(
        db=True,
        migrate_only=False,
        all_quarters=True,
        term=None,
        ratings=True,
        all_colleges=True,
        no_file=False,
        output_file=str(tmp_path / "courses.json"),
    )
    return main, args


def install_failures(monkeypatch, main, args, kind, failed_terms):
    attempted = []
    published = []

    def scrape(**kwargs):
        code = kwargs["term_code"]
        attempted.append(code)
        if code in failed_terms:
            if kind == "scrape":
                raise TimeoutError("sensitive-upstream-response")
            if kind == "empty":
                return {}
        return {"12345": {"crn": 12345}}

    def publish(data, code):
        if kind == "database" and code in failed_terms:
            raise RuntimeError("sensitive-database-error")
        published.append(code)

    def open_file(filename, *open_args, **kwargs):
        if kind == "file" and (
            not args.all_quarters or any(code in filename for code in failed_terms)
        ):
            raise OSError("sensitive-filesystem-error")
        return builtins.open(filename, *open_args, **kwargs)

    monkeypatch.setattr(main, "scrape", scrape)
    monkeypatch.setattr(main.db, "populate_db", publish)
    monkeypatch.setattr(main, "open", open_file, raising=False)
    return attempted, published


@pytest.mark.parametrize("kind", ["scrape", "empty", "file", "database"])
@pytest.mark.parametrize("failed_terms", [TERMS[:1], TERMS[:2]])
def test_all_quarters_continue_and_report_failures(
    run_context, monkeypatch, capsys, kind, failed_terms
):
    main, args = run_context
    attempted, published = install_failures(monkeypatch, main, args, kind, failed_terms)
    with pytest.raises(
        RuntimeError, match="Quarters failed: " + ", ".join(failed_terms)
    ):
        main.main(args)
    assert attempted == TERMS
    assert published == [code for code in TERMS if code not in failed_terms]
    assert "sensitive-" not in capsys.readouterr().out


@pytest.mark.parametrize(
    "kind,error",
    [
        ("scrape", TimeoutError),
        ("empty", ValueError),
        ("file", OSError),
        ("database", RuntimeError),
    ],
)
def test_single_quarter_propagates_original_error(
    run_context, monkeypatch, kind, error
):
    main, args = run_context
    args.all_quarters = False
    args.term = TERMS[0]
    attempted, published = install_failures(monkeypatch, main, args, kind, TERMS[:1])
    with pytest.raises(error) as raised:
        main.main(args)
    assert not str(raised.value).startswith("Quarters failed:")
    assert attempted == TERMS[:1]
    assert published == []


def test_all_quarters_success(run_context, monkeypatch):
    main, args = run_context
    attempted, published = install_failures(monkeypatch, main, args, "none", [])
    main.main(args)
    assert attempted == published == TERMS
