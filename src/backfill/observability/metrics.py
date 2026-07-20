"""Observability — progress / throughput / failure rate, read from the ledger."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import psycopg

_STATUSES = ("pending", "running", "done", "failed", "quarantined")


@dataclass
class Progress:
    pending: int = 0
    running: int = 0
    done: int = 0
    failed: int = 0
    quarantined: int = 0

    @property
    def total(self) -> int:
        return self.pending + self.running + self.done + self.failed + self.quarantined

    @property
    def pct_done(self) -> float:
        return 100.0 * self.done / self.total if self.total else 0.0


def progress(conn: psycopg.Connection[Any]) -> Progress:
    counts = dict(conn.execute("SELECT status, count(*) FROM ledger GROUP BY status").fetchall())
    return Progress(**{s: int(counts.get(s, 0)) for s in _STATUSES})
