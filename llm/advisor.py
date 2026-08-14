"""Trading explanation and recommendation helpers."""

from __future__ import annotations

from llm.gemini import GeminiClient, GeminiError


def explain_arbitrage(opportunities: list[dict[str, str]]) -> dict[str, str]:
    """Explain arbitrage opportunities using Gemini when configured."""
    if not opportunities:
        return {
            "source": "Local advisor",
            "text": "No comparable multi-exchange opportunity is available right now.",
        }

    top = opportunities[0]
    prompt = (
        "Explain this cryptocurrency arbitrage opportunity in plain language. "
        "Do not calculate or invent any numbers. Use only the provided values. "
        "Mention risk briefly and keep it under 120 words.\n\n"
        f"Coin: {top['coin']}\n"
        f"Buy exchange: {top['buy_exchange']} at {top['buy_price']}\n"
        f"Sell exchange: {top['sell_exchange']} at {top['sell_price']}\n"
        f"Spread: {top['spread_percent']}\n"
        f"Fees: {top['fees']}\n"
        f"Net profit: {top['net_profit']}\n"
        f"Confidence: {top['confidence']}"
    )
    return _generate_or_fallback(prompt, _arbitrage_fallback(top))


def recommend_portfolio(summary: dict[str, str], holdings: list[dict[str, str]]) -> dict[str, str]:
    """Generate portfolio advice from already-computed portfolio data."""
    if not holdings:
        return {
            "source": "Local advisor",
            "text": "Add holdings first to receive portfolio-specific AI commentary.",
        }

    holding_lines = [
        f"{item['coin']}: value {item['value']}, profit/loss {item['profit_loss']}"
        for item in holdings[:6]
    ]
    prompt = (
        "Provide portfolio advice in plain language. Do not calculate or invent "
        "numbers. Use only the provided values and avoid financial guarantees. "
        "Keep it under 120 words.\n\n"
        f"Portfolio value: {summary['total_value']}\n"
        f"Total cost: {summary['total_cost']}\n"
        f"Profit/loss: {summary['profit_loss']} ({summary['profit_loss_percent']})\n"
        "Holdings:\n"
        + "\n".join(holding_lines)
    )
    return _generate_or_fallback(prompt, _portfolio_fallback(summary))


def answer_chat_question(question: str) -> dict[str, str]:
    """Answer a user question about crypto arbitrage concepts."""
    cleaned = question.strip()
    if not cleaned:
        return {"source": "Local advisor", "text": "Ask a question to get an explanation."}

    prompt = (
        "Answer this crypto arbitrage education question. Keep it concise, "
        "avoid financial guarantees, and do not invent live market numbers.\n\n"
        f"Question: {cleaned}"
    )
    return _generate_or_fallback(
        prompt,
        {
            "source": "Local advisor",
            "text": (
                "Arbitrage means buying an asset where it is cheaper and selling "
                "it where it is more expensive. In real markets, fees, transfer "
                "time, liquidity, and price movement can remove the profit."
            ),
        },
    )


def summarize_news(sentiment_summary: dict[str, str], articles: list[dict[str, str]]) -> dict[str, str]:
    """Summarize news sentiment using Gemini when available."""
    if not articles:
        return {
            "source": "Local advisor",
            "text": "No news articles are available for sentiment analysis right now.",
        }

    article_lines = [
        f"{item['title']} - sentiment {item['sentiment']}"
        for item in articles[:6]
    ]
    prompt = (
        "Summarize this crypto news sentiment for a dashboard. Do not invent "
        "facts or numbers. Use only the provided article titles and sentiment "
        "labels. Include likely market impact in plain language under 120 words.\n\n"
        f"Dominant sentiment: {sentiment_summary['dominant']}\n"
        f"Positive: {sentiment_summary['positive']}\n"
        f"Neutral: {sentiment_summary['neutral']}\n"
        f"Negative: {sentiment_summary['negative']}\n"
        "Articles:\n"
        + "\n".join(article_lines)
    )
    return _generate_or_fallback(prompt, _news_fallback(sentiment_summary))


def _generate_or_fallback(prompt: str, fallback: dict[str, str]) -> dict[str, str]:
    """Generate Gemini text with a safe local fallback."""
    try:
        return {"source": "Gemini", "text": GeminiClient().generate_text(prompt)}
    except GeminiError:
        return fallback


def _arbitrage_fallback(top: dict[str, str]) -> dict[str, str]:
    """Return deterministic arbitrage explanation when Gemini is unavailable."""
    return {
        "source": "Local advisor",
        "text": (
            f"{top['coin']} is cheaper on {top['buy_exchange']} and higher on "
            f"{top['sell_exchange']}. The listed net profit already includes "
            "fees, but execution risk remains because crypto prices can move "
            "before the trade settles."
        ),
    }


def _news_fallback(sentiment_summary: dict[str, str]) -> dict[str, str]:
    """Return deterministic news summary when Gemini is unavailable."""
    dominant = sentiment_summary["dominant"].lower()
    return {
        "source": "Local advisor",
        "text": (
            f"Current crypto news sentiment is mostly {dominant}. Treat this as "
            "context rather than a trade signal: confirm with live prices, "
            "exchange spreads, liquidity, and risk before acting."
        ),
    }


def _portfolio_fallback(summary: dict[str, str]) -> dict[str, str]:
    """Return deterministic portfolio advice when Gemini is unavailable."""
    return {
        "source": "Local advisor",
        "text": (
            f"Your portfolio shows {summary['profit_loss']} profit/loss against "
            f"a total value of {summary['total_value']}. Review concentration, "
            "keep position sizes deliberate, and avoid acting on a single signal."
        ),
    }
