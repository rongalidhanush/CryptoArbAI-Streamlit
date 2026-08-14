"""Exchange fee definitions and calculations."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeeSchedule:
    """Trading and transfer fee assumptions for an exchange."""

    trading_fee_rate: float
    withdrawal_fee_usd: float
    network_fee_usd: float


DEFAULT_FEE_SCHEDULES = {
    "CoinGecko": FeeSchedule(0.0010, 1.50, 0.75),
    "Binance": FeeSchedule(0.0010, 1.25, 0.75),
    "CoinCap": FeeSchedule(0.0015, 1.75, 0.75),
    "Kraken": FeeSchedule(0.0016, 2.00, 0.75),
}

DEFAULT_FEE_SCHEDULE = FeeSchedule(0.0015, 2.00, 0.75)


def get_fee_schedule(exchange: str) -> FeeSchedule:
    """Return configured fee assumptions for an exchange."""
    return DEFAULT_FEE_SCHEDULES.get(exchange, DEFAULT_FEE_SCHEDULE)
