"""Historical price preprocessing utilities."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScaledSeries:
    """Normalized price series with scaler metadata."""

    values: list[float]
    minimum: float
    maximum: float


def clean_prices(prices: list[float]) -> list[float]:
    """Remove invalid historical price values."""
    return [float(price) for price in prices if price and price > 0]


def normalize_prices(prices: list[float]) -> ScaledSeries:
    """Normalize prices to the 0-1 range for model input."""
    cleaned = clean_prices(prices)
    if not cleaned:
        return ScaledSeries([], 0.0, 0.0)

    minimum = min(cleaned)
    maximum = max(cleaned)
    if minimum == maximum:
        return ScaledSeries([0.5 for _ in cleaned], minimum, maximum)

    return ScaledSeries(
        values=[(price - minimum) / (maximum - minimum) for price in cleaned],
        minimum=minimum,
        maximum=maximum,
    )


def denormalize_price(value: float, scaled: ScaledSeries) -> float:
    """Convert a normalized price back into the original price range."""
    if scaled.minimum == scaled.maximum:
        return scaled.maximum
    return (value * (scaled.maximum - scaled.minimum)) + scaled.minimum


def create_sequences(
    normalized_prices: list[float],
    window_size: int = 24,
) -> tuple[list[list[float]], list[float]]:
    """Create sliding-window training sequences for an LSTM."""
    if len(normalized_prices) <= window_size:
        return [], []

    inputs: list[list[float]] = []
    targets: list[float] = []
    for index in range(window_size, len(normalized_prices)):
        inputs.append(normalized_prices[index - window_size:index])
        targets.append(normalized_prices[index])
    return inputs, targets
