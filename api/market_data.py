"""Market data aggregation service for dashboard and future engines."""

from __future__ import annotations

import logging
from statistics import mean

from api.base import APIClientError, BaseAPIClient
from api.binance import BinanceClient
from api.coincap import CoinCapClient
from api.coingecko import CoinGeckoClient
from api.coins import coin_name, supported_symbols
from api.kraken import KrakenClient
from api.types import HistoricalPrice, PriceQuote
from config import get_settings


LOGGER = logging.getLogger(__name__)

SUPPORTED_COINS = supported_symbols()
_CLIENTS: list[BaseAPIClient] | None = None
_CLIENT_CONFIG_KEY: tuple[object, ...] | None = None


def fetch_exchange_prices(
    symbols: list[str] | None = None,
) -> dict[str, dict[str, PriceQuote]]:
    """Fetch live prices grouped by exchange name."""
    requested_symbols = symbols or SUPPORTED_COINS
    clients = _get_clients()

    prices_by_exchange: dict[str, dict[str, PriceQuote]] = {}
    for client in clients:
        try:
            prices_by_exchange[client.exchange_name] = client.get_prices(requested_symbols)
        except APIClientError as exc:
            LOGGER.info("%s price fetch skipped: %s", client.exchange_name, exc)

    return prices_by_exchange


def fetch_historical_prices(
    symbol: str,
    days: int = 30,
) -> tuple[list[HistoricalPrice], str]:
    """Return live timestamped prices using CoinGecko then Binance as backup.

    CoinGecko remains the preferred source because it supplies a 30-day market
    chart. Binance k-lines provide a compatible live fallback when CoinGecko is
    rate-limited or temporarily unavailable.
    """
    clients = _get_clients()
    history_errors: list[str] = []
    for client in clients:
        if isinstance(client, CoinGeckoClient):
            try:
                return client.get_historical_points(symbol, days=days), client.exchange_name
            except APIClientError as exc:
                history_errors.append(f"{client.exchange_name}: {exc}")
        elif isinstance(client, BinanceClient):
            try:
                return client.get_historical_points(symbol, limit=days * 24), client.exchange_name
            except APIClientError as exc:
                history_errors.append(f"{client.exchange_name}: {exc}")

    detail = "; ".join(history_errors) or "No historical-data client is configured."
    raise APIClientError(f"Historical live data is unavailable for {symbol}. {detail}")


def _get_clients() -> list[BaseAPIClient]:
    """Return API clients, preserving their caches across requests."""
    global _CLIENTS, _CLIENT_CONFIG_KEY

    settings = get_settings()
    config_key = (
        settings.coingecko_base_url,
        settings.binance_base_url,
        settings.coincap_base_url,
        settings.kraken_base_url,
        settings.api_timeout_seconds,
        settings.market_cache_ttl_seconds,
    )
    if _CLIENTS is not None and _CLIENT_CONFIG_KEY == config_key:
        return _CLIENTS

    timeout = settings.api_timeout_seconds
    optional_timeout = min(timeout, 3)
    cache_ttl = settings.market_cache_ttl_seconds
    _CLIENTS = [
        CoinGeckoClient(settings.coingecko_base_url, timeout, cache_ttl),
        BinanceClient(settings.binance_base_url, timeout, cache_ttl),
        CoinCapClient(settings.coincap_base_url, timeout, cache_ttl),
        KrakenClient(settings.kraken_base_url, optional_timeout, cache_ttl),
    ]
    _CLIENT_CONFIG_KEY = config_key
    return _CLIENTS


def build_market_snapshot(
    symbols: list[str] | None = None,
) -> tuple[list[dict[str, str]], dict[str, str]]:
    """Build dashboard cards from live prices with graceful fallback metadata."""
    requested_symbols = symbols or SUPPORTED_COINS
    prices_by_exchange = fetch_exchange_prices(requested_symbols)
    rows: list[dict[str, str]] = []

    for symbol in requested_symbols:
        quotes = [
            exchange_prices[symbol]
            for exchange_prices in prices_by_exchange.values()
            if symbol in exchange_prices
        ]
        if not quotes:
            continue

        primary_quote = _choose_primary_quote(quotes)
        rows.append(
            {
                "symbol": symbol,
                "name": coin_name(symbol),
                "price": primary_quote.formatted_price,
                "change": primary_quote.formatted_change,
                "tone": primary_quote.tone,
                "exchange": primary_quote.exchange,
                "average_price": _format_price(mean(quote.price_usd for quote in quotes)),
            }
        )

    status = {
        "source_count": str(len(prices_by_exchange)),
        "source_label": ", ".join(prices_by_exchange) or "No live source",
        "mode": "Live" if rows else "Fallback",
    }
    return rows, status


def _choose_primary_quote(quotes: list[PriceQuote]) -> PriceQuote:
    """Prefer quotes that include 24-hour movement data for dashboard cards."""
    return next((quote for quote in quotes if quote.change_24h is not None), quotes[0])


def _format_price(price: float) -> str:
    """Format a USD price for display."""
    if price >= 1:
        return f"${price:,.2f}"
    return f"${price:,.6f}"
