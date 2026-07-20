"""Cost projection — rows per euro, and the projected cost of the full backfill.

Single node, no Spark (ADR 002): the dominant cost is wall-clock machine time. Tune the
rate to your environment. This turns "it's cheap" into a defensible number.
"""

from __future__ import annotations

from dataclasses import dataclass

_EURO_PER_HOUR = 0.05  # a modest commodity node; adjust to your infra


@dataclass
class CostEstimate:
    partitions: int
    rows: int
    seconds: float

    @property
    def euros(self) -> float:
        return self.seconds / 3600 * _EURO_PER_HOUR

    @property
    def rows_per_euro(self) -> float:
        return self.rows / self.euros if self.euros else float("inf")


def project_full_backfill(measured: CostEstimate, total_partitions: int) -> CostEstimate:
    """Scale a measured sample linearly up to the whole history."""
    if measured.partitions == 0:
        return CostEstimate(total_partitions, 0, 0.0)
    factor = total_partitions / measured.partitions
    return CostEstimate(total_partitions, int(measured.rows * factor), measured.seconds * factor)
