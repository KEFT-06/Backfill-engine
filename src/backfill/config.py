"""Typed configuration — the single source of truth for all runtime settings.

Every value is read from the environment (prefix ``BACKFILL_``) or from a local
``.env`` file. Nothing in the codebase should read ``os.environ`` directly.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="BACKFILL_",
        env_file=".env",
        extra="ignore",
    )

    # --- Ledger (PostgreSQL) ---
    pg_dsn: str = "postgresql://backfill:backfill@localhost:5432/backfill"

    # --- Object store (MinIO / S3) ---
    s3_endpoint: str = "localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "backfill"
    s3_secure: bool = False

    # --- Runner ---
    max_concurrency: int = 4
    max_attempts: int = 5

    # --- Source ---
    gharchive_base_url: str = "https://data.gharchive.org"


def get_settings() -> Settings:
    """Load settings once, at process start."""
    return Settings()
