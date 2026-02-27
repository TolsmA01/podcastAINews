"""Fetches the latest news from RSS feeds and filters by user topic."""

import feedparser
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


def fetch_from_rss(feed_url: str, source_name: str, max_items: int = 3) -> list[NewsItem]:
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


def _matches_topic(item: NewsItem, keywords: list[str]) -> bool:
    """Return True if the item title or summary contains any topic keyword."""
    text = (item.title + " " + item.summary).lower()
    return any(kw in text for kw in keywords)


def fetch_news(topic: str, max_items_per_feed: int | None = None) -> list[NewsItem]:
    config = load_config()
    limit = max_items_per_feed or config.get("max_items_per_feed", 3)
    keywords = [w.lower() for w in topic.split() if len(w) > 2]

    all_items: list[NewsItem] = []

    for feed in config.get("rss_feeds", []):
        try:
            items = fetch_from_rss(feed["url"], feed["name"], max_items=limit)
            all_items.extend(items)
        except Exception as exc:
            print(f"[news_fetcher] Failed to fetch {feed['name']}: {exc}")

    # Filter by topic keywords when we have enough matches
    if keywords:
        filtered = [i for i in all_items if _matches_topic(i, keywords)]
        # Fall back to all items if filtering is too aggressive
        if len(filtered) >= 5:
            all_items = filtered

    # Cap at 2 items per source so no single outlet dominates
    source_counts: dict[str, int] = {}
    balanced: list[NewsItem] = []
    for item in all_items:
        count = source_counts.get(item.source, 0)
        if count < 2:
            balanced.append(item)
            source_counts[item.source] = count + 1

    return balanced
