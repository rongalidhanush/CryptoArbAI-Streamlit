"""Kraken API client for live cryptocurrency prices."""

from __future__ import annotations

from datetime import datetime, timezone

from api.base import APIClientError, BaseAPIClient
from api.coins import COINS_BY_SYMBOL
from api.types import PriceQuote


KRAKEN_USD_PAIRS = {
    symbol: coin.kraken_pair
    for symbol, coin in COINS_BY_SYMBOL.items()
    if coin.kraken_pair
}


class KrakenClient(BaseAPIClient):
    """Client for Kraken public ticker endpoints."""

    exchange_name = "Kraken"

    def get_prices(self, symbols: list[str]) -> dict[str, PriceQuote]:
        """Fetch live USD prices for supported symbols."""
        requested = [symbol.upper() for symbol in symbols if symbol.upper() in KRAKEN_USD_PAIRS]
        if not requested:
            return {}

        fetched_at = datetime.now(timezone.utc)
        quotes: dict[str, PriceQuote] = {}

        for symbol in requested:
            pair = KRAKEN_USD_PAIRS[symbol]
            payload = self.get_json("/0/public/Ticker", {"pair": pair})
            errors = payload.get("error", [])
            if errors:
                continue

            data = payload.get("result", {})
            if not isinstance(data, dict):
                continue

            item = next(iter(data.values()), {})
            ticker = item.get("c", [])
            if not ticker:
                continue
            quotes[symbol] = PriceQuote(
                symbol=symbol,
                exchange=self.exchange_name,
                price_usd=float(ticker[0]),
                fetched_at=fetched_at,
            )

        if not quotes:
            raise APIClientError("Kraken returned no supported price data.")
        return quotes
