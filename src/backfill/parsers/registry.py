"""Route a partition's date to the right era parser.

The history is non-linear (2011 modern, 2012-2014 old, 2015+ modern), so routing is a
date-RANGE test, not a single cutoff: the old Timeline-API format spans
[2012-01-01, 2015-01-01); everything else (2011 and 2015+) is modern.

NOTE: the 2015-01-01 boundary is well documented (Events API switch). The lower bound
is approximate — confirm it with a denser sweep of discover_schema_eras.py.
"""

from __future__ import annotations

from datetime import datetime

from backfill.parsers.base import Parser
from backfill.parsers.era_2012_2014 import ERA_2012_2014
from backfill.parsers.era_modern import MODERN

_OLD_START = datetime(2012, 1, 1)
_OLD_END = datetime(2015, 1, 1)


def parser_for(hour: datetime) -> Parser:
    """Return the parser whose era contains ``hour``."""
    if _OLD_START <= hour < _OLD_END:
        return ERA_2012_2014
    return MODERN
