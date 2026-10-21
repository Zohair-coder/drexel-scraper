"""Bounded failure diagnostics without exception messages, source, or locals."""

from datetime import datetime, timezone
import os
from pathlib import Path
import time
import traceback
from uuid import uuid4


MAX_RECORDS = 2048
MAX_AGE_SECONDS = 14 * 24 * 60 * 60


class QuarterFailures(RuntimeError):
    """Carry already-sanitized diagnostics through the aggregate failure."""

    def __init__(self, failures: dict[str, str]) -> None:
        self.diagnostics = "\n\n".join(
            f"Quarter {code}:\n{detail}" for code, detail in failures.items()
        )
        super().__init__(f"Quarters failed: {', '.join(failures)}")


def format_failure(exc: BaseException) -> str:
    """Keep exception types and code locations, including wrapped root causes."""
    lines = []
    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen and len(seen) < 8:
        seen.add(id(current))
        lines.append(type(current).__name__)
        # walk_tb avoids loading source lines or formatting exception values.
        frames = list(traceback.walk_tb(current.__traceback__))
        if len(frames) > 32:
            lines.append("  [earlier frames omitted]")
        for frame, lineno in frames[-32:]:
            lines.append(
                f"  at {Path(frame.f_code.co_filename).name}:{lineno}"
                f" in {frame.f_code.co_name}"
            )
        if isinstance(current, QuarterFailures):
            lines.append(current.diagnostics)
        # Even a suppressed context can identify the underlying network/DB
        # failure safely: no messages, response data, or locals are included.
        current = current.__cause__ or current.__context__
        if current is not None:
            lines.append("Caused by / during handling of:")
    if current is not None:
        lines.append("[exception chain truncated]")
    return "\n".join(lines)


def persist_failure(diagnostic: str) -> Path | None:
    """Persist sanitized evidence on the existing PVC, independent of pod GC.

    Keep up to 14 days / 2048 records. Archive failures must never prevent
    remaining quarters from running or suppress the exception email.
    """
    try:
        directory = Path(os.environ.get("SCRAPER_FAILURE_DIR", "performance/failures"))
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        path = directory / f"failure-{stamp}-{uuid4().hex}.log"
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as stream:
            stream.write(f"UTC: {stamp}\n{diagnostic}\n")
        print(f"Failure diagnostic saved: {path.name}", flush=True)
        records = sorted(directory.glob("failure-*.log"), reverse=True)
        cutoff = time.time() - MAX_AGE_SECONDS
        for index, record in enumerate(records):
            if index >= MAX_RECORDS or record.stat().st_mtime < cutoff:
                record.unlink()
        return path
    except OSError as exc:
        print(
            f"Could not persist failure diagnostic ({type(exc).__name__})", flush=True
        )
        return None
