"""Fetches the latest news from RSS feeds or a news API."""

import feedparser
import requests
import yaml
from dataclasses import dataclass
from pathlib import Path


@dataclass
class NewsItem:
    title: str
    summary: str
    link: str
    source: str


def load_config() -> dict:
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def fetch_from_rss(feed_url: str, source_name: str, max_items: int = 5) -> list[NewsItem]:
    feed = feedparser.parse(feed_url)
    items = []
    for entry in feed.entries[:max_items]:
        summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
        items.append(NewsItem(
            title=entry.get("title", ""),
            summary=summary[:500],
            link=entry.get("link", ""),
            source=source_name,
        ))
    return items


def fetch_news(max_items_per_feed: int = 5) -> list[NewsItem]:
    config = load_config()
    all_items: list[NewsItem] = []

    for feed in config.get("rss_feeds", []):
        try:
            items = fetch_from_rss(feed["url"], feed["name"], max_items_per_feed)
            all_items.extend(items)
        except Exception as exc:
            print(f"[news_fetcher] Failed to fetch {feed['name']}: {exc}")

    return all_items
