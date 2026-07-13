# ADR 003 — Runner first, Dagster later

- **Status:** Accepted
- **Date:** 2026-07-12

## Context

The prompt suggests Dagster (partitions + backfill are native to it). But the
intellectual core of this project — claim a partition, commit, update the ledger,
`SKIP LOCKED` so two workers never grab the same one — is something we must build
and *prove* ourselves. Introducing Dagster on day one would hide that mechanism
behind an abstraction.

## Decision

**Build a hand-written, ledger-driven runner first (Phase 2) and prove it resumes
with zero gaps / zero duplicates. Wrap it in Dagster only in Phase 5.** The order
is the argument.

## Rationale (the interview answer)

- The resume mechanism is *mine* to write, so I can explain it at a whiteboard —
  not "Dagster does it for me."
- Once the mechanism is built and proven, wrapping it in Dagster is easy, and
  Dagster then earns its place: scheduling and the backfill UI.
- Avoids burning limited time learning an orchestrator at the worst moment
  (project start), keeping effort on `ledger/` + `runner/`.

## Alternatives considered

- **Dagster from the start.** Rejected: learning curve up front, and the core
  mechanism becomes a black box I didn't build.
- **No Dagster at all.** Rejected: loses scheduling + the backfill UI, and a
  résumé line, for little gain once the runner already exists.

## Note on ADR numbering

This decision was taken during scoping, before the Phase 5 isolation decisions,
so it takes number 003. Isolation strategy and atomic swap become 004 / 005.
