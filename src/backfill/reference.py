"""Phase 1 reference pipeline — deliberately naive.

For one hour: download -> transform (your whitelist SELECT) -> write
hourly-partitioned Parquet -> delete the raw file. No ledger, no resume yet;
that arrives in Phase 2. This is the "before" state on purpose.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import duckdb

from backfill.sources import gharchive

# The business logic — YOUR transform. Kept as one readable constant so it stays
# easy to own and change. NOTE: valid for the 2015-era schema (`actor` is a struct);
# older eras drift, which is Phase 4.
TRANSFORM_SQL = """
    SELECT
        id::BIGINT   AS id,
        type         AS event_type,
        actor.login  AS actor_login,
        repo.name    AS repo_name,
        created_at   AS created_at
    FROM read_json_auto('{raw}')
"""


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
    try:
        out = partition_path(output_dir, hour)
        out.parent.mkdir(parents=True, exist_ok=True)
        select = TRANSFORM_SQL.format(raw=raw.as_posix())
        con = duckdb.connect()
        con.execute(f"COPY ({select}) TO '{out.as_posix()}' (FORMAT PARQUET)")
        result = con.execute(f"SELECT count(*) FROM read_parquet('{out.as_posix()}')").fetchone()
        return int(result[0]) if result else 0
    finally:
        # Never retain raw — the <256 GB disk rule. Download -> process -> discard.
        raw.unlink(missing_ok=True)


def ingest_day(day: datetime, work_dir: Path, output_dir: Path) -> dict[int, int]:
    """Ingest all 24 hours of a day. Returns {hour: rows_written}."""
    start = day.replace(hour=0, minute=0, second=0, microsecond=0)
    written: dict[int, int] = {}
    for h in range(24):
        hour = start + timedelta(hours=h)
        written[hour.hour] = ingest_hour(hour, work_dir, output_dir)
    return written
