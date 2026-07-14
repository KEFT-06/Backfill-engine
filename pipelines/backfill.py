"""Phase 3 — the real historical backfill entry point.

This is the hand-written, ledger-driven backfill (Dagster will wrap it in Phase 5).
It seeds a date range into the ledger, then runs the runner with the REAL processor
(download → transform → write Parquet). Expect it to hit real incidents — that is
the point of Phase 3; document each one hot in docs/incidents.md.

Run it:  python -m pipelines.backfill
Change the range with the constants below (start small, then widen).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import psycopg

from backfill.config import get_settings
from backfill.ledger import repository
from backfill.runner import worker

# --- Backfill window (start small; widen once it survives) ---
START = datetime(2015, 1, 1, 0)
END = datetime(2015, 1, 4, 0)  # exclusive → 3 days = 72 hourly partitions

WORK_DIR = Path("data/_work")       # raw files land here, then get deleted
OUTPUT_DIR = Path("data/reference")  # hourly Parquet output


def seed(conn: psycopg.Connection, start: datetime, end: datetime) -> int:
    """Enqueue every hour in [start, end) into the ledger (idempotent)."""
    hours: list[datetime] = []
    cursor = start
    while cursor < end:
        hours.append(cursor)
        cursor += timedelta(hours=1)
    repository.enqueue_partitions(conn, hours)
    return len(hours)


def main() -> None:
    settings = get_settings()
    with psycopg.connect(settings.pg_dsn) as conn:
        n = seed(conn, START, END)
        print(f"Semé {n} partitions horaires ({START:%Y-%m-%d} → {END:%Y-%m-%d}).")
        process = worker.gharchive_processor(WORK_DIR, OUTPUT_DIR)
        print("Backfill lancé (téléchargement + transformation réels)...")
        stats = worker.run(conn, process, settings.max_attempts)
        print(f"Terminé : {stats}")


if __name__ == "__main__":
    main()
