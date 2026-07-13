"""Ledger repository — transactional claim / commit of partitions.

🔑 STUB — the core of the whole project. You write claim_next() in Phase 2.

The critical race: N workers pull work at the same time and must NEVER grab the
same partition. The one-line idea is:

    SELECT ... FROM ledger WHERE status = 'pending'
    ORDER BY partition_key
    FOR UPDATE SKIP LOCKED
    LIMIT 1;

...but the interview lives in the details: what happens on commit, on crash
between claim and commit, on retry, on quarantine. Design it yourself first.
"""

from __future__ import annotations
