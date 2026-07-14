"""Old era parser — GH Archive "Timeline API" format (2012-2014).

Discovered empirically, not assumed (scripts/discover_schema_eras.py). In this era:
  - `actor` is a plain STRING (already the login), not a struct.
  - the repo is `repository` (a struct with `name`), not `repo`.
  - there is NO top-level event `id` → we synthesise a DETERMINISTIC hash of the
    event's stable content, so replaying a partition yields the same id (idempotence).
"""

from __future__ import annotations

from backfill.parsers.base import Parser

ERA_2012_2014 = Parser(
    name="era_2012_2014",
    sql_template="""
        SELECT
            md5(
                COALESCE(CAST(created_at AS VARCHAR), '') || '|' ||
                COALESCE(type, '')                        || '|' ||
                COALESCE(actor, '')                       || '|' ||
                COALESCE(url, '')                         || '|' ||
                COALESCE(CAST(repository AS VARCHAR), '')
            )                    AS id,          -- synthetic, deterministic hash
            type                 AS event_type,
            actor                AS actor_login, -- actor IS the login string here
            repository.name      AS repo_name,   -- NULL for repo-less events
            created_at           AS created_at
        FROM read_json_auto('{raw}')
    """,
)
