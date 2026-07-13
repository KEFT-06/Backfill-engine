# ADR 002 — No Spark

- **Status:** Accepted (claim to be *measured* in Phase 7)
- **Date:** 2026-07-12

## Context

The instinct for "reprocess years of history" is Spark. The claim of this project
is that a **well-partitioned** workload is embarrassingly parallel at the partition
level and fits a single node with DuckDB or Polars, at a fraction of the
operational cost.

## Decision

**No Spark.** Single-node compute (DuckDB or Polars — see Phase 1), parallelism via
independent partitions pulled from the ledger.

## Rationale

- Each hourly partition is independent and small (~1 GB decompressed). There is no
  cross-partition shuffle, which is exactly where Spark earns its complexity.
- A JVM cluster, its tuning, and its ops burden are a **negative signal** in an
  interview when the data shape doesn't require them.
- Concurrency is a `max_concurrency` knob over the ledger, not a cluster.

## To be proven (Phase 7)

- [ ] Measured rows/s on this single node.
- [ ] Cost/€ vs. the Spark alternative it replaces.
- [ ] Honest note if the numbers contradict the claim.

## Alternatives considered

- **Spark (local or cluster).** Rejected for this data shape; revisit only if
  benchmarks show a single node can't keep up.
