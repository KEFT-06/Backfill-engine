"""🔑 Parsers — the intellectual core: schema drift over the years.

The GH Archive event schema really drifted between 2011 and today. You will
DISCOVER the eras yourself (scripts/discover_schema_eras.py, Phase 4), not guess
them. The era_*.py filenames below are intentionally NOT created yet — their date
boundaries come from your discovery, not from an a-priori assumption.

Planned modules (Phase 4):
    base.py        common parser interface
    registry.py    route a date to the right parser
    era_*.py       one versioned parser per discovered era
"""
