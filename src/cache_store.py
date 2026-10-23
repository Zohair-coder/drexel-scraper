"""Disposable scraper caches must not make a failed write poison later runs."""

import json
import os
from pathlib import Path
import tempfile
from typing import Any, cast


def load_cache(filename: str) -> dict[str, Any]:
    try:
        with open(filename) as f:
            data = json.load(f)
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, UnicodeDecodeError):
        # Do not log cache contents or remove the old file before a successful scrape.
        print(f"Invalid {Path(filename).name}; rebuilding cache", flush=True)
        return {}
    if not isinstance(data, dict):
        print(f"Invalid {Path(filename).name}; rebuilding cache", flush=True)
        return {}
    return cast(dict[str, Any], data)


def save_cache(filename: str, data: dict[str, Any]) -> None:
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        # Same directory/filesystem: readers see either the old or complete new JSON.
        with tempfile.NamedTemporaryFile(
            mode="w", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as f:
            temporary = Path(f.name)
            json.dump(data, f, indent=4)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
