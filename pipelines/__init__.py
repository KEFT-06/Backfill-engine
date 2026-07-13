"""Dagster pipeline definitions — PLUMBING, added in Phase 5.

Per ADR 003, Dagster is deliberately NOT introduced yet. We first build and prove
the ledger-driven runner ourselves, then wrap it here.

Planned modules (Phase 5):
    hot_path.py  the daily job — touches ONLY yesterday's partition
    backfill.py  the history job — touches ONLY the past
    assets.py    partitioned assets
"""
