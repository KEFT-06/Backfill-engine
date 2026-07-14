"""The partition checksum must be order-independent (same rows, any order → same hash)."""

from __future__ import annotations

from pathlib import Path

import duckdb

from backfill.reconciliation.checksums import partition_checksum

_ROWS = (
    "(SELECT * FROM (VALUES "
    "('1','PushEvent','u1','o/r1',TIMESTAMP '2015-01-01 00:00:00'), "
    "('2','WatchEvent','u2','o/r2',TIMESTAMP '2015-01-01 00:00:01'), "
    "('3','ForkEvent','u3',NULL,TIMESTAMP '2015-01-01 00:00:02')"
    ") t(id, event_type, actor_login, repo_name, created_at) {order})"
)


def _write(path: Path, order: str) -> None:
    duckdb.sql(f"COPY {_ROWS.format(order=order)} TO '{path.as_posix()}' (FORMAT PARQUET)")


def test_checksum_is_order_independent(tmp_path: Path) -> None:
    a, b = tmp_path / "a.parquet", tmp_path / "b.parquet"
    _write(a, "ORDER BY id")
    _write(b, "ORDER BY id DESC")  # same rows, opposite order
    assert partition_checksum(a) == partition_checksum(b)


def test_checksum_detects_a_content_change(tmp_path: Path) -> None:
    a, b = tmp_path / "a.parquet", tmp_path / "b.parquet"
    _write(a, "ORDER BY id")
    duckdb.sql(
        "COPY (SELECT '9' AS id, 'X' AS event_type, 'x' AS actor_login, "
        "'x' AS repo_name, TIMESTAMP '2015-01-01 00:00:00' AS created_at) "
        f"TO '{b.as_posix()}' (FORMAT PARQUET)"
    )
    assert partition_checksum(a) != partition_checksum(b)
