"""Base helpers for cryptocurrency API clients."""

from __future__ import annotations

import logging
from time import monotonic
from typing import Any

import requests


LOGGER = logging.getLogger(__name__)


class APIClientError(RuntimeError):
    """Raised when an external market API request fails."""


class TTLCache:
    """Small in-memory TTL cache for rate-limited market API responses."""

    def __init__(self, ttl_seconds: int) -> None:
        self.ttl_seconds = ttl_seconds
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        """Return a cached value when it has not expired."""
        cached = self._store.get(key)
        if not cached:
            return None

        expires_at, value = cached
        if expires_at < monotonic():
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        """Store a value until the configured TTL expires."""
        self._store[key] = (monotonic() + self.ttl_seconds, value)


class BaseAPIClient:
    """Shared JSON request logic for external API clients."""

    def __init__(
        self,
        base_url: str,
        timeout_seconds: int,
        cache_ttl_seconds: int,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.cache = TTLCache(cache_ttl_seconds)
        self.session = requests.Session()

    def get_json(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """GET JSON from an external API with basic caching and errors."""
        params = params or {}
        cache_key = self._cache_key(path, params)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        url = f"{self.base_url}{path}"
        try:
            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            LOGGER.warning("Market API request failed for %s: %s", url, exc)
            raise APIClientError(f"Could not fetch market data from {url}") from exc
        except ValueError as exc:
            LOGGER.warning("Market API returned invalid JSON for %s", url)
            raise APIClientError(f"Invalid JSON returned by {url}") from exc

        self.cache.set(cache_key, payload)
        return payload

    @staticmethod
    def _cache_key(path: str, params: dict[str, Any]) -> str:
        """Build a deterministic cache key for a request."""
        parts = [f"{key}={params[key]}" for key in sorted(params)]
        return f"{path}?{'&'.join(parts)}"
