"""Prepare chart data for Streamlit without browser-side chart code."""

from __future__ import annotations

from datetime import datetime
from statistics import mean

import pandas as pd

from api.types import HistoricalPrice, PriceQuote


def market_price_frame(
    prices_by_exchange: dict[str, dict[str, PriceQuote]],
    symbols: list[str],
) -> pd.DataFrame:
    """Return average live prices indexed by asset for the dashboard chart."""
    rows: dict[str, float] = {}
    for symbol in symbols:
        quotes = [
            exchange_prices[symbol].price_usd
            for exchange_prices in prices_by_exchange.values()
            if symbol in exchange_prices
        ]
        if quotes:
            rows[symbol] = mean(quotes)
    return pd.DataFrame.from_dict(rows, orient="index", columns=["Average price (USD)"])


def portfolio_value_frame(rows: list[dict[str, str]]) -> pd.DataFrame:
    """Return holding values indexed by asset for a Streamlit bar chart."""
    values = {
        row["coin"]: float(row["value"].replace("$", "").replace(",", ""))
        for row in rows
    }
    return pd.DataFrame.from_dict(values, orient="index", columns=["Holding value (USD)"])


def prediction_frame(
    points: list[HistoricalPrice],
    predicted_price: float,
    prediction_timestamp: datetime,
) -> pd.DataFrame:
    """Return historical actuals and one forecast point on a shared time axis."""
    forecast_values: list[float] = [float("nan")] * len(points)
    if points:
        forecast_values[-1] = points[-1].price_usd
    historical = pd.DataFrame(
        {
            "Timestamp": [point.timestamp for point in points],
            "Historical live price": [point.price_usd for point in points],
            "Predicted price": forecast_values,
        }
    )
    forecast = pd.DataFrame(
        {
            "Timestamp": [prediction_timestamp],
            "Historical live price": [float("nan")],
            "Predicted price": [predicted_price],
        }
    )
    return pd.concat([historical, forecast], ignore_index=True).set_index("Timestamp")
