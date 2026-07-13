# ADR 005 — Atomic partition swap

- **Status:** Proposed — decided in Phase 2 (mechanism) / Phase 5 (table swap)
- **Date:** _tbd_

## Context

Idempotence requires that writing a partition is an atomic overwrite: never a bare
INSERT. Replaying a partition must yield exactly the same result.

## Options to weigh

- Iceberg / Delta atomic partition overwrite.
- Blue/green table swap for the isolation story (ADR 004).
- `MERGE` semantics.

## Decision

_tbd — anchored on the storage/format choice made when the sink is built._
