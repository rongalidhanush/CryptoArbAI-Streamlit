"""Arbitrage opportunity detection engine."""

from __future__ import annotations

from dataclasses import dataclass

from api.types import PriceQuote
from arbitrage.calculator import ProfitBreakdown, calculate_profit
from arbitrage.fees import get_fee_schedule


@dataclass(frozen=True)
class ArbitrageOpportunity:
    """Detected arbitrage opportunity between two exchanges."""

    coin: str
    buy_exchange: str
    sell_exchange: str
    buy_price_usd: float
    sell_price_usd: float
    spread_usd: float
    spread_percent: float
    confidence_score: float
    profit: ProfitBreakdown

    @property
    def is_profitable(self) -> bool:
        """Return whether the opportunity remains profitable after fees."""
        return self.profit.net_profit_usd > 0


def find_opportunities(
    prices_by_exchange: dict[str, dict[str, PriceQuote]],
    quantity: float = 1.0,
) -> list[ArbitrageOpportunity]:
    """Find fee-aware arbitrage opportunities from exchange price quotes."""
    coins = sorted(
        {
            symbol
            for exchange_prices in prices_by_exchange.values()
            for symbol in exchange_prices
        }
    )
    opportunities = [
        opportunity
        for coin in coins
        if (opportunity := _build_opportunity(coin, prices_by_exchange, quantity))
    ]
    return sorted(
        opportunities,
        key=lambda item: item.profit.net_profit_usd,
        reverse=True,
    )


def _build_opportunity(
    coin: str,
    prices_by_exchange: dict[str, dict[str, PriceQuote]],
    quantity: float,
) -> ArbitrageOpportunity | None:
    """Build one opportunity for a coin using min and max exchange prices."""
    quotes = [
        quote
        for exchange_prices in prices_by_exchange.values()
        if (quote := exchange_prices.get(coin))
    ]
    if len(quotes) < 2:
        return None

    buy_quote = min(quotes, key=lambda quote: quote.price_usd)
    sell_quote = max(quotes, key=lambda quote: quote.price_usd)
    if buy_quote.exchange == sell_quote.exchange:
        return None

    spread = sell_quote.price_usd - buy_quote.price_usd
    spread_percent = (spread / buy_quote.price_usd) * 100
    profit = calculate_profit(
        buy_price_usd=buy_quote.price_usd,
        sell_price_usd=sell_quote.price_usd,
        quantity=quantity,
        buy_fee=get_fee_schedule(buy_quote.exchange),
        sell_fee=get_fee_schedule(sell_quote.exchange),
    )

    return ArbitrageOpportunity(
        coin=coin,
        buy_exchange=buy_quote.exchange,
        sell_exchange=sell_quote.exchange,
        buy_price_usd=buy_quote.price_usd,
        sell_price_usd=sell_quote.price_usd,
        spread_usd=spread,
        spread_percent=spread_percent,
        confidence_score=_confidence_score(len(quotes), spread_percent, profit.net_profit_usd),
        profit=profit,
    )


def _confidence_score(
    source_count: int,
    spread_percent: float,
    net_profit_usd: float,
) -> float:
    """Estimate confidence from source count, spread size, and net profit."""
    source_score = min(source_count / 4, 1.0) * 45
    spread_score = min(max(spread_percent, 0) / 2, 1.0) * 35
    profit_score = 20 if net_profit_usd > 0 else 0
    return round(source_score + spread_score + profit_score, 1)
