# Backfill-engine
Reprocessing 10 years of event history without breaking production — an idempotent, resumable backfill system with reconciliation proofs.
# Large-Scale Backfill

Reprocessing 10 years of GitHub event history — 130,000 hourly partitions,
X billion rows — while the daily production pipeline keeps running.

Zero duplicates. Zero gaps. Proven, not claimed.

## The problem

A transformation bug ships. It has been corrupting a metric for two years.
Fixing the code is the easy part — reprocessing the history is not:

- The daily pipeline cannot stop while history is rewritten.
- Reruns must be idempotent, or you double-count.
- The job will die halfway. It has to resume, not restart.
- Some partitions are corrupt and will never succeed. The backfill
  must survive them, not halt on them.
- The schema drifted over 10 years. Old data does not look like new data.
- And at the end, you have to prove the result is correct.

This repository is that problem, solved end to end.

## Results

| | |
|---|---|
| Partitions processed | X |
| Rows written | X |
| Total runtime | X h |
| Estimated cost | X € |
| Partitions quarantined | X |
| Production downtime | 0 |
| Reconciliation discrepancies | X, all explained |

## What broke

[Le lien vers docs/incidents.md — et cette section est celle
que les lecteurs expérimentés ouvriront en premier.]
