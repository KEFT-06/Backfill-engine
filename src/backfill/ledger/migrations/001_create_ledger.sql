-- 001_create_ledger.sql
-- The partition registry: one row per hourly partition. This table DRIVES the
-- whole backfill — the runner never loops over a list, it asks the ledger for work.

CREATE TABLE IF NOT EXISTS ledger (
    partition_hour  TIMESTAMP     PRIMARY KEY,          -- identity: one hour = one partition
    status          TEXT          NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'running', 'done', 'failed', 'quarantined')),
    attempts        INT           NOT NULL DEFAULT 0,   -- retries done so far (backoff + quarantine threshold)
    rows_written    BIGINT,                             -- proof: how many rows this partition produced
    checksum        TEXT,                               -- proof: deterministic fingerprint (idempotence)
    started_at      TIMESTAMPTZ,                        -- when a worker claimed it
    finished_at     TIMESTAMPTZ,                        -- when it finished
    error           TEXT                                -- last error message (poison-pill debugging)
);

-- Speeds up claim_next() (finding the oldest 'pending'). Partial index: it only
-- indexes 'pending' rows, so it stays tiny even when millions of rows are 'done'.
CREATE INDEX IF NOT EXISTS ix_ledger_pending
    ON ledger (partition_hour)
    WHERE status = 'pending';
