# ADR 004 — Hot-path / backfill isolation strategy

- **Status:** Accepted
- **Date:** 2026-07-14

## Context

Two processes write to the same target table: the daily hot path (recent partitions)
and the backfill (the past). We must be able to **prove production was never
interrupted** and that the backfill never degraded the daily job's latency.

## Decision

**Partition-level isolation by disjoint date ranges.** A shared `cutoff`: the hot path
processes only partitions `>= cutoff`, the backfill only `< cutoff`. They therefore
never claim or write the same partition.

Enforced in code: `claim_next` and `requeue_stale_running` take `[min_hour, max_hour)`
bounds; the hot path passes `min_hour=cutoff`, the backfill `max_hour=cutoff`.

## Rationale (the interview answer)

- A **lock** would make the hot path **wait** while the backfill writes — that is added
  latency, the exact opposite of the goal. A lock *manages* contention.
- Disjoint ranges **remove** the contention entirely: there is nothing shared to fight
  over, so the hot path never waits. Latency stays flat.
- "Zero downtime" becomes provable **by construction**: the two work sets are disjoint
  date ranges — they cannot intersect.

## Consequences

- `requeue_stale_running` had to become range-scoped too, so the hot path never resets
  the backfill's in-flight partitions (and vice versa).
- Proof (`isolation_proof.py`): run the backfill over 400 past partitions in a thread
  while measuring the hot path's per-partition latency; show it stays flat and the two
  streams share zero partitions.

## Alternatives considered

- **Shadow table + atomic swap (blue/green).** Needed only if prod and backfill must
  touch the *same* partitions; ours are naturally disjoint in time. Rejected as
  unnecessary complexity here.
- **Locking.** Rejected: it degrades hot-path latency — the thing we must protect.
