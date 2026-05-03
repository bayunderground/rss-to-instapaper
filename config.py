from __future__ import annotations

import os
from dataclasses import dataclass


from dotenv import load_dotenv
load_dotenv()

def _env(name: str, default: str | None = None, required: bool = True) -> str:
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value or ""


def _env_int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


def _env_float(name: str, default: float) -> float:
    return float(os.getenv(name, str(default)))


@dataclass(frozen=True)
class Settings:
    database_url: str
    instapaper_username: str
    instapaper_password: str
    feed_fetch_timeout_seconds: int = 20
    instapaper_timeout_seconds: int = 30
    instapaper_retry_attempts: int = 4
    instapaper_retry_base_delay_seconds: float = 1.5
    instapaper_retry_max_delay_seconds: float = 20.0
    stale_pending_retry_after_seconds: int = 7200  # 2 hours


def load_settings() -> Settings:
    return Settings(
        database_url=_env("DATABASE_URL"),
        instapaper_username=_env("INSTAPAPER_USERNAME"),
        instapaper_password=_env("INSTAPAPER_PASSWORD"),
        feed_fetch_timeout_seconds=_env_int("FEED_FETCH_TIMEOUT_SECONDS", 20),
        instapaper_timeout_seconds=_env_int("INSTAPAPER_TIMEOUT_SECONDS", 30),
        instapaper_retry_attempts=_env_int("INSTAPAPER_RETRY_ATTEMPTS", 4),
        instapaper_retry_base_delay_seconds=_env_float("INSTAPAPER_RETRY_BASE_DELAY", 1.5),
        instapaper_retry_max_delay_seconds=_env_float("INSTAPAPER_RETRY_MAX_DELAY", 20.0),
        stale_pending_retry_after_seconds=_env_int("STALE_PENDING_RETRY_AFTER_SECONDS", 7200),
    )