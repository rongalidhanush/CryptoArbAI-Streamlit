# CryptoArb AI Project Specification

CryptoArb AI is a Python + Streamlit application for live cryptocurrency
arbitrage analysis. It uses public API responses from CoinGecko, Binance,
CoinCap, and Kraken, then retains the existing fee-aware profit calculation and
opportunity detector.

## Required stack

- Python 3.12+
- Streamlit
- SQLAlchemy
- Requests
- SQLite locally and PostgreSQL in production
- Optional Google Gemini API for natural-language explanation only

## Architecture

- `app.py`: native Streamlit presentation and page navigation
- `api/`: external exchange API clients
- `arbitrage/`: exchange comparison, fees, and profit calculations
- `database/`: SQLAlchemy schema and session setup
- `ml/`: LSTM-ready and momentum prediction pipeline
- `llm/`: Gemini client and constrained advisor prompts
- `sentiment/`: RSS fetch and keyword sentiment analysis
- `utils/`: account and portfolio helpers

## Rules

- Preserve live API data; make failures visible instead of fabricating values.
- Do not add maintainable HTML, CSS, JavaScript, React, Node.js, npm, or other
  frontend build tooling.
- Use SQLAlchemy instead of raw SQL.
- Store secrets in environment variables or Streamlit secrets.
- Gemini must not calculate numerical values or make financial guarantees.
