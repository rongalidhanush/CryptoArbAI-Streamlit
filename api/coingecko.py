"""CoinGecko API client for live cryptocurrency prices."""

from __future__ import annotations

from datetime import datetime, timezone

from api.base import APIClientError, BaseAPIClient
from api.coins import COINS_BY_SYMBOL
from api.types import HistoricalPrice, PriceQuote


COINGECKO_IDS = {
    symbol: coin.coingecko_id for symbol, coin in COINS_BY_SYMBOL.items()
}


class CoinGeckoClient(BaseAPIClient):
    """Client for CoinGecko public market data endpoints."""

    exchange_name = "CoinGecko"

    def get_prices(self, symbols: list[str]) -> dict[str, PriceQuote]:
        """Fetch live USD prices for supported symbols."""
        requested = [symbol.upper() for symbol in symbols if symbol.upper() in COINGECKO_IDS]
        if not requested:
            return {}

        ids = [COINGECKO_IDS[symbol] for symbol in requested]
        payload = self.get_json(
            "/simple/price",
            {
                "ids": ",".join(ids),
                "vs_currencies": "usd",
                "include_24hr_change": "true",
                "include_24hr_vol": "true",
            },
        )

        fetched_at = datetime.now(timezone.utc)
        quotes: dict[str, PriceQuote] = {}
        for symbol in requested:
            coin_id = COINGECKO_IDS[symbol]
            coin_data = payload.get(coin_id, {})
            price = coin_data.get("usd")
            if price is None:
                continue
            quotes[symbol] = PriceQuote(
                symbol=symbol,
                exchange=self.exchange_name,
                price_usd=float(price),
                change_24h=_optional_float(coin_data.get("usd_24h_change")),
                volume_24h=_optional_float(coin_data.get("usd_24h_vol")),
                fetched_at=fetched_at,
            )

        if not quotes:
            raise APIClientError("CoinGecko returned no supported price data.")
        return quotes

    def get_historical_points(
        self,
        symbol: str,
        days: int = 30,
    ) -> list[HistoricalPrice]:
        """Fetch timestamped historical USD prices for a supported coin symbol."""
        normalized_symbol = symbol.upper()
        coin_id = COINGECKO_IDS.get(normalized_symbol)
        if not coin_id:
            raise APIClientError(f"Unsupported CoinGecko symbol: {symbol}")

        payload = self.get_json(
            f"/coins/{coin_id}/market_chart",
            {"vs_currency": "usd", "days": days, "interval": "hourly"},
        )
        prices = payload.get("prices", [])
        if not isinstance(prices, list) or not prices:
            raise APIClientError("CoinGecko returned no historical prices.")

        points: list[HistoricalPrice] = []
        for item in prices:
            if not isinstance(item, list) or len(item) < 2:
                continue
            try:
                timestamp = datetime.fromtimestamp(float(item[0]) / 1000, tz=timezone.utc)
                price = float(item[1])
            except (TypeError, ValueError, OSError):
                continue
            if price > 0:
                points.append(HistoricalPrice(timestamp=timestamp, price_usd=price))
        if not points:
            raise APIClientError("CoinGecko returned no valid historical prices.")
        return points

    def get_historical_prices(self, symbol: str, days: int = 30) -> list[float]:
        """Return historical price values for backwards-compatible callers."""
        return [point.price_usd for point in self.get_historical_points(symbol, days)]


def _optional_float(value: object) -> float | None:
    """Convert optional API numeric values to float."""
    if value is None:
        return None
    return float(value)
