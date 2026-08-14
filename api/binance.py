"""Binance API client for live cryptocurrency prices."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from api.base import APIClientError, BaseAPIClient
from api.coins import COINS_BY_SYMBOL
from api.types import PriceQuote


BINANCE_USDT_SYMBOLS = {
    symbol: coin.binance_pair
    for symbol, coin in COINS_BY_SYMBOL.items()
    if coin.binance_pair
}


class BinanceClient(BaseAPIClient):
    """Client for Binance spot public ticker endpoints."""

    exchange_name = "Binance"

    def get_prices(self, symbols: list[str]) -> dict[str, PriceQuote]:
        """Fetch live USDT prices for supported symbols."""
        requested = [symbol.upper() for symbol in symbols if symbol.upper() in BINANCE_USDT_SYMBOLS]
        if not requested:
            return {}

        requested_pairs = [BINANCE_USDT_SYMBOLS[symbol] for symbol in requested]
        payload = self.get_json(
            "/api/v3/ticker/price",
            {"symbols": json.dumps(requested_pairs, separators=(",", ":"))},
        )
        if not isinstance(payload, list):
            raise APIClientError("Binance returned an unexpected ticker payload.")

        symbol_lookup = {BINANCE_USDT_SYMBOLS[symbol]: symbol for symbol in requested}
        fetched_at = datetime.now(timezone.utc)
        quotes: dict[str, PriceQuote] = {}

        for item in payload:
            pair = item.get("symbol")
            if pair not in symbol_lookup:
                continue
            symbol = symbol_lookup[pair]
            quotes[symbol] = PriceQuote(
                symbol=symbol,
                exchange=self.exchange_name,
                price_usd=float(item["price"]),
                fetched_at=fetched_at,
            )

        if not quotes:
            raise APIClientError("Binance returned no supported price data.")
        return quotes
