"""make reconcile — print the reconciliation report for the reference output."""

from __future__ import annotations

from pathlib import Path

import psycopg

from backfill.reconciliation import report

DSN = "postgresql://backfill:backfill@localhost:5433/backfill"


def main() -> None:
    with psycopg.connect(DSN) as conn:
        print(report.format_report(report.reconcile(conn, Path("data/reference"))))


if __name__ == "__main__":
    main()
