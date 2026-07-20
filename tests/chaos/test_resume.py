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


def _status_counts(conn: psycopg.Connection[tuple[object, ...]]) -> dict[str, int]:
    rows = conn.execute("SELECT status, count(*) FROM ledger GROUP BY status").fetchall()
    return {str(s): int(str(n)) for s, n in rows}


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

        # h0,h1,h2 are 'done'; h3 is orphaned in 'running'; h4..h9 are 'pending'.
        running = conn.execute("SELECT count(*) FROM ledger WHERE status = 'running'").fetchone()
        assert running is not None and running[0] == 1

        # Restart: requeue the orphan, then finish everything — tracking what it touches.
        resumed: list[datetime] = []

        def finishing(hour: datetime) -> tuple[int, str]:
            resumed.append(hour)
            return 1, "ok"

        worker.run(conn, finishing)

        assert _status_counts(conn) == {"done": 10}      # zero gap: every partition finished
        assert set(resumed) == set(hours[3:])            # resume did ONLY the remaining work
        assert not set(resumed) & set(hours[:3])         # never re-did the already-'done' ones
    finally:
        conn.close()
