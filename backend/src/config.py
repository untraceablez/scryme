"""Application settings, loaded from environment variables.

Single-user deployment: there is one implicit collection per running instance, so
there is no authentication or per-user configuration here.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from src import __version__


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SCRYME_", env_file=".env", extra="ignore")

    environment: str = "development"
    debug: bool = False

    # PostgreSQL (async driver). Override via SCRYME_DATABASE_URL.
    database_url: str = "postgresql+asyncpg://scryme:scryme@localhost:5432/scryme"

    # Where downloaded Scryfall bulk files and cached card images live on disk.
    data_dir: Path = Path("/data")
    image_cache_dir: Path = Path("/data/images")

    # Scryfall good-citizenship settings (see https://scryfall.com/docs/api).
    # User-Agent MUST identify this app; Accept MUST be set. Keep < 10 req/s.
    scryfall_api_base: str = "https://api.scryfall.com"
    scryfall_user_agent: str = f"scryme/{__version__} (+https://github.com/untraceablez/scryme)"
    scryfall_accept: str = "application/json;q=0.9,*/*;q=0.8"
    scryfall_min_request_interval: float = 0.1  # seconds between requests (<= 10/s)
    # Don't re-download bulk data more often than this many hours (Scryfall asks >= 24h cache).
    bulk_refresh_min_hours: int = 24

    # Read-only demo mode disables uploads/mutations (used by the public sandbox).
    read_only: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
