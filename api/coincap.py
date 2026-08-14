"""CoinCap API client for live cryptocurrency prices."""

from __future__ import annotations

from datetime import datetime, timezone

from api.base import APIClientError, BaseAPIClient
from api.coins import COINS_BY_SYMBOL
from api.types import PriceQuote


COINCAP_IDS = {
    symbol: coin.coincap_id for symbol, coin in COINS_BY_SYMBOL.items()
}


class CoinCapClient(BaseAPIClient):
    """Client for CoinCap public asset endpoints."""

    exchange_name = "CoinCap"

    def get_prices(self, symbols: list[str]) -> dict[str, PriceQuote]:
        """Fetch live USD prices for supported symbols."""
        requested = [symbol.upper() for symbol in symbols if symbol.upper() in COINCAP_IDS]
        if not requested:
            return {}

        assets = ",".join(COINCAP_IDS[symbol] for symbol in requested)
        payload = self.get_json("/assets", {"ids": assets})
        data = payload.get("data", [])
        if not isinstance(data, list):
            raise APIClientError("CoinCap returned an unexpected assets payload.")

        id_lookup = {COINCAP_IDS[symbol]: symbol for symbol in requested}
        fetched_at = datetime.now(timezone.utc)
        quotes: dict[str, PriceQuote] = {}

        for item in data:
            asset_id = item.get("id")
            if asset_id not in id_lookup:
                continue
            symbol = id_lookup[asset_id]
            quotes[symbol] = PriceQuote(
                symbol=symbol,
                exchange=self.exchange_name,
                price_usd=float(item["priceUsd"]),
                change_24h=_optional_float(item.get("changePercent24Hr")),
                volume_24h=_optional_float(item.get("volumeUsd24Hr")),
                fetched_at=fetched_at,
            )

        if not quotes:
            raise APIClientError("CoinCap returned no supported price data.")
        return quotes


def _optional_float(value: object) -> float | None:
    """Convert optional API numeric values to float."""
    if value in (None, ""):
        return None
    return float(value)
