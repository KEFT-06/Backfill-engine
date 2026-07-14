"""Phase 4 — empirically DISCOVER the schema eras of GH Archive.

Sample one hour per year, compute a compact schema signature, and report where the
signature changes. Eras are DISCOVERED from the data, never assumed. The output
feeds docs/schema-eras.md and answers the real question: does our whitelist
(id, type, actor.login, repo.name, created_at) hold across the years, or do we
actually need versioned parsers?

Run:  uv run python scripts/discover_schema_eras.py
"""

from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path

import duckdb

from backfill.sources import gharchive

YEARS = [2011, 2012, 2013, 2014, 2015, 2016, 2018, 2020, 2022, 2024]

WHITELIST = (
    "id::BIGINT AS id, type AS event_type, actor.login AS actor_login, "
    "repo.name AS repo_name, created_at AS created_at"
)


def _whitelist_works(f: str) -> str:
    try:
        duckdb.sql(f"SELECT {WHITELIST} FROM read_json_auto('{f}') LIMIT 1").fetchone()
    except Exception as exc:
        return f"CASSE: {str(exc).splitlines()[0][:60]}"
    return "OK"


def _actor_type(f: str) -> str:
    row = duckdb.sql(f"SELECT typeof(actor) FROM read_json_auto('{f}') LIMIT 1").fetchone()
    return str(row[0])[:48] if row else "?"


def signature(path: Path) -> dict[str, str]:
    f = path.as_posix()
    cols = [r[0] for r in duckdb.sql(f"DESCRIBE SELECT * FROM read_json_auto('{f}')").fetchall()]
    return {
        "columns": ",".join(sorted(cols)),
        "actor_type": _actor_type(f),
        "whitelist": _whitelist_works(f),
    }


def _download_with_retry(hour: datetime, work: Path, tries: int = 3) -> Path:
    last: Exception | None = None
    for _ in range(tries):
        try:
            return gharchive.download(hour, work)
        except Exception as exc:  # noqa: BLE001 — flaky network, retry
            last = exc
    raise last if last else RuntimeError("download failed")


def main() -> None:
    results: list[tuple[int, dict[str, str]]] = []
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        for year in YEARS:
            hour = datetime(year, 6, 15, 12)
            try:
                path = _download_with_retry(hour, work)
                sig = signature(path)
                path.unlink(missing_ok=True)
            except Exception as exc:
                sig = {"columns": "?", "actor_type": "?", "whitelist": f"INDISPO: {exc}"[:50]}
            results.append((year, sig))
            print(f"{year}: whitelist={sig['whitelist']:<14} actor={sig['actor_type']}")

    print("\n=== Époques (regroupement par signature de colonnes) ===")
    prev: str | None = None
    for year, sig in results:
        if sig["columns"] != prev:
            print(f"--- bascule de signature à {year} ---")
            print(f"    colonnes : {sig['columns']}")
            prev = sig["columns"]
        print(f"    {year}: whitelist {sig['whitelist']}")


if __name__ == "__main__":
    main()
