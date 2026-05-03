from __future__ import annotations

import re
from dataclasses import dataclass

import feedparser
import requests


@dataclass(frozen=True)
class FeedItem:
    key: str
    url: str
    title: str | None


class FeedFetchError(RuntimeError):
    pass


def fetch_feed_items(feed, timeout_seconds: int) -> list[FeedItem]:
    headers = {"User-Agent": "rss-to-instapaper/1.0"}
    try:
        response = requests.get(feed.url, headers=headers, timeout=timeout_seconds)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise FeedFetchError(f"Failed to fetch feed {feed.url}: {exc}") from exc

    parsed = feedparser.parse(response.content)

    # Invalid regex on one feed should not kill the whole job.
    regex = None
    if feed.regex_filter:
        try:
            regex = re.compile(feed.regex_filter)
        except re.error as exc:
            raise FeedFetchError(f"Invalid regex for feed {feed.url}: {exc}") from exc

    items: list[FeedItem] = []
    for entry in parsed.entries:
        title = (entry.get("title") or "").strip()
        if regex and not regex.search(title):
            continue

        url = (entry.get("link") or "").strip()
        if not url:
            continue

        key = (entry.get("id") or entry.get("guid") or url).strip()
        if not key:
            continue

        items.append(FeedItem(key=key, url=url, title=title or None))

    return items