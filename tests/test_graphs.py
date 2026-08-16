"""Tests for native Streamlit chart-data builders."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest

from api.types import HistoricalPrice
from graphs.charts import prediction_frame


class GraphTests(unittest.TestCase):
    """Verify charts include actual historical and predicted data."""

    def test_prediction_frame_has_history_and_forecast(self) -> None:
        """A prediction chart should retain actuals and append a forecast point."""
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        points = [
            HistoricalPrice(timestamp=start, price_usd=100.0),
            HistoricalPrice(timestamp=start + timedelta(hours=1), price_usd=102.0),
        ]
        frame = prediction_frame(points, 103.5, start + timedelta(hours=2))
        self.assertEqual(len(frame), 3)
        self.assertEqual(frame.iloc[0]["Historical live price"], 100.0)
        self.assertEqual(frame.iloc[-1]["Predicted price"], 103.5)
