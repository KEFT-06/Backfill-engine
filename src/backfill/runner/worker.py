"""The runner loop — marries the ledger and the processing pipeline.

    recover crashed 'running' partitions
    while there is pending work:
        claim → process → mark_done   (or mark_failed on error)

The processing step is injected (a `Processor`), so production wires in the real
GH Archive pipeline while tests can inject a fast, deterministic one.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

import psycopg

from backfill.ledger import repository
from backfill.reference import ingest_hour

# Process one hour → (rows_written, checksum).
Processor = Callable[[datetime], tuple[int, str]]


def gharchive_processor(work_dir: Path, output_dir: Path) -> Processor:
    """The real processor: download → transform → write Parquet (Phase 1 pipeline)."""

    def process(hour: datetime) -> tuple[int, str]:
        rows = ingest_hour(hour, work_dir, output_dir)
        return rows, f"rows={rows}"  # placeholder checksum; real ones in Phase 6

    return process


def run(
    conn: psycopg.Connection[Any],
    process: Processor,
    max_attempts: int = 5,
    min_hour: datetime | None = None,
    max_hour: datetime | None = None,
) -> dict[str, int]:
    """Drain the ledger of pending work in [min_hour, max_hour). Returns {'done','failed'}.

    First recovers any partition orphaned in 'running' by a previous crash — that
    is what makes a restart resume instead of leaving a gap. The [min_hour, max_hour)
    bounds keep the hot path and the backfill on disjoint date ranges (Phase 5).
    """
    repository.requeue_stale_running(conn, min_hour, max_hour)
    stats = {"done": 0, "failed": 0}
    while True:
        hour = repository.claim_next(conn, min_hour, max_hour)
        if hour is None:
            break
        try:
            rows, checksum = process(hour)
        except Exception as exc:  # noqa: BLE001 — any failure quarantines/retries, never halts
            repository.mark_failed(conn, hour, str(exc), max_attempts)
            stats["failed"] += 1
        else:
            repository.mark_done(conn, hour, rows, checksum)
            stats["done"] += 1
    return stats
