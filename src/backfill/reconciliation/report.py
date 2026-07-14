"""Reconciliation report — the numbers-first proof that the backfill is correct.

For every 'done' partition, re-read the target Parquet and recompute its row count and
checksum, then compare to the receipt the ledger stored at write time. Any mismatch is
a discrepancy that must be explained (an unexplained one is a bug). Also reports gaps
(partitions not 'done').
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import duckdb
import psycopg

from backfill.reconciliation import checksums
from backfill.reference import partition_path


@dataclass
class Discrepancy:
    partition_hour: datetime
    kind: str
    detail: str


@dataclass
class Report:
    partitions_done: int = 0
    rows_total: int = 0
    not_done: dict[str, int] = field(default_factory=dict)
    discrepancies: list[Discrepancy] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.discrepancies


def _parquet_rows(path: Path) -> int:
    row = duckdb.sql(f"SELECT count(*) FROM read_parquet('{path.as_posix()}')").fetchone()
    return int(row[0]) if row else 0


def reconcile(conn: psycopg.Connection[Any], output_dir: Path) -> Report:
    """Compare the ledger's receipts against what is actually on storage."""
    rep = Report()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT partition_hour, rows_written, checksum FROM ledger "
            "WHERE status = 'done' ORDER BY partition_hour"
        )
        done = cur.fetchall()
        cur.execute("SELECT status, count(*) FROM ledger WHERE status <> 'done' GROUP BY status")
        rep.not_done = dict(cur.fetchall())

    for partition_hour, rows_written, ledger_ck in done:
        rep.partitions_done += 1
        rep.rows_total += rows_written or 0
        path = partition_path(output_dir, partition_hour)
        if not path.exists():
            rep.discrepancies.append(
                Discrepancy(partition_hour, "fichier manquant", "ledger 'done' mais aucun Parquet")
            )
            continue
        actual_ck = checksums.partition_checksum(path)
        if actual_ck != ledger_ck:
            rep.discrepancies.append(
                Discrepancy(partition_hour, "checksum", f"ledger={ledger_ck} storage={actual_ck}")
            )
        actual_rows = _parquet_rows(path)
        if actual_rows != rows_written:
            rep.discrepancies.append(
                Discrepancy(
                    partition_hour, "comptage", f"ledger={rows_written} storage={actual_rows}"
                )
            )
    return rep


def format_report(rep: Report) -> str:
    lines = [
        "=== RAPPORT DE RECONCILIATION ===",
        f"Partitions 'done'     : {rep.partitions_done}",
        f"Lignes totales        : {rep.rows_total:,}",
        f"Partitions non-'done' : {rep.not_done or 'aucune'}",
        f"Ecarts detectes       : {len(rep.discrepancies)}",
    ]
    lines.extend(
        f"  - {d.partition_hour:%Y-%m-%d %Hh} [{d.kind}] {d.detail}" for d in rep.discrepancies
    )
    lines.append(
        "VERDICT : " + ("OK, zero ecart inexplique." if rep.ok else "ECARTS a expliquer !")
    )
    return "\n".join(lines)
