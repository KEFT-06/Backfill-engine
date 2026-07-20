"""make chaos — kill a worker mid-run, restart, prove zero gap / zero duplicate.

Needs the stack up (`docker compose up -d`). ~10 seconds, reproducible.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import psycopg

from backfill.ledger import repository
from backfill.runner import worker

DSN = "postgresql://backfill:backfill@localhost:5433/backfill"


class _Killed(BaseException):
    """Escapes the runner's `except Exception` — simulates a real process kill."""


def main() -> None:
    hours = [datetime(2017, 1, 1) + timedelta(hours=h) for h in range(12)]
    with psycopg.connect(DSN) as conn:
        conn.execute("TRUNCATE ledger")
        conn.commit()
        repository.enqueue_partitions(conn, hours)

        seen: list[datetime] = []

        def killing(hour: datetime) -> tuple[int, str]:
            seen.append(hour)
            if len(seen) == 5:
                raise _Killed
            return 1, "ok"

        print("Backfill lance (12 partitions)... il va etre TUE a la 5e.")
        try:
            worker.run(conn, killing)
        except _Killed:
            counts = dict(conn.execute("SELECT status, count(*) FROM ledger GROUP BY status").fetchall())
            print(f"  💥 TUE apres {len(seen)} partitions. Etat du ledger : {counts}")

        print("Redemarrage du worker...")
        worker.run(conn, lambda hour: (1, "ok"))
        counts = dict(conn.execute("SELECT status, count(*) FROM ledger GROUP BY status").fetchall())
        print(f"  Etat final : {counts}")

        assert counts == {"done": 12}, counts
        print("✅ 12/12 done. Zero trou, zero doublon. Reprise apres kill : PROUVEE.")


if __name__ == "__main__":
    main()
