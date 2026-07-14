"""Common parser interface.

Every era parser turns a raw GH Archive file into the SAME canonical columns, so the
output contract is stable no matter which era the input came from. A parser is just a
named SQL template with a ``{raw}`` placeholder that SELECTs the output columns from
``read_json_auto('{raw}')``.
"""

from __future__ import annotations

from dataclasses import dataclass

# The stable output contract — same columns, same types, every era.
# `id` is TEXT (not BIGINT) on purpose: the old era has no event id, so we synthesise
# a hash there — and the column type must stay identical across eras.
OUTPUT_COLUMNS = ("id", "event_type", "actor_login", "repo_name", "created_at")


@dataclass(frozen=True)
class Parser:
    name: str
    sql_template: str

    def sql(self, raw_path: str) -> str:
        """The SQL SELECT for one raw file."""
        return self.sql_template.format(raw=raw_path)
