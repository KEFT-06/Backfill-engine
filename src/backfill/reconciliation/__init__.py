"""🔑 Reconciliation — the proof.

"Zero duplicates, zero gaps" is proven, not claimed. Every discrepancy between
the old logic and the new one must be explained; an unexplained gap is a bug.

Planned modules (Phase 6):
    counts.py     source vs target row counts, per partition
    checksums.py  deterministic per-partition checksums
    overlap.py    old logic vs new logic on shared partitions
    report.py     the auto-generated, numbers-first report
"""
