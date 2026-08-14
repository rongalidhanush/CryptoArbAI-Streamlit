"""Portfolio validation and valuation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from statistics import mean

from database.models import Portfolio


@dataclass(frozen=True)
class PortfolioSummary:
    """Aggregated portfolio valuation details."""

    total_value_usd: Decimal
    total_cost_usd: Decimal
    profit_loss_usd: Decimal
    profit_loss_percent: Decimal


def parse_positive_decimal(value: str, field_name: str) -> Decimal:
    """Parse and validate a positive decimal form value."""
    try:
        parsed = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be a valid number.") from exc

    if parsed <= 0:
        raise ValueError(f"{field_name} must be greater than zero.")
    return parsed


def normalize_coin_symbol(symbol: str) -> str:
    """Normalize user-entered coin symbols."""
    return symbol.strip().upper()


def current_prices_for_holdings(holdings: list[Portfolio]) -> dict[str, Decimal]:
    """Return average live USD prices for the user's holding symbols."""
    symbols = sorted({holding.coin for holding in holdings})
    if not symbols:
        return {}

    from api.market_data import fetch_exchange_prices

    prices_by_exchange = fetch_exchange_prices(symbols)
    prices: dict[str, Decimal] = {}
    for symbol in symbols:
        quotes = [
            quote.price_usd
            for exchange_prices in prices_by_exchange.values()
            if (quote := exchange_prices.get(symbol))
        ]
        if quotes:
            prices[symbol] = Decimal(str(mean(quotes)))
    return prices


def build_holding_rows(
    holdings: list[Portfolio],
    current_prices: dict[str, Decimal],
) -> tuple[list[dict[str, str]], PortfolioSummary]:
    """Build template-ready holding rows and portfolio totals."""
    rows: list[dict[str, str]] = []
    total_value = Decimal("0")
    total_cost = Decimal("0")

    for holding in holdings:
        quantity = Decimal(holding.quantity)
        buy_price = Decimal(holding.buy_price)
        current_price = current_prices.get(holding.coin, buy_price)
        cost = quantity * buy_price
        value = quantity * current_price
        profit_loss = value - cost
        total_value += value
        total_cost += cost

        rows.append(
            {
                "id": str(holding.id),
                "coin": holding.coin,
                "quantity": _format_decimal(quantity),
                "buy_price": _format_usd(buy_price),
                "current_price": _format_usd(current_price),
                "value": _format_usd(value),
                "profit_loss": _format_usd(profit_loss),
                "tone": "positive" if profit_loss >= 0 else "negative",
            }
        )

    total_profit_loss = total_value - total_cost
    profit_percent = (
        (total_profit_loss / total_cost) * Decimal("100")
        if total_cost
        else Decimal("0")
    )
    return rows, PortfolioSummary(
        total_value_usd=total_value,
        total_cost_usd=total_cost,
        profit_loss_usd=total_profit_loss,
        profit_loss_percent=profit_percent,
    )


def format_summary(summary: PortfolioSummary) -> dict[str, str]:
    """Return a template-ready portfolio summary."""
    return {
        "total_value": _format_usd(summary.total_value_usd),
        "total_cost": _format_usd(summary.total_cost_usd),
        "profit_loss": _format_usd(summary.profit_loss_usd),
        "profit_loss_percent": f"{summary.profit_loss_percent:.2f}%",
        "tone": "positive" if summary.profit_loss_usd >= 0 else "negative",
    }


def _format_usd(value: Decimal) -> str:
    """Format a decimal value as USD."""
    return f"${value:,.2f}"


def _format_decimal(value: Decimal) -> str:
    """Format a decimal quantity without unnecessary trailing zeros."""
    return f"{value.normalize():f}"
