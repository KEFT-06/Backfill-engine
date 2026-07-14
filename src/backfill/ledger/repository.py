"""Ledger repository — transactional claim / commit of partitions.

🔑 The core of the project. claim_next() is what makes concurrency safe:
multiple workers pull work at once and never grab the same partition.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any

import psycopg

# Pick the oldest pending partition AND lock it in one step. FOR UPDATE locks the
# row; SKIP LOCKED makes other workers skip rows already locked instead of waiting.
# Optional [min_hour, max_hour) bounds let the hot path and the backfill claim
# DISJOINT date ranges (recent vs past) so they never contend (Phase 5 isolation).
CLAIM_SQL = """
    SELECT partition_hour
    FROM ledger
    WHERE status = 'pending'
      AND (%(min_hour)s IS NULL OR partition_hour >= %(min_hour)s)
      AND (%(max_hour)s IS NULL OR partition_hour <  %(max_hour)s)
    ORDER BY partition_hour
    LIMIT 1
    FOR UPDATE SKIP LOCKED
"""

# Mark the claimed partition as taken. Once committed, 'running' (not the lock)
# is what keeps other workers away during the long processing that follows.
MARK_RUNNING_SQL = """
    UPDATE ledger
    SET status = 'running', attempts = attempts + 1, started_at = now()
    WHERE partition_hour = %s
"""


def enqueue_partitions(conn: psycopg.Connection[Any], hours: Iterable[datetime]) -> None:
    """Insert partitions as 'pending'. Idempotent: ON CONFLICT DO NOTHING."""
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO ledger (partition_hour) VALUES (%s) "
            "ON CONFLICT (partition_hour) DO NOTHING",
            [(h,) for h in hours],
        )
    conn.commit()


def claim_next(
    conn: psycopg.Connection[Any],
    min_hour: datetime | None = None,
    max_hour: datetime | None = None,
) -> datetime | None:
    """Atomically claim the oldest pending partition in [min_hour, max_hour), or None.

    Everything happens in ONE short transaction (the `with conn.transaction()`):
    the SELECT locks the row, the UPDATE marks it 'running', and the commit at
    the end of the block releases the lock. No two workers can claim the same row.

    The optional bounds enforce hot-path / backfill isolation: give the hot path
    min_hour=cutoff and the backfill max_hour=cutoff and their work sets are disjoint.
    """
    with conn.transaction():
        row = conn.execute(
            CLAIM_SQL, {"min_hour": min_hour, "max_hour": max_hour}
        ).fetchone()
        if row is None:
            return None
        partition_hour: datetime = row[0]
        conn.execute(MARK_RUNNING_SQL, (partition_hour,))
        return partition_hour


# Finish a task successfully: flip 'running' -> 'done' and write the "receipt"
# (rows produced + a checksum) that reconciliation will later verify.
MARK_DONE_SQL = """
    UPDATE ledger
    SET status = 'done', rows_written = %s, checksum = %s, finished_at = now()
    WHERE partition_hour = %s
"""


def mark_done(
    conn: psycopg.Connection[Any],
    partition_hour: datetime,
    rows_written: int,
    checksum: str,
) -> None:
    """Mark a partition as successfully done, recording its result for later proof."""
    conn.execute(MARK_DONE_SQL, (rows_written, checksum, partition_hour))
    conn.commit()


# On failure, one CASE decides everything: if it has already been attempted enough
# times, quarantine it (a poison pill — set aside so the backfill keeps going);
# otherwise put it back to 'pending' to be retried later.
MARK_FAILED_SQL = """
    UPDATE ledger
    SET status = CASE WHEN attempts >= %s THEN 'quarantined' ELSE 'pending' END,
        error = %s,
        finished_at = now()
    WHERE partition_hour = %s
    RETURNING status
"""


def mark_failed(
    conn: psycopg.Connection[Any],
    partition_hour: datetime,
    error: str,
    max_attempts: int = 5,
) -> str:
    """Record a failure. Returns the new status: 'pending' (will retry) or
    'quarantined' (poison pill, set aside; the backfill continues)."""
    row = conn.execute(MARK_FAILED_SQL, (max_attempts, error, partition_hour)).fetchone()
    conn.commit()
    new_status: str = row[0] if row else "unknown"
    return new_status


def requeue_stale_running(
    conn: psycopg.Connection[Any],
    min_hour: datetime | None = None,
    max_hour: datetime | None = None,
) -> int:
    """Reset partitions stuck in 'running' (a worker crashed mid-processing) back to
    'pending', so they get reprocessed instead of being lost forever. Returns how
    many were reset.

    Scoped to [min_hour, max_hour) so that a stream only recovers ITS OWN orphans:
    the hot path must not reset the backfill's in-flight partitions, and vice versa.
    (Still assumes one runner per range; with several per range you'd gate on a
    staleness timeout / heartbeat.)
    """
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE ledger SET status = 'pending' "
            "WHERE status = 'running' "
            "  AND (%(min_hour)s IS NULL OR partition_hour >= %(min_hour)s) "
            "  AND (%(max_hour)s IS NULL OR partition_hour <  %(max_hour)s)",
            {"min_hour": min_hour, "max_hour": max_hour},
        )
        reset = cur.rowcount
    conn.commit()
    return reset
