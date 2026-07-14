"""🔑 Parsers — the intellectual core: schema drift over the years.

The eras here were DISCOVERED empirically (scripts/discover_schema_eras.py), not
guessed. The GH Archive event schema is non-linear: 2011 is in the modern format,
2012-2014 is the old "Timeline API" format (actor is a plain string, `repository`
not `repo`, no event id), and 2015+ is modern again.

Modules:
    base.py            Parser interface + the stable output contract (5 columns)
    era_modern.py      2011 + 2015-onward ("Events API")
    era_2012_2014.py   the old era (synthesises a deterministic id hash)
    registry.py        route a date to the right parser (range test, not a cutoff)
"""
