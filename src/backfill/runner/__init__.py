"""🔑 Runner — the resume-on-failure loop.

The loop is ledger-driven, never a `for` in a script:
    claim (ledger) → process (source + parser + sink) → commit → update ledger

Planned modules (Phase 2, then hardened in Phase 3):
    worker.py      the claim → process → commit → update loop
    retry.py       exponential backoff, max_attempts
    quarantine.py  poison pill → isolate → the backfill CONTINUES
    throttle.py    concurrency cap, protect production
"""
