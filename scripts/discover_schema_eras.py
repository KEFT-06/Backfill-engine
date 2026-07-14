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


def signature(path: Path) -> dict[str, str]:
    f = path.as_posix()
    cols = [r[0] for r in duckdb.sql(f"DESCRIBE SELECT * FROM read_json_auto('{f}')").fetchall()]
    actor_type = duckdb.sql(f"SELECT typeof(actor) FROM read_json_auto('{f}') LIMIT 1").fetchone()
    is_struct = bool(actor_type) and str(actor_type[0]).startswith("STRUCT")
    return {
        "columns": ",".join(sorted(cols)),
        "actor_struct": "oui" if is_struct else "NON",
        "whitelist": _whitelist_works(f),
    }


def main() -> None:
    results: list[tuple[int, dict[str, str]]] = []
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        for year in YEARS:
            hour = datetime(year, 6, 15, 12)
            try:
                path = gharchive.download(hour, work)
                sig = signature(path)
                path.unlink(missing_ok=True)
            except Exception as exc:
                sig = {"columns": "?", "actor_struct": "?", "whitelist": f"INDISPO: {exc}"[:60]}
            results.append((year, sig))
            print(f"{year}: whitelist={sig['whitelist']:<12} actor_struct={sig['actor_struct']}")

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
