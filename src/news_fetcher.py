"""Fetches the latest news from RSS feeds and filters by user topic."""

import feedparser
import requests
import yaml
from dataclasses import dataclass
from pathlib import Path

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; PodcastBot/1.0; +https://github.com/TolsmA01/podcastAINews)"
    )
}
_TIMEOUT = 15  # seconds per feed


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
    # Guard against YAML returning a non-int (root cause of the "slice indices" TypeError)
    max_items = int(max_items)

    # Let feedparser fetch the URL itself with custom headers — it handles redirects
    # and charset detection better than passing raw bytes from requests.
    feed = feedparser.parse(feed_url, request_headers=_HEADERS)

    # If feedparser couldn't fetch (no network in some environments), fall back to requests
    if not feed.entries and feed.get("bozo"):
        response = requests.get(feed_url, headers=_HEADERS, timeout=_TIMEOUT, allow_redirects=True)
        response.raise_for_status()
        feed = feedparser.parse(response.text)

    items = []
    for entry in feed.entries[:max_items]:
        summary = entry.get("summary", "") or entry.get("description", "")
        if not isinstance(summary, str):
            summary = str(summary)
        items.append(NewsItem(
            title=str(entry.get("title", "")),
            summary=summary[:500],
            link=str(entry.get("link", "")),
            source=source_name,
        ))
    return items


def _matches_topic(item: NewsItem, keywords: list[str]) -> bool:
    text = (item.title + " " + item.summary).lower()
    return any(kw in text for kw in keywords)


def fetch_news(topic: str, max_items_per_feed: int | None = None) -> list[NewsItem]:
    config = load_config()
    # Cast to int so a YAML string value can never reach fetch_from_rss as a non-int
    limit = int(max_items_per_feed or config.get("max_items_per_feed", 3))
    # Include short words like "AI", "ML" — only skip single-char words
    keywords = [w.lower() for w in topic.split() if len(w) > 1]

    all_items: list[NewsItem] = []

    for feed in config.get("rss_feeds", []):
        try:
            items = fetch_from_rss(feed["url"], feed["name"], max_items=limit)
            all_items.extend(items)
            print(f"[news_fetcher] OK  {feed['name']} ({len(items)} articles)")
        except Exception as exc:
            # Include exception type so it's obvious whether it's a network error,
            # parse error, HTTP error, etc.
            print(f"[news_fetcher] SKIP {feed['name']}: {type(exc).__name__}: {exc}")

    if not all_items:
        print("[news_fetcher] No articles fetched — check internet access and RSS URLs.")
        return []

    # Filter by topic keywords; fall back to all items if too few matches
    if keywords:
        filtered = [i for i in all_items if _matches_topic(i, keywords)]
        print(f"[news_fetcher] {len(filtered)}/{len(all_items)} articles match topic '{topic}'")
        if len(filtered) >= 3:
            all_items = filtered

    # Cap at 2 articles per source so no single outlet dominates
    source_counts: dict[str, int] = {}
    balanced: list[NewsItem] = []
    for item in all_items:
        count = source_counts.get(item.source, 0)
        if count < 2:
            balanced.append(item)
            source_counts[item.source] = count + 1

    return balanced
