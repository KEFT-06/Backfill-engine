"""Chaos: kill a worker mid-run, restart, prove zero gap / zero duplicate.

Needs Postgres (the ledger). Skips cleanly when it is unavailable so CI stays green.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import psycopg
import pytest

from backfill.ledger import repository
from backfill.runner import worker


class _Killed(BaseException):
    """Escapes the runner's `except Exception` — simulates a real process kill."""


def _connect() -> psycopg.Connection[tuple[object, ...]]:
    try:
        return psycopg.connect(
            host="localhost", port=5433, user="backfill", password="backfill",
            dbname="backfill", connect_timeout=3,
        )
    except psycopg.Error:
        pytest.skip("Postgres indisponible (ledger requis pour le test chaos)")


def test_kill_and_resume_no_gap_no_dup() -> None:
    conn = _connect()
    try:
        hours = [datetime(2017, 1, 1) + timedelta(hours=h) for h in range(10)]
        conn.execute("TRUNCATE ledger")
        conn.commit()
        repository.enqueue_partitions(conn, hours)

        seen: list[datetime] = []

        def killing(hour: datetime) -> tuple[int, str]:
            seen.append(hour)
            if len(seen) == 4:
                raise _Killed  # kill mid-processing → this partition stays 'running'
            return 1, "ok"

        with pytest.raises(_Killed):
            worker.run(conn, killing)

        # One partition is orphaned in 'running'; the rest are done/pending.
        running = conn.execute("SELECT count(*) FROM ledger WHERE status = 'running'").fetchone()
        assert running is not None and running[0] == 1

        # Restart: requeue the orphan, then finish everything.
        worker.run(conn, lambda hour: (1, "ok"))

        statuses = dict(conn.execute("SELECT status, count(*) FROM ledger GROUP BY status").fetchall())
        assert statuses == {"done": 10}       # zero gap: every partition finished
        assert set(hours) <= set(seen)        # every partition was actually processed
    finally:
        conn.close()
