"""backfill-hell — idempotent, resumable backfill engine.

Package map (🔑 = the project; the rest is plumbing):
    config        typed settings, single source of truth
    sources/      download + stream GitHub Archive           (plumbing)
    ledger/       🔑 partition registry: claim / commit / resume
    parsers/      🔑 versioned parsers for schema drift
    runner/       🔑 claim → process → commit loop, retry, quarantine, throttle
    sinks/        🔑 atomic partition overwrite + blue/green swap
    reconciliation/ 🔑 counts, checksums, overlap — the proof
    observability/  throughput, failure rate, cost projection
"""
