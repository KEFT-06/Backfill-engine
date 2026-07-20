"""Phase 7 compaction — merge a day's many small hourly Parquet files into one.

The hourly files exist because the work unit is hourly (ADR 001), which is great for
idempotent per-partition overwrites but creates the classic "small files problem" for
readers. Compaction is a SEPARATE, read-only-then-atomic-swap operation: it never
touches the hourly write path, so per-partition idempotence is preserved.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import duckdb


def compact_day(output_dir: Path, day: datetime) -> tuple[int, int]:
    """Merge dt=<day>/hour=*/events.parquet into dt=<day>/day.parquet (atomic).

    Returns (hourly_files_merged, rows_in_daily_file).
    """
    dt = f"dt={day.year}-{day.month:02d}-{day.day:02d}"
    day_dir = output_dir / dt
    hourly = sorted(day_dir.glob("hour=*/events.parquet"))
    if not hourly:
        return 0, 0

    src = (day_dir / "hour=*" / "events.parquet").as_posix()
    target = day_dir / "day.parquet"
    tmp = target.with_name("day.parquet.tmp")
    duckdb.sql(f"COPY (SELECT * FROM read_parquet('{src}')) TO '{tmp.as_posix()}' (FORMAT PARQUET)")
    result = duckdb.sql(f"SELECT count(*) FROM read_parquet('{tmp.as_posix()}')").fetchone()
    os.replace(tmp, target)
    return len(hourly), int(result[0]) if result else 0
