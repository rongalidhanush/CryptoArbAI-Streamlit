"""Offline tests for the preserved arbitrage calculations."""

import unittest

from api.types import PriceQuote
from arbitrage.calculator import calculate_profit
from arbitrage.engine import find_opportunities
from arbitrage.fees import FeeSchedule


class ArbitrageTests(unittest.TestCase):
    """Verify calculations independently of external API availability."""

    def test_profit_includes_all_configured_fees(self) -> None:
        fee = FeeSchedule(0.01, 1.5, 0.75)
        result = calculate_profit(100.0, 110.0, 2.0, fee, fee)
        self.assertEqual(result.gross_profit_usd, 20.0)
        self.assertAlmostEqual(result.trading_fee_usd, 4.2)
        self.assertAlmostEqual(result.total_fees_usd, 6.45)
        self.assertAlmostEqual(result.net_profit_usd, 13.55)

    def test_engine_selects_lowest_buy_and_highest_sell(self) -> None:
        prices = {
            "Alpha": {"BTC": PriceQuote("BTC", "Alpha", 100.0)},
            "Beta": {"BTC": PriceQuote("BTC", "Beta", 110.0)},
        }
        opportunities = find_opportunities(prices)
        self.assertEqual(len(opportunities), 1)
        self.assertEqual(opportunities[0].buy_exchange, "Alpha")
        self.assertEqual(opportunities[0].sell_exchange, "Beta")


if __name__ == "__main__":
    unittest.main()
