"""Deterministic, ORDER-INDEPENDENT partition checksum.

Hash each row, then XOR the row hashes together. XOR is commutative and associative,
so the result depends only on the SET of rows, not the order they were written — the
same content always yields the same checksum. That is exactly what lets a checksum
*prove* idempotence: replay a partition, get the same fingerprint.
"""

from __future__ import annotations

from pathlib import Path

import duckdb

# Hash of one row's content (the stable output contract), as a single concatenated
# string so it works regardless of column types; COALESCE keeps NULLs deterministic.
_ROW_HASH = (
    "hash("
    "COALESCE(id, '')          || '|' || "
    "COALESCE(event_type, '')  || '|' || "
    "COALESCE(actor_login, '') || '|' || "
    "COALESCE(repo_name, '')   || '|' || "
    "CAST(created_at AS VARCHAR))"
)


def partition_checksum(parquet_path: Path) -> str:
    """Order-independent hex checksum of a partition's rows ('0' if empty)."""
    row = duckdb.sql(
        f"SELECT bit_xor({_ROW_HASH}) FROM read_parquet('{parquet_path.as_posix()}')"
    ).fetchone()
    value = row[0] if row else None
    return f"{value:016x}" if value is not None else "0"
