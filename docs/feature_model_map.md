# Feature → Model / Technology Map

| Feature | Technology / API | Main implementation | Purpose | Live data |
| --- | --- | --- | --- | --- |
| Market dashboard | CoinGecko, Binance, CoinCap, Kraken public APIs | `api/market_data.py`, `app.py` | Fetch and compare current exchange quotes | Yes |
| Arbitrage scanner | Fee-aware Python arbitrage engine | `arbitrage/engine.py`, `arbitrage/calculator.py`, `arbitrage/fees.py` | Identify lowest buy and highest sell quote, then calculate gross/net profit | Yes |
| Price prediction | Optional TensorFlow LSTM; momentum fallback | `ml/predictor.py`, `ml/lstm.py` | Forecast from live historical prices | Yes |
| Prediction history | CoinGecko market chart; Binance k-lines fallback | `api/coingecko.py`, `api/binance.py`, `api/market_data.py` | Provide timestamped historical prices for forecast input and chart | Yes |
| Graphs | Streamlit charts and pandas data frames | `graphs/charts.py`, `app.py` | Render market, portfolio, and prediction charts from Python | Yes, except saved portfolio cost basis |
| Watchlist | SQLAlchemy plus live market APIs | `database/models.py`, `utils/watchlist.py`, `app.py` | Persist a user's assets and show their current quotes | Yes |
| Accounts and portfolios | SQLAlchemy, Werkzeug password hashing | `database/`, `utils/auth.py`, `utils/portfolio.py` | Persist users, encrypted password hashes, holdings, and trades | No for stored records; live prices for valuation |
| Advisor | Gemini REST API with constrained local text fallback | `llm/gemini.py`, `llm/advisor.py` | Generate natural-language explanations only | Gemini is optional; no financial calculations are delegated |
| News sentiment | RSS feeds and local keyword classifier | `sentiment/news_fetcher.py`, `sentiment/analyzer.py` | Summarize current crypto news sentiment | Yes |
