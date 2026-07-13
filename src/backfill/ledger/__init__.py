"""🔑 Ledger — the heart of the project.

The partition registry is the single driver of the backfill. The runner never
loops over a Python list; it repeatedly asks the ledger for the next partition
to process. This is what makes the backfill resumable: kill the process, restart,
and it picks up from the ledger's state — no gaps, no duplicates.

Planned modules (designed by you in Phase 2):
    models.py      partition_key, status, attempts, rows_written, checksum,
                   started_at, finished_at, error
    repository.py  claim_next() with SELECT ... FOR UPDATE SKIP LOCKED
    migrations/    SQL schema
"""
