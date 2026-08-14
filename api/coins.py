"""Supported cryptocurrency metadata for UI and API integrations."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Coin:
    """Display and API metadata for a supported cryptocurrency."""

    symbol: str
    name: str
    coingecko_id: str
    coincap_id: str
    binance_pair: str | None = None
    kraken_pair: str | None = None


SUPPORTED_COINS = [
    Coin("BTC", "Bitcoin", "bitcoin", "bitcoin", "BTCUSDT", "XBTUSD"),
    Coin("ETH", "Ethereum", "ethereum", "ethereum", "ETHUSDT", "ETHUSD"),
    Coin("SOL", "Solana", "solana", "solana", "SOLUSDT", "SOLUSD"),
    Coin("BNB", "BNB", "binancecoin", "binance-coin", "BNBUSDT", "BNBUSD"),
    Coin("XRP", "XRP", "ripple", "xrp", "XRPUSDT", "XRPUSD"),
    Coin("DOGE", "Dogecoin", "dogecoin", "dogecoin", "DOGEUSDT", "DOGEUSD"),
    Coin("ADA", "Cardano", "cardano", "cardano", "ADAUSDT", "ADAUSD"),
    Coin("AVAX", "Avalanche", "avalanche-2", "avalanche", "AVAXUSDT", "AVAXUSD"),
    Coin("DOT", "Polkadot", "polkadot", "polkadot", "DOTUSDT", "DOTUSD"),
    Coin("MATIC", "Polygon", "matic-network", "polygon", "MATICUSDT", "MATICUSD"),
    Coin("LINK", "Chainlink", "chainlink", "chainlink", "LINKUSDT", "LINKUSD"),
    Coin("LTC", "Litecoin", "litecoin", "litecoin", "LTCUSDT", "LTCUSD"),
    Coin("BCH", "Bitcoin Cash", "bitcoin-cash", "bitcoin-cash", "BCHUSDT", "BCHUSD"),
    Coin("UNI", "Uniswap", "uniswap", "uniswap", "UNIUSDT", "UNIUSD"),
    Coin("ATOM", "Cosmos", "cosmos", "cosmos", "ATOMUSDT", "ATOMUSD"),
    Coin("ETC", "Ethereum Classic", "ethereum-classic", "ethereum-classic", "ETCUSDT", "ETCUSD"),
    Coin("FIL", "Filecoin", "filecoin", "filecoin", "FILUSDT", "FILUSD"),
    Coin("APT", "Aptos", "aptos", "aptos", "APTUSDT", "APTUSD"),
    Coin("ARB", "Arbitrum", "arbitrum", "arbitrum", "ARBUSDT", "ARBUSD"),
    Coin("OP", "Optimism", "optimism", "optimism", "OPUSDT", "OPUSD"),
    Coin("NEAR", "NEAR Protocol", "near", "near-protocol", "NEARUSDT", "NEARUSD"),
    Coin("TRX", "TRON", "tron", "tron", "TRXUSDT", "TRXUSD"),
    Coin("SHIB", "Shiba Inu", "shiba-inu", "shiba-inu", "SHIBUSDT", "SHIBUSD"),
]


COINS_BY_SYMBOL = {coin.symbol: coin for coin in SUPPORTED_COINS}


def supported_symbols() -> list[str]:
    """Return supported coin symbols in display order."""
    return [coin.symbol for coin in SUPPORTED_COINS]


def coin_name(symbol: str) -> str:
    """Return the display name for a supported symbol."""
    coin = COINS_BY_SYMBOL.get(symbol.upper())
    return coin.name if coin else symbol.upper()
