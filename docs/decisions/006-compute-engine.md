# ADR 006 — Compute engine: DuckDB

- **Status:** Accepted
- **Date:** 2026-07-12

## Context

The backfill needs a single-node engine (no Spark, ADR 002) to read nested GH
Archive JSON, aggregate, and write Parquet — on a 16 GB / <256 GB machine, by an
author whose strength is SQL and whose time budget is 5-10 h/week. Candidates:
DuckDB vs Polars.

## Decision

**DuckDB.**

## Rationale (the interview answer)

Speed is explicitly *not* the argument (Polars often wins raw benchmarks).

- **Machine fit.** DuckDB is out-of-core: it spills to disk when RAM saturates, so
  16 GB is not a wall. (Caveat acknowledged: Polars can also stream larger-than-RAM
  — so this alone doesn't decide it.)
- **Time goes to logic, not tooling.** Transformations are written in SQL, already
  mastered. With a 5-10 h/week budget, that's decisive: effort lands on the
  business logic, not on learning a new DataFrame API.

## Alternatives considered

- **Polars.** Excellent and fast, but the DataFrame API is a new thing to learn on
  top of everything else; it would move limited time from the problem to the tool.
  Rejected for this author/profile, not on technical merit.
