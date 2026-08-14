"""Profit calculation utilities for arbitrage opportunities."""

from __future__ import annotations

from dataclasses import dataclass

from arbitrage.fees import FeeSchedule


@dataclass(frozen=True)
class ProfitBreakdown:
    """Fee-aware profit details for an arbitrage trade."""

    gross_profit_usd: float
    trading_fee_usd: float
    withdrawal_fee_usd: float
    network_fee_usd: float
    total_fees_usd: float
    net_profit_usd: float
    profit_percent: float


def calculate_profit(
    buy_price_usd: float,
    sell_price_usd: float,
    quantity: float,
    buy_fee: FeeSchedule,
    sell_fee: FeeSchedule,
) -> ProfitBreakdown:
    """Calculate gross profit, fees, and net profit for an opportunity."""
    buy_value = buy_price_usd * quantity
    sell_value = sell_price_usd * quantity
    gross_profit = sell_value - buy_value
    trading_fee = (buy_value * buy_fee.trading_fee_rate) + (
        sell_value * sell_fee.trading_fee_rate
    )
    withdrawal_fee = buy_fee.withdrawal_fee_usd
    network_fee = buy_fee.network_fee_usd
    total_fees = trading_fee + withdrawal_fee + network_fee
    net_profit = gross_profit - total_fees
    profit_percent = (net_profit / buy_value) * 100 if buy_value else 0.0

    return ProfitBreakdown(
        gross_profit_usd=gross_profit,
        trading_fee_usd=trading_fee,
        withdrawal_fee_usd=withdrawal_fee,
        network_fee_usd=network_fee,
        total_fees_usd=total_fees,
        net_profit_usd=net_profit,
        profit_percent=profit_percent,
    )
