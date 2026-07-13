"""Ledger data model.

STUB — you design this in Phase 2. Do NOT let me fill it in.

The prompt hints at the fields (partition_key, status, attempts, rows_written,
checksum, started_at, finished_at, error) but the interesting questions are yours
to answer first:
    - What are the valid states, and which transitions are legal?
      (pending → claimed → done | failed | quarantined ?)
    - What makes claim + commit atomic under concurrency?
    - Where does the checksum come from, and when is it written?
Sketch it, we review, then we write it together.
"""

from __future__ import annotations
