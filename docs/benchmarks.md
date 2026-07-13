# Benchmarks

> Throughput, partition size, concurrency, and cost. Filled in Phase 7 — with
> curves and a defensible recommendation, not vibes.

## Questions to answer with numbers

- How does throughput scale with concurrency? Where does it plateau (and why —
  CPU, disk, network, Postgres contention)?
- Optimal partition/output file size after compaction?
- Rows per euro, and the projected cost of the full backfill.
- The no-Spark claim (ADR 002), measured: rows/s on this single node vs. the
  Spark alternative it replaces.

## Results

_tbd — Phase 7._
