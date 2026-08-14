"""Environment-based configuration for the Streamlit application."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _database_url() -> str:
    """Return a deployment-safe database URL."""
    configured_url = os.getenv("DATABASE_URL")
    if configured_url:
        return configured_url.replace("postgres://", "postgresql://", 1)
    database_path = BASE_DIR / "database" / "database.db"
    return f"sqlite:///{database_path.as_posix()}"


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from local environment variables or secrets."""

    database_url: str
    gemini_api_key: str
    gemini_model: str
    gemini_base_url: str
    coingecko_base_url: str
    binance_base_url: str
    coincap_base_url: str
    kraken_base_url: str
    api_timeout_seconds: int
    market_cache_ttl_seconds: int
    market_refresh_interval_seconds: int
    news_feeds: tuple[str, ...]
    news_timeout_seconds: int


def load_streamlit_secrets() -> None:
    """Make Streamlit secrets available to existing environment-based services."""
    try:
        import streamlit as st

        for key, value in st.secrets.items():
            if isinstance(value, (str, int, float, bool)) and key not in os.environ:
                os.environ[key] = str(value)
    except (FileNotFoundError, RuntimeError, KeyError):
        # Local CLI tools and tests do not have a Streamlit secrets context.
        return


def get_settings() -> Settings:
    """Build immutable settings from the current environment."""
    feeds = tuple(
        feed.strip()
        for feed in os.getenv(
            "NEWS_FEEDS",
            "https://www.coindesk.com/arc/outboundfeeds/rss/,"
            "https://cointelegraph.com/rss",
        ).split(",")
        if feed.strip()
    )
    return Settings(
        database_url=_database_url(),
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
        gemini_base_url=os.getenv(
            "GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"
        ),
        coingecko_base_url=os.getenv(
            "COINGECKO_BASE_URL", "https://api.coingecko.com/api/v3"
        ),
        binance_base_url=os.getenv("BINANCE_BASE_URL", "https://api.binance.com"),
        coincap_base_url=os.getenv("COINCAP_BASE_URL", "https://api.coincap.io/v2"),
        kraken_base_url=os.getenv("KRAKEN_BASE_URL", "https://api.kraken.com"),
        api_timeout_seconds=int(os.getenv("API_TIMEOUT_SECONDS", "8")),
        market_cache_ttl_seconds=int(os.getenv("MARKET_CACHE_TTL_SECONDS", "30")),
        market_refresh_interval_seconds=int(
            os.getenv("MARKET_REFRESH_INTERVAL_SECONDS", "30")
        ),
        news_feeds=feeds,
        news_timeout_seconds=int(os.getenv("NEWS_TIMEOUT_SECONDS", "8")),
    )
