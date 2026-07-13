# ADR 004 — Hot-path / backfill isolation strategy

- **Status:** Proposed — decided in Phase 5
- **Date:** _tbd_

## Context

Two processes write to the same target table: the daily hot path (yesterday's
partition) and the backfill (the past). We must be able to **prove production was
never interrupted**.

## Options to weigh (Phase 5)

- Partition-level isolation (they never touch the same partitions).
- Shadow table + atomic swap (see ADR 005).
- Locking.

## Decision

_tbd — Phase 5. Must come with a trace proving the daily job kept running with no
latency regression throughout the backfill._
