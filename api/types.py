"""Shared API data types for market price integrations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class PriceQuote:
    """Normalized live price quote from an exchange API."""

    symbol: str
    exchange: str
    price_usd: float
    change_24h: float | None = None
    volume_24h: float | None = None
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def formatted_price(self) -> str:
        """Return a dashboard-friendly USD price string."""
        if self.price_usd >= 1:
            return f"${self.price_usd:,.2f}"
        return f"${self.price_usd:,.6f}"

    @property
    def formatted_change(self) -> str:
        """Return a dashboard-friendly 24-hour change string."""
        if self.change_24h is None:
            return "n/a"
        sign = "+" if self.change_24h >= 0 else ""
        return f"{sign}{self.change_24h:.2f}%"

    @property
    def tone(self) -> str:
        """Return the visual tone for the quote movement."""
        if self.change_24h is None or self.change_24h >= 0:
            return "positive"
        return "negative"


@dataclass(frozen=True)
class HistoricalPrice:
    """A timestamped live historical closing price."""

    timestamp: datetime
    price_usd: float
