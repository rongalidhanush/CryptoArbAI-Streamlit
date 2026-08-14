"""Sentiment analysis utilities."""

from __future__ import annotations

from collections import Counter

from sentiment.news_fetcher import NewsArticle


POSITIVE_TERMS = {
    "gain",
    "gains",
    "growth",
    "rally",
    "surge",
    "bullish",
    "improves",
    "stronger",
    "adoption",
    "record",
}

NEGATIVE_TERMS = {
    "loss",
    "losses",
    "crash",
    "drop",
    "bearish",
    "risk",
    "hack",
    "fraud",
    "lawsuit",
    "volatility",
    "concern",
}


def analyze_articles(articles: list[NewsArticle]) -> tuple[list[dict[str, str]], dict[str, str]]:
    """Classify articles and summarize overall sentiment."""
    rows = []
    counts: Counter[str] = Counter()
    for article in articles:
        sentiment, score = classify_sentiment(f"{article.title} {article.summary}")
        counts[sentiment] += 1
        rows.append(
            {
                "title": article.title,
                "link": article.link,
                "source": article.source,
                "published_at": article.published_at,
                "summary": article.summary,
                "sentiment": sentiment,
                "score": f"{score:+d}",
                "tone": _tone(sentiment),
            }
        )

    dominant = counts.most_common(1)[0][0] if counts else "Neutral"
    summary = {
        "positive": str(counts["Positive"]),
        "neutral": str(counts["Neutral"]),
        "negative": str(counts["Negative"]),
        "dominant": dominant,
        "tone": _tone(dominant),
    }
    return rows, summary


def classify_sentiment(text: str) -> tuple[str, int]:
    """Classify text as Positive, Neutral, or Negative using keyword scoring."""
    words = {
        word.strip(".,:;!?()[]{}\"'").lower()
        for word in text.split()
    }
    score = len(words & POSITIVE_TERMS) - len(words & NEGATIVE_TERMS)
    if score > 0:
        return "Positive", score
    if score < 0:
        return "Negative", score
    return "Neutral", score


def _tone(sentiment: str) -> str:
    """Return visual tone for a sentiment label."""
    if sentiment == "Positive":
        return "positive"
    if sentiment == "Negative":
        return "negative"
    return "neutral"
