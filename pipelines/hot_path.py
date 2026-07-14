"""The daily hot path — processes ONLY recent partitions (>= cutoff).

Isolated from the backfill (which touches only the past, < cutoff) by disjoint date
ranges: they never claim or write the same partition, so a heavy backfill can never
slow production. This is the Phase 5 isolation strategy (ADR 004), enforced in code —
no locks, no contention, because there is nothing shared to contend over.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import psycopg

from backfill.runner import worker


def run_hot_path(
    conn: psycopg.Connection[Any],
    process: worker.Processor,
    cutoff: datetime,
) -> dict[str, int]:
    """Process only partitions at or after `cutoff` (production's recent window)."""
    return worker.run(conn, process, min_hour=cutoff)
