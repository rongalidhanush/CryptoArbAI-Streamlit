"""Streamlit entrypoint for the live CryptoArb AI dashboard."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import logging

import streamlit as st
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from api.base import APIClientError
from api.coins import coin_name, supported_symbols
from api.market_data import fetch_exchange_prices
from api.types import PriceQuote
from arbitrage.engine import ArbitrageOpportunity, find_opportunities
from config import get_settings, load_streamlit_secrets
from database import get_session, initialize_database, remove_session
from database.models import Portfolio, TradeHistory, User
from graphs.charts import market_price_frame, portfolio_value_frame, prediction_frame
from llm.advisor import answer_chat_question, explain_arbitrage, recommend_portfolio, summarize_news
from ml.predictor import predict_price
from sentiment.analyzer import analyze_articles
from sentiment.news_fetcher import fetch_latest_news
from utils.auth import authenticate_user, create_user, validate_registration
from utils.portfolio import build_holding_rows, current_prices_for_holdings, format_summary
from utils.watchlist import (
    add_to_watchlist,
    build_watchlist_rows,
    list_watchlist,
    remove_from_watchlist,
)


LOGGER = logging.getLogger(__name__)

load_streamlit_secrets()
DATABASE_INITIALIZATION_ERROR: str | None = None
try:
    initialize_database()
except SQLAlchemyError as exc:
    LOGGER.exception("Database initialization failed: %s", exc)
    DATABASE_INITIALIZATION_ERROR = (
        "The application database is unavailable. Check DATABASE_URL and try again."
    )
SETTINGS = get_settings()

st.set_page_config(page_title="CryptoArb AI", page_icon="₿", layout="wide")


@st.cache_data(ttl=SETTINGS.market_refresh_interval_seconds, show_spinner=False)
def load_live_market_data(symbols: tuple[str, ...], quantity: float) -> tuple[
    dict[str, dict[str, PriceQuote]], list[ArbitrageOpportunity]
]:
    """Fetch current live prices and run the retained arbitrage engine."""
    prices = fetch_exchange_prices(list(symbols))
    return prices, find_opportunities(prices, quantity=quantity)


@st.cache_data(ttl=SETTINGS.market_refresh_interval_seconds, show_spinner=False)
def load_live_forecast(symbol: str, horizon: str):
    """Cache a short-lived live forecast without storing it as user data."""
    return predict_price(symbol, horizon)


def format_usd(value: float | Decimal) -> str:
    """Format a USD value for a compact dashboard display."""
    numeric_value = float(value)
    return f"${numeric_value:,.6f}" if abs(numeric_value) < 1 else f"${numeric_value:,.2f}"


def current_user() -> User | None:
    """Resolve the signed-in user for the current Streamlit browser session."""
    user_id = st.session_state.get("user_id")
    return get_session().get(User, user_id) if user_id else None


def render_authentication() -> User | None:
    """Render native Streamlit sign-in and registration controls."""
    user = current_user()
    if user:
        return user

    st.title("CryptoArb AI")
    st.caption("Live cryptocurrency arbitrage analytics. Educational use only; no trades are executed.")
    sign_in, create_account = st.tabs(["Sign in", "Create account"])
    with sign_in:
        with st.form("sign_in"):
            identifier = st.text_input("Username or email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in", type="primary")
        if submitted:
            user = authenticate_user(identifier, password)
            if user:
                st.session_state.user_id = user.id
                st.rerun()
            st.error("Invalid username/email or password.")
    with create_account:
        with st.form("create_account"):
            username = st.text_input("Username")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password", key="register_password")
            confirm = st.text_input("Confirm password", type="password")
            submitted = st.form_submit_button("Create account", type="primary")
        if submitted:
            errors = validate_registration(username, email, password, confirm)
            if errors:
                for error in errors:
                    st.error(error)
            else:
                user = create_user(username, email, password)
                st.session_state.user_id = user.id
                st.rerun()
    return None


def render_header(user: User) -> str:
    """Render sidebar navigation and return the selected page."""
    with st.sidebar:
        st.title("CryptoArb AI")
        st.caption(f"Signed in as {user.username}")
        page = st.radio(
            "Navigate",
            [
                "Dashboard",
                "Arbitrage",
                "Watchlist",
                "Portfolio",
                "Prediction",
                "News",
                "Advisor",
            ],
        )
        st.caption(f"Live refresh TTL: {SETTINGS.market_refresh_interval_seconds}s")
        if st.button("Refresh live data", width="stretch"):
            load_live_market_data.clear()
            load_live_forecast.clear()
            st.rerun()
        if st.button("Sign out", width="stretch"):
            st.session_state.pop("user_id", None)
            remove_session()
            st.rerun()
    return page


def market_rows(prices: dict[str, dict[str, PriceQuote]], symbols: list[str]) -> list[dict[str, object]]:
    """Create a native-table market overview from live exchange quotes."""
    rows: list[dict[str, object]] = []
    for symbol in symbols:
        quotes = [values[symbol] for values in prices.values() if symbol in values]
        if not quotes:
            continue
        primary = next((quote for quote in quotes if quote.change_24h is not None), quotes[0])
        rows.append(
            {
                "Coin": symbol,
                "Name": coin_name(symbol),
                "Current price": format_usd(primary.price_usd),
                "Exchange": primary.exchange,
                "24h change": primary.formatted_change,
                "24h volume": format_usd(primary.volume_24h) if primary.volume_24h else "n/a",
                "Updated": primary.fetched_at.strftime("%H:%M:%S UTC"),
            }
        )
    return rows


def opportunity_rows(
    opportunities: list[ArbitrageOpportunity],
    quantity: float,
) -> list[dict[str, object]]:
    """Create table rows without modifying arbitrage calculations."""
    return [
        {
            "Coin": item.coin,
            "Buy exchange": item.buy_exchange,
            "Sell exchange": item.sell_exchange,
            "Buy price": format_usd(item.buy_price_usd),
            "Sell price": format_usd(item.sell_price_usd),
            "Difference": format_usd(item.spread_usd),
            "Spread": f"{item.spread_percent:.2f}%",
            "Quantity": f"{quantity:,.6f}",
            "Estimated gross profit": format_usd(item.profit.gross_profit_usd),
            "Fees": format_usd(item.profit.total_fees_usd),
            "Estimated net profit": format_usd(item.profit.net_profit_usd),
            "Profit": f"{item.profit.profit_percent:.2f}%",
            "Status": "Profitable" if item.is_profitable else "Fees exceed spread",
            "Confidence": f"{item.confidence_score:.1f}%",
        }
        for item in opportunities
    ]


def source_comparison_rows(
    prices: dict[str, dict[str, PriceQuote]],
    symbols: list[str],
) -> list[dict[str, object]]:
    """Show the source quotes that support each arbitrage comparison."""
    rows: list[dict[str, object]] = []
    for symbol in symbols:
        for source, quotes in prices.items():
            quote = quotes.get(symbol)
            if quote is None:
                continue
            rows.append(
                {
                    "Asset": symbol,
                    "Source": source,
                    "Live price": format_usd(quote.price_usd),
                    "24h change": quote.formatted_change,
                    "Updated": quote.fetched_at.strftime("%H:%M:%S UTC"),
                }
            )
    return rows


def fetch_or_report(symbols: list[str], quantity: float = 1.0) -> tuple[
    dict[str, dict[str, PriceQuote]], list[ArbitrageOpportunity]
]:
    """Fetch live data and give users a safe status instead of demo content."""
    with st.spinner("Fetching live exchange data..."):
        prices, opportunities = load_live_market_data(tuple(symbols), quantity)
    if not prices:
        st.error("No live exchange API responded. Check network access or try again shortly.")
    elif len(prices) < 2:
        st.warning("Comparison requires data from at least two live sources.")
    return prices, opportunities


def render_dashboard() -> None:
    """Render the live market overview and best current opportunities."""
    st.title("Live market dashboard")
    st.caption("Prices are fetched from the configured public exchange APIs; no simulated prices are shown.")
    symbols = supported_symbols()
    prices, opportunities = fetch_or_report(symbols)
    rows = market_rows(prices, symbols)
    profitable = [item for item in opportunities if item.is_profitable]
    best = profitable[0] if profitable else None
    metrics = st.columns(4)
    metrics[0].metric("Live exchanges", len(prices))
    metrics[1].metric("Quoted assets", len(rows))
    metrics[2].metric("Profitable opportunities", len(profitable))
    metrics[3].metric("Best net profit", format_usd(best.profit.net_profit_usd) if best else "n/a")
    if prices:
        st.success(f"Connected to: {', '.join(prices)}")
    if rows:
        st.subheader("Market overview")
        st.dataframe(rows, width="stretch", hide_index=True)
        st.bar_chart(market_price_frame(prices, [row["Coin"] for row in rows]))
    st.subheader("Arbitrage opportunities")
    if opportunities:
        st.dataframe(opportunity_rows(opportunities, quantity=1.0), width="stretch", hide_index=True)
    else:
        st.info("No comparable multi-exchange opportunity is available from the live responses.")
    st.caption(f"Last dashboard render: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")


def render_arbitrage(user: User) -> None:
    """Render opportunity filters, fee-aware results, and trade recording."""
    st.title("Arbitrage scanner")
    filter_col, amount_col = st.columns([3, 1])
    with filter_col:
        symbols = st.multiselect("Assets", supported_symbols(), default=supported_symbols()[:8])
    with amount_col:
        quantity = st.number_input("Trade quantity", min_value=0.000001, value=1.0, format="%.6f")
    if not symbols:
        st.info("Select at least one asset to scan.")
        return
    prices, opportunities = fetch_or_report(symbols, quantity)
    comparison_rows = source_comparison_rows(prices, symbols)
    if comparison_rows:
        with st.expander("Live source comparison", expanded=True):
            st.dataframe(comparison_rows, width="stretch", hide_index=True)
    if len(prices) < 2:
        return
    minimum_profit = st.number_input("Minimum net profit (USD)", value=0.0, step=1.0)
    visible = [item for item in opportunities if item.profit.net_profit_usd >= minimum_profit]
    if not visible:
        st.info("No live opportunities meet the selected minimum net profit.")
        return
    st.dataframe(opportunity_rows(visible, quantity), width="stretch", hide_index=True)
    top = visible[0]
    if top.is_profitable:
        st.success(f"Best live result: {top.coin} nets {format_usd(top.profit.net_profit_usd)} after the configured fees.")
    else:
        st.warning("The displayed spreads do not cover the configured trading, withdrawal, and network fees.")
    serialized = [{
        "coin": item.coin, "buy_exchange": item.buy_exchange, "sell_exchange": item.sell_exchange,
        "buy_price": format_usd(item.buy_price_usd), "sell_price": format_usd(item.sell_price_usd),
        "spread_percent": f"{item.spread_percent:.2f}%", "fees": format_usd(item.profit.total_fees_usd),
        "net_profit": format_usd(item.profit.net_profit_usd), "confidence": f"{item.confidence_score:.1f}%",
    } for item in visible]
    with st.expander("AI explanation of the top result"):
        advice = explain_arbitrage(serialized)
        st.caption(advice["source"])
        st.write(advice["text"])
    choice = st.selectbox("Record an opportunity", range(len(visible)), format_func=lambda index: f"{visible[index].coin}: {visible[index].buy_exchange} → {visible[index].sell_exchange}")
    if st.button("Save selected trade"):
        item = visible[choice]
        session = get_session()
        session.add(TradeHistory(
            user_id=user.id, coin=item.coin, buy_exchange=item.buy_exchange,
            sell_exchange=item.sell_exchange, gross_profit=Decimal(str(item.profit.gross_profit_usd)),
            fees=Decimal(str(item.profit.total_fees_usd)), net_profit=Decimal(str(item.profit.net_profit_usd)),
        ))
        session.commit()
        st.success("Trade record saved.")


def render_portfolio(user: User) -> None:
    """Render portfolio CRUD, live valuation, and native Python charts."""
    st.title("Portfolio")
    session = get_session()
    holdings = list(session.scalars(select(Portfolio).where(Portfolio.user_id == user.id).order_by(Portfolio.coin)))
    with st.expander("Add holding"):
        with st.form("add_holding"):
            coin = st.selectbox("Asset", supported_symbols())
            quantity = st.number_input("Quantity", min_value=0.00000001, value=1.0, format="%.8f")
            buy_price = st.number_input("Average buy price (USD)", min_value=0.00000001, value=1.0, format="%.8f")
            submitted = st.form_submit_button("Save holding")
        if submitted:
            session.add(Portfolio(user_id=user.id, coin=coin, quantity=Decimal(str(quantity)), buy_price=Decimal(str(buy_price))))
            session.commit()
            st.rerun()
    if not holdings:
        st.info("No holdings recorded yet.")
        return
    prices = current_prices_for_holdings(holdings)
    if not prices:
        st.warning("Live prices are currently unavailable; valuation cannot be refreshed.")
    rows, summary = build_holding_rows(holdings, prices)
    formatted = format_summary(summary)
    metrics = st.columns(3)
    metrics[0].metric("Portfolio value", formatted["total_value"])
    metrics[1].metric("Total cost", formatted["total_cost"])
    metrics[2].metric("Profit / loss", formatted["profit_loss"], formatted["profit_loss_percent"])
    st.dataframe(rows, width="stretch", hide_index=True)
    st.bar_chart(portfolio_value_frame(rows))
    with st.expander("Portfolio commentary"):
        advice = recommend_portfolio(formatted, rows)
        st.caption(advice["source"])
        st.write(advice["text"])
    holding_lookup = {f"{holding.coin} #{holding.id}": holding for holding in holdings}
    selected_label = st.selectbox("Edit or remove holding", list(holding_lookup))
    selected = holding_lookup[selected_label]
    edit_col, remove_col = st.columns(2)
    with edit_col:
        with st.form("edit_holding"):
            quantity = st.number_input("New quantity", min_value=0.00000001, value=float(selected.quantity), format="%.8f")
            buy_price = st.number_input("New average buy price", min_value=0.00000001, value=float(selected.buy_price), format="%.8f")
            if st.form_submit_button("Update holding"):
                selected.quantity = Decimal(str(quantity))
                selected.buy_price = Decimal(str(buy_price))
                session.commit()
                st.rerun()
    with remove_col:
        st.write("")
        st.write("")
        if st.button("Remove holding", type="secondary"):
            session.delete(selected)
            session.commit()
            st.rerun()


def render_watchlist(user: User) -> None:
    """Render persistent user watchlist entries with live market quotes."""
    st.title("Watchlist")
    st.caption("Saved assets remain linked to this account; prices are refreshed from live sources.")
    items = list_watchlist(user.id)
    with st.form("add_to_watchlist", clear_on_submit=True):
        add_col, submit_col = st.columns([3, 1])
        coin = add_col.selectbox("Add asset", supported_symbols(), key="watchlist_asset")
        submitted = submit_col.form_submit_button("Add asset", type="primary")
    if submitted:
        _, created = add_to_watchlist(user.id, coin)
        if created:
            st.success(f"{coin} added to your watchlist.")
            st.rerun()
        st.info(f"{coin} is already in your watchlist.")
    if not items:
        st.info("Add an asset to start tracking its live price and 24-hour movement.")
        return
    symbols = [item.coin for item in items]
    prices, _ = fetch_or_report(symbols)
    st.dataframe(build_watchlist_rows(items, prices), width="stretch", hide_index=True)
    selected = st.selectbox(
        "Manage watched asset",
        items,
        format_func=lambda item: item.coin,
    )
    remove_col, prediction_col = st.columns(2)
    with remove_col:
        if st.button(f"Remove {selected.coin}", type="secondary"):
            if remove_from_watchlist(user.id, selected.id):
                st.success(f"{selected.coin} removed from your watchlist.")
                st.rerun()
    with prediction_col:
        if st.button(f"Use {selected.coin} in prediction"):
            st.session_state.prediction_asset = selected.coin
            st.info("Open Prediction from the sidebar to generate a live-data forecast.")


def render_prediction() -> None:
    """Render live-data price forecast controls with explicit API failures."""
    st.title("Price prediction")
    coin_col, horizon_col = st.columns(2)
    default_symbol = st.session_state.pop("prediction_asset", "BTC")
    symbol = coin_col.selectbox(
        "Asset",
        supported_symbols(),
        index=supported_symbols().index(default_symbol),
    )
    horizon = horizon_col.radio("Forecast horizon", ["15m", "1h", "24h"], horizontal=True)
    if st.button("Generate live-data forecast", type="primary"):
        try:
            with st.spinner("Fetching live and historical prices..."):
                result = load_live_forecast(symbol, horizon)
        except APIClientError as exc:
            st.error(str(exc))
            return
        st.session_state.prediction_result = result
    result = st.session_state.get("prediction_result")
    if result and result.symbol == symbol and result.horizon == horizon:
        metrics = st.columns(4)
        metrics[0].metric("Current price", result.formatted_current_price)
        metrics[1].metric("Forecast", result.formatted_predicted_price)
        metrics[2].metric("Trend", result.trend)
        metrics[3].metric("Model confidence", f"{result.confidence:.1f}%")
        st.caption(
            f"Horizon: {result.horizon} · History source: {result.historical_source} · "
            f"Generated: {result.generated_at.strftime('%Y-%m-%d %H:%M UTC')}"
        )
        st.caption(
            f"Forecast timestamp: {result.prediction_timestamp.strftime('%Y-%m-%d %H:%M UTC')} · "
            f"Method: {result.method}. Educational estimate only, not trading advice."
        )
        st.line_chart(
            prediction_frame(
                result.history_points,
                result.predicted_price,
                result.prediction_timestamp,
            )
        )


def render_news() -> None:
    """Render live RSS news and local/Gemini sentiment explanation."""
    st.title("News sentiment")
    if st.button("Refresh live news", type="primary"):
        st.session_state.pop("news", None)
    if "news" not in st.session_state:
        with st.spinner("Fetching configured RSS feeds..."):
            st.session_state.news = fetch_latest_news()
    articles = st.session_state.news
    if not articles:
        st.warning("No live news feed responded. Try again later.")
        return
    rows, summary = analyze_articles(articles)
    metrics = st.columns(4)
    metrics[0].metric("Positive", summary["positive"])
    metrics[1].metric("Neutral", summary["neutral"])
    metrics[2].metric("Negative", summary["negative"])
    metrics[3].metric("Dominant", summary["dominant"])
    st.dataframe(rows, width="stretch", hide_index=True, column_config={"link": st.column_config.LinkColumn("Source")})
    advice = summarize_news(summary, rows)
    st.subheader("Market context")
    st.caption(advice["source"])
    st.write(advice["text"])


def render_advisor() -> None:
    """Render the existing Gemini-backed educational chat interface."""
    st.title("Arbitrage advisor")
    question = st.text_area("Ask about crypto arbitrage concepts", placeholder="How do trading fees affect arbitrage?")
    if st.button("Ask advisor", type="primary"):
        answer = answer_chat_question(question)
        st.caption(answer["source"])
        st.write(answer["text"])


def main() -> None:
    """Run the Streamlit application."""
    if DATABASE_INITIALIZATION_ERROR:
        st.error(DATABASE_INITIALIZATION_ERROR)
        st.info("For deployment, configure a reachable managed PostgreSQL DATABASE_URL.")
        return
    user = render_authentication()
    if not user:
        return
    page = render_header(user)
    if page == "Dashboard":
        render_dashboard()
    elif page == "Arbitrage":
        render_arbitrage(user)
    elif page == "Watchlist":
        render_watchlist(user)
    elif page == "Portfolio":
        render_portfolio(user)
    elif page == "Prediction":
        render_prediction()
    elif page == "News":
        render_news()
    else:
        render_advisor()


if __name__ == "__main__":
    main()
