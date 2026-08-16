"""Persistent watchlist operations and live-data presentation helpers."""

from __future__ import annotations

from sqlalchemy import select

from api.coins import coin_name
from api.types import PriceQuote
from database import get_session
from database.models import Watchlist


def list_watchlist(user_id: int) -> list[Watchlist]:
    """Return a user's watchlist in stable alphabetical order."""
    return list(
        get_session().scalars(
            select(Watchlist)
            .where(Watchlist.user_id == user_id)
            .order_by(Watchlist.coin)
        )
    )


def add_to_watchlist(user_id: int, coin: str) -> tuple[Watchlist, bool]:
    """Persist a coin once and report whether it was newly added."""
    normalized_coin = coin.strip().upper()
    session = get_session()
    existing = session.scalar(
        select(Watchlist).where(
            Watchlist.user_id == user_id,
            Watchlist.coin == normalized_coin,
        )
    )
    if existing:
        return existing, False

    item = Watchlist(user_id=user_id, coin=normalized_coin)
    session.add(item)
    session.commit()
    return item, True


def remove_from_watchlist(user_id: int, item_id: int) -> bool:
    """Remove only a watchlist item owned by the active user."""
    session = get_session()
    item = session.scalar(
        select(Watchlist).where(Watchlist.id == item_id, Watchlist.user_id == user_id)
    )
    if item is None:
        return False
    session.delete(item)
    session.commit()
    return True


def build_watchlist_rows(
    items: list[Watchlist],
    prices_by_exchange: dict[str, dict[str, PriceQuote]],
) -> list[dict[str, str]]:
    """Format persisted watchlist coins with their current live market quote."""
    rows: list[dict[str, str]] = []
    for item in items:
        quotes = [
            exchange_prices[item.coin]
            for exchange_prices in prices_by_exchange.values()
            if item.coin in exchange_prices
        ]
        if not quotes:
            rows.append(
                {
                    "Coin": item.coin,
                    "Name": coin_name(item.coin),
                    "Current price": "Unavailable",
                    "24h change": "Unavailable",
                    "24h volume": "Unavailable",
                    "Sources": "No live source",
                }
            )
            continue

        primary = next((quote for quote in quotes if quote.change_24h is not None), quotes[0])
        volume = (
            _format_usd(primary.volume_24h)
            if primary.volume_24h is not None
            else "n/a"
        )
        rows.append(
            {
                "Coin": item.coin,
                "Name": coin_name(item.coin),
                "Current price": _format_usd(primary.price_usd),
                "24h change": primary.formatted_change,
                "24h volume": volume,
                "Sources": ", ".join(quote.exchange for quote in quotes),
            }
        )
    return rows


def _format_usd(value: float) -> str:
    """Format a price or volume value for a concise watchlist table."""
    return f"${value:,.6f}" if abs(value) < 1 else f"${value:,.2f}"
