"""Smoke test so the CI pipeline is green from Phase 0."""

from __future__ import annotations

from backfill.config import Settings, get_settings


def test_defaults_are_typed() -> None:
    s = Settings()
    assert s.max_attempts >= 1
    assert s.max_concurrency >= 1
    assert s.gharchive_base_url.startswith("https://")


def test_get_settings_returns_settings() -> None:
    assert isinstance(get_settings(), Settings)
