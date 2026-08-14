"""Crypto news fetching utilities."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from html import unescape
from xml.etree import ElementTree

import requests

from config import get_settings


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class NewsArticle:
    """Normalized crypto news article."""

    title: str
    link: str
    source: str
    published_at: str
    summary: str


def fetch_latest_news(limit: int = 8) -> list[NewsArticle]:
    """Fetch latest crypto news from configured RSS feeds."""
    articles: list[NewsArticle] = []
    settings = get_settings()
    for feed_url in settings.news_feeds:
        try:
            articles.extend(_fetch_feed(feed_url))
        except requests.RequestException as exc:
            LOGGER.info("News feed fetch failed for %s: %s", feed_url, exc)
        except ElementTree.ParseError as exc:
            LOGGER.info("News feed parse failed for %s: %s", feed_url, exc)

    return articles[:limit]


def _fetch_feed(feed_url: str) -> list[NewsArticle]:
    """Fetch and parse one RSS feed."""
    response = requests.get(
        feed_url,
        timeout=get_settings().news_timeout_seconds,
        headers={"User-Agent": "CryptoArbAI/1.0"},
    )
    response.raise_for_status()
    root = ElementTree.fromstring(response.content)
    source = _text(root.find("./channel/title")) or "Crypto News"
    articles: list[NewsArticle] = []

    for item in root.findall("./channel/item")[:8]:
        title = _clean_text(_text(item.find("title")))
        link = _text(item.find("link"))
        summary = _clean_text(
            _text(item.find("description")) or _text(item.find("summary"))
        )
        published = _format_published(_text(item.find("pubDate")))
        if title and link:
            articles.append(
                NewsArticle(
                    title=title,
                    link=link,
                    source=source,
                    published_at=published,
                    summary=summary,
                )
            )
    return articles


def _text(element: ElementTree.Element | None) -> str:
    """Return stripped text from an XML element."""
    return element.text.strip() if element is not None and element.text else ""


def _clean_text(value: str) -> str:
    """Remove simple RSS/HTML noise from text."""
    cleaned = unescape(value)
    for token in ("<p>", "</p>", "<br>", "<br/>", "<br />"):
        cleaned = cleaned.replace(token, " ")
    return " ".join(cleaned.split())


def _format_published(value: str) -> str:
    """Format RSS published date safely."""
    if not value:
        return "Unknown"
    try:
        return parsedate_to_datetime(value).strftime("%Y-%m-%d %H:%M UTC")
    except (TypeError, ValueError):
        return value

