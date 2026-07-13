"""🔑 Sinks — idempotence lives here.

Never a bare INSERT. Writing a partition means atomically OVERWRITING it, so that
replaying the same partition yields exactly the same result.

Planned modules (Phase 2/5):
    iceberg.py  atomic partition overwrite (Iceberg/Delta) — decision in ADR 004
    swap.py     blue/green table swap for hot-path / backfill isolation (Phase 5)
"""
