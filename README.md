# CryptoArb AI

CryptoArb AI is a Python + Streamlit cryptocurrency arbitrage dashboard. It
fetches live public prices from CoinGecko, Binance, CoinCap, and Kraken; compares
the returned quotes using the existing fee-aware arbitrage engine; persists user
accounts, portfolios, and saved trade records with SQLAlchemy; and provides
optional Gemini commentary.

No HTML, CSS, JavaScript, Node.js, npm, or frontend build tool is maintained in
this repository. The dashboard uses Streamlit layouts, widgets, tables, metrics,
forms, and charts directly from Python.

## Features

- Live market overview with source and timestamp visibility
- Fee-aware cross-exchange arbitrage scanner
- Persistent per-user watchlists, saved trade history, and portfolio holdings
- Live portfolio valuation and native Streamlit charts
- Historical-price forecast interface (LSTM when a local model is available,
  otherwise the existing momentum model)
- Live RSS news sentiment and optional Gemini explanations
- Local SQLite by default; PostgreSQL supported through `DATABASE_URL`

CryptoArb AI does not execute trades and is for education and analysis only.

## Project structure

```text
CryptoArbAI/
  app.py                 # Streamlit entry point
  config.py              # Environment and Streamlit-secrets settings
  api/                   # Live public exchange API clients
  arbitrage/             # Preserved fee and profit calculations
  database/              # SQLAlchemy schema and session setup
  graphs/                # Python chart-data builders for Streamlit
  llm/                   # Gemini natural-language integration
  ml/                    # Existing LSTM/momentum prediction logic
  sentiment/             # RSS fetch and sentiment analysis
  utils/                 # Account and portfolio helpers
  tests/                 # Offline unit tests
  .streamlit/config.toml # Native Streamlit theme configuration
```

## Local setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
streamlit run app.py
```

Open the URL displayed by Streamlit, register an account, and use the sidebar to
navigate. Add `GEMINI_API_KEY` to `.env` only if Gemini commentary is desired.

## Configuration and secrets

Copy `.env.example` to `.env` for local development. Streamlit deployments can
instead use `.streamlit/secrets.toml` or the host's secret manager with the same
keys. Never commit either `.env` or `secrets.toml`.

```text
DATABASE_URL=sqlite:///database/database.db
GEMINI_API_KEY=
API_TIMEOUT_SECONDS=8
MARKET_CACHE_TTL_SECONDS=30
MARKET_REFRESH_INTERVAL_SECONDS=30
```

`DATABASE_URL` accepts a PostgreSQL URL in production. Existing `postgres://`
URLs are normalized automatically for SQLAlchemy. User accounts, portfolios,
watchlists, and saved trades are committed to this database; only the temporary
signed-in browser indicator uses Streamlit session state.

## Deployment

Deploy with a Streamlit-compatible service such as Streamlit Community Cloud or
Render. Configure:

```text
Build command: pip install -r requirements.txt
Start command: streamlit run app.py --server.address 0.0.0.0 --server.port $PORT
```

On Streamlit Community Cloud, set `app.py` as the entry point and provide secrets
through its secret configuration. Set `DATABASE_URL` to a managed PostgreSQL
database in deployment: local SQLite files are ephemeral on services without a
persistent disk and cannot guarantee that accounts or watchlists survive a
redeploy.

## Feature map

See [docs/feature_model_map.md](docs/feature_model_map.md) for the modules and
live sources behind each feature.

## Live-data behavior

The dashboard does not substitute static prices, arbitrary opportunities, or
offline news when a service fails. It reports the affected live-source failure in
the UI, logs request failures in the Python services, and lets the user refresh.
The API client TTL cache and Streamlit data cache reduce avoidable rate-limit
pressure without turning live data into mock data.
