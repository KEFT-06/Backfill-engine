"""The schema history is non-linear, so routing is a date RANGE, not a single cutoff."""

from __future__ import annotations

from datetime import datetime

from backfill.parsers import registry


def test_routing_is_a_range_not_a_cutoff() -> None:
    assert registry.parser_for(datetime(2011, 6, 1)).name == "modern"
    assert registry.parser_for(datetime(2012, 1, 1)).name == "era_2012_2014"
    assert registry.parser_for(datetime(2014, 12, 31, 23)).name == "era_2012_2014"
    assert registry.parser_for(datetime(2015, 1, 1)).name == "modern"
    assert registry.parser_for(datetime(2023, 6, 1)).name == "modern"
