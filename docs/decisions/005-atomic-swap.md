# ADR 005 — Atomic partition swap

- **Status:** Accepted
- **Date:** 2026-07-14

## Context

Idempotence requires that writing a partition is an atomic overwrite: never a bare
INSERT, and never a half-written file. Writing Parquet directly to the final path is
NOT atomic — a crash mid-write (which happened for real, see INC-005) leaves a corrupt
partition, and a reader can see a partial file.

## Decision

**Write to a temp file, then `os.replace` over the final path.** `os.replace` is atomic
on the same filesystem: a reader sees either the old complete file or the new complete
file, never a partial one. A crash mid-write leaves only the `.tmp` (cleaned up on the
next attempt); the final partition is never corrupt.

Implemented in `reference.ingest_hour`: `COPY (...) TO events.parquet.tmp` →
`os.replace(tmp, events.parquet)`, with `.tmp` cleanup in `finally`.

## Rationale

- Same principle as a blue/green table swap, applied per partition file.
- Combined with the ledger (`running` → `done`), a replayed partition either fully
  succeeds (new file swapped in) or leaves the previous state intact — the atomic
  building block of idempotence.

## Proof

`atomic_proof.py`: write v1, then simulate a crash *during* the swap (`os.replace`
raises). Result: the final file stays complete and readable, the `.tmp` is cleaned up.

## Alternatives considered

- **Direct `COPY TO` the final path.** Rejected: not crash-safe (corrupt partial file).
- **Iceberg/Delta atomic partition overwrite.** Heavier; the temp-file + rename gives
  the same guarantee for a plain Parquet sink without the table-format machinery.
