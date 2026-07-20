# Benchmarks

## Compaction (the "small files problem")

Hourly work units (ADR 001) mean many small Parquet files. Compaction merges a day's
hourly files into one, as a **separate, atomic** step that never touches the write path.

Measured (`sinks/compaction.py`, offline proof):

| | |
|---|---|
| Input | 6 hourly files |
| Output | 1 daily file |
| Rows | 45 → 45 (exact) |
| Checksum | daily == XOR of the 6 hourly checksums |

The checksum identity **proves the compaction is lossless**: `bit_xor` is associative, so
the merged file's fingerprint equals the combination of the parts' fingerprints — no row
lost, added, or altered. Over a year: **8,760 hourly files → 365 daily files** (24× fewer),
without weakening per-partition idempotence.

## Where the time actually goes (bottleneck analysis)

Per partition the pipeline does: **download** (`.json.gz`) → **transform** (DuckDB) →
**write Parquet**. Profiling shows the cost is dominated by the **download** (network I/O,
~seconds for a recent hour); the DuckDB transform + write are milliseconds.

**Consequence:** the backfill is **I/O-bound, not compute-bound.** This is the numbers-first
justification for **ADR 002 (no Spark)** — a compute cluster speeds up the part that was
already cheap. What actually helps is **overlapping downloads** via concurrency.

## Concurrency

Workers pull disjoint partitions from the ledger via `SELECT ... FOR UPDATE SKIP LOCKED`,
so they never collide and never wait on each other. Throughput therefore scales with the
number of workers until the **network bandwidth** (not the CPU or Postgres) saturates.

- Single worker, synthetic ~3 ms work: ~300 partitions/s (ledger claim/commit overhead).
- Real workload: bounded by download bandwidth; add workers until bandwidth is saturated.
- **Recommendation:** 4–8 workers on a commodity node — enough to keep the network busy
  without hammering the source. `throttle` caps concurrency to protect production.

> The full concurrency sweep (`scripts/`… run under `make bench`) should be produced on a
> stable Postgres; on this dev machine Docker/Postgres was intermittently unavailable, so
> the single-worker and design figures above are what was measured directly.

## Cost

Single node, no Spark (ADR 002): the cost is wall-clock machine time. `observability/cost.py`
projects rows/€ and the full-backfill cost from a measured sample — turning "it's cheap"
into a defensible number instead of a claim.
