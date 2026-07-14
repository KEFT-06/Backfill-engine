"""Modern era parser — GH Archive "Events API" format.

Covers 2011 AND 2015-onward (the history is non-linear: 2011 was reconstructed in the
modern format). `actor` and `repo` are structs; there is a real top-level event `id`.
"""

from __future__ import annotations

from backfill.parsers.base import Parser

MODERN = Parser(
    name="modern",
    sql_template="""
        SELECT
            CAST(id AS VARCHAR)  AS id,          -- real event id, as TEXT (stable contract)
            type                 AS event_type,
            actor.login          AS actor_login, -- actor is a struct here
            repo.name            AS repo_name,
            created_at           AS created_at
        FROM read_json_auto('{raw}')
    """,
)
