"""Prediction service interface."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from statistics import mean

from api.base import APIClientError
from api.market_data import fetch_exchange_prices, fetch_historical_prices
from api.types import HistoricalPrice
from ml.lstm import load_model
from ml.preprocessing import clean_prices


HORIZON_FACTORS = {
    "15m": 0.25,
    "1h": 1.0,
    "24h": 24.0,
}

HORIZON_DELTAS = {
    "15m": timedelta(minutes=15),
    "1h": timedelta(hours=1),
    "24h": timedelta(hours=24),
}

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class PredictionResult:
    """Price prediction result for a coin and horizon."""

    symbol: str
    horizon: str
    current_price: float
    predicted_price: float
    trend: str
    confidence: float
    method: str
    history: list[float]
    history_points: list[HistoricalPrice]
    historical_source: str
    generated_at: datetime
    prediction_timestamp: datetime

    @property
    def formatted_current_price(self) -> str:
        """Return formatted current price."""
        return _format_usd(self.current_price)

    @property
    def formatted_predicted_price(self) -> str:
        """Return formatted predicted price."""
        return _format_usd(self.predicted_price)


def predict_price(symbol: str = "BTC", horizon: str = "1h") -> PredictionResult:
    """Predict a future price using LSTM when available, otherwise momentum."""
    normalized_symbol = symbol.upper()
    normalized_horizon = horizon if horizon in HORIZON_FACTORS else "1h"
    current_price = _current_price(normalized_symbol)
    history_points, historical_source = _historical_prices(normalized_symbol)
    history = clean_prices([point.price_usd for point in history_points])
    if len(history) < 24:
        raise APIClientError(
            f"Historical live data for {normalized_symbol} has fewer than 24 valid points."
        )
    history_points = history_points[-len(history):]
    model = _load_model(normalized_symbol)

    if model:
        try:
            predicted_price = _predict_with_lstm(model, history)
            method = "LSTM"
        except Exception as exc:  # Model files can become incompatible after upgrades.
            LOGGER.exception("LSTM prediction failed for %s: %s", normalized_symbol, exc)
            predicted_price = _predict_with_momentum(
                history,
                current_price,
                HORIZON_FACTORS[normalized_horizon],
            )
            method = "Momentum fallback (LSTM unavailable)"
    else:
        predicted_price = _predict_with_momentum(
            history,
            current_price,
            HORIZON_FACTORS[normalized_horizon],
        )
        method = "Momentum fallback"

    trend = _trend(current_price, predicted_price)
    confidence = _confidence(history, current_price, predicted_price, method)
    generated_at = datetime.now(timezone.utc)
    return PredictionResult(
        symbol=normalized_symbol,
        horizon=normalized_horizon,
        current_price=current_price,
        predicted_price=predicted_price,
        trend=trend,
        confidence=confidence,
        method=method,
        history=history[-48:],
        history_points=history_points[-48:],
        historical_source=historical_source,
        generated_at=generated_at,
        prediction_timestamp=generated_at + HORIZON_DELTAS[normalized_horizon],
    )


def _current_price(symbol: str) -> float:
    """Return average current price from available exchanges."""
    prices_by_exchange = fetch_exchange_prices([symbol])
    quotes = [
        quote.price_usd
        for exchange_prices in prices_by_exchange.values()
        if (quote := exchange_prices.get(symbol))
    ]
    if not quotes:
        raise APIClientError(f"No live current price is available for {symbol}.")
    return mean(quotes)


def _historical_prices(symbol: str) -> tuple[list[HistoricalPrice], str]:
    """Fetch timestamped live history with a compatible Binance fallback."""
    points, source = fetch_historical_prices(symbol, days=30)
    valid_points = [point for point in points if point.price_usd > 0]
    if not valid_points:
        raise APIClientError(f"Historical live data is unavailable for {symbol}.")
    return valid_points, source


def _load_model(symbol: str) -> object | None:
    """Load an optional LSTM model without surfacing model errors to users."""
    try:
        return load_model(symbol)
    except Exception as exc:
        LOGGER.exception("Could not load LSTM model for %s: %s", symbol, exc)
        return None


def _predict_with_lstm(model: object, history: list[float]) -> float:
    """Predict the next normalized point using a saved TensorFlow model."""
    import numpy as np

    window = history[-24:]
    minimum = min(window)
    maximum = max(window)
    if minimum == maximum:
        return maximum
    normalized = [(price - minimum) / (maximum - minimum) for price in window]
    x_input = np.array(normalized).reshape((1, 24, 1))
    normalized_prediction = float(model.predict(x_input, verbose=0)[0][0])
    return (normalized_prediction * (maximum - minimum)) + minimum


def _predict_with_momentum(
    history: list[float],
    current_price: float,
    horizon_factor: float,
) -> float:
    """Predict price using recent average hourly momentum."""
    recent = history[-24:] if len(history) >= 24 else history
    if len(recent) < 2:
        return current_price

    hourly_changes = [
        recent[index] - recent[index - 1]
        for index in range(1, len(recent))
    ]
    average_change = mean(hourly_changes)
    return max(current_price + (average_change * horizon_factor), 0)


def _trend(current_price: float, predicted_price: float) -> str:
    """Return a trend label for the prediction."""
    delta_percent = ((predicted_price - current_price) / current_price) * 100
    if delta_percent > 0.5:
        return "Bullish"
    if delta_percent < -0.5:
        return "Bearish"
    return "Neutral"


def _confidence(
    history: list[float],
    current_price: float,
    predicted_price: float,
    method: str,
) -> float:
    """Estimate prediction confidence from method and forecast distance."""
    method_score = 72 if method == "LSTM" else 54
    movement = abs((predicted_price - current_price) / current_price) * 100
    penalty = min(movement * 3, 24)
    history_bonus = min(len(history) / 720, 1) * 14
    return round(max(method_score + history_bonus - penalty, 20), 1)


def _format_usd(value: float) -> str:
    """Format a price for display."""
    if value >= 1:
        return f"${value:,.2f}"
    return f"${value:,.6f}"
