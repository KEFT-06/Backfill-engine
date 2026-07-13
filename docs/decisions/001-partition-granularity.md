# ADR 001 — Partition granularity: hourly

- **Status:** Accepted
- **Date:** 2026-07-12

## Context

GH Archive publishes one `.json.gz` file per hour. The backfill must be resumable
("die at 60%, resume exactly"), survive corrupt files, and never double-count.
The unit of work registered in the ledger — the *partition* — has to be chosen.
For one year: hourly = ~8,760 partitions, daily = ~365, monthly = ~12.

## Decision

**One hourly file = one partition = one unit of work.**

## Rationale (the interview answer)

- **Minimal blast radius.** A crash or a corrupt file is localised to exactly one
  hour, not buried inside a 24-file batch.
- **Cheap, idempotent re-run.** Replaying a partition means re-downloading *one*
  file and re-writing *one* partition. Wasted work on resume is minimal.
- **Surgical quarantine.** A poison pill isolates exactly one hour; the backfill
  keeps going on the other 8,759.
- **Row count is not a cost.** 8,760 ledger rows is noise for Postgres. The only
  real downside — many small output files — is **not** solved by coarsening the
  work unit; it is solved by **compaction at the sink** (Phase 7). Work
  granularity and storage granularity are decoupled.
- **The narrative.** "Resume exactly where it died" is only crisp at a fine
  granularity.

## Alternatives considered

- **Daily (365/yr).** Fewer ledger rows, but a single corrupt file taints a whole
  day, re-runs re-download 24 files, and quarantine is coarse. Rejected.
- **Monthly (12/yr).** Blast radius of a month, ~720-file re-runs, resume story
  becomes vague. Rejected — kept only as a foil.

## Consequences

- Sink must compact small hourly outputs into larger files (Phase 7).
- Ledger carries ~8.7k rows/year — trivial.
