"""Phase 1 reference pipeline — deliberately naive.

For one hour: download -> transform (your whitelist SELECT) -> write
hourly-partitioned Parquet -> delete the raw file. No ledger, no resume yet;
that arrives in Phase 2. This is the "before" state on purpose.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

import duckdb

from backfill.parsers import registry
from backfill.sources import gharchive


def partition_path(base: Path, hour: datetime) -> Path:
    """Output path for one hour — partitioned by day then hour (aligned on the work unit)."""
    return (
        base
        / f"dt={hour.year}-{hour.month:02d}-{hour.day:02d}"
        / f"hour={hour.hour:02d}"
        / "events.parquet"
    )


def ingest_hour(hour: datetime, work_dir: Path, output_dir: Path) -> int:
    """Download -> transform -> write Parquet -> delete raw. Returns rows written."""
    raw = gharchive.download(hour, work_dir)
    out = partition_path(output_dir, hour)
    tmp = out.with_name(out.name + ".tmp")
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        # Route the date to the right era parser (handles schema drift).
        select = registry.parser_for(hour).sql(raw.as_posix())
        con = duckdb.connect()
        # Atomic swap: write to a temp file, then os.replace over the final path.
        # A reader sees the old-or-new file, never a partial one; a crash mid-write
        # leaves only the .tmp, so the final partition is never corrupt (ADR 005).
        con.execute(f"COPY ({select}) TO '{tmp.as_posix()}' (FORMAT PARQUET)")
        result = con.execute(f"SELECT count(*) FROM read_parquet('{tmp.as_posix()}')").fetchone()
        os.replace(tmp, out)
        return int(result[0]) if result else 0
    finally:
        # Never retain raw — the <256 GB disk rule. Download -> process -> discard.
        raw.unlink(missing_ok=True)
        tmp.unlink(missing_ok=True)  # leftover temp on failure — the final stays intact


def ingest_day(day: datetime, work_dir: Path, output_dir: Path) -> dict[int, int]:
    """Ingest all 24 hours of a day. Returns {hour: rows_written}."""
    start = day.replace(hour=0, minute=0, second=0, microsecond=0)
    written: dict[int, int] = {}
    for h in range(24):
        hour = start + timedelta(hours=h)
        written[hour.hour] = ingest_hour(hour, work_dir, output_dir)
    return written
