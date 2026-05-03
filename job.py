from __future__ import annotations

import logging
import random
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from config import load_settings
from db import SessionLocal
from instapaper import InstapaperClient, InstapaperError, RetryableInstapaperError
from models import Feed, ProcessedItem
from rss import FeedFetchError, FeedItem, fetch_feed_items

logger = logging.getLogger(__name__)
settings = load_settings()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)



# Only RetryableInstapaperError triggers a retry; plain InstapaperError propagates immediately.
def retry_call(func, *, attempts: int, base_delay: float, max_delay: float):
    delay = base_delay
    last_exc: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            return func()
        except RetryableInstapaperError as exc:
            last_exc = exc
            if attempt == attempts:
                raise
            sleep_for = min(max_delay, delay) * random.uniform(0.8, 1.2)
            time.sleep(sleep_for)
            delay *= 2

    assert last_exc is not None
    raise last_exc


def run_job() -> dict:
    stats = {
        "feeds_total": 0,
        "feeds_failed": 0,
        "items_seen": 0,
        "items_sent": 0,
        "items_skipped": 0,
        "items_failed": 0,
    }

    client = InstapaperClient(
        settings.instapaper_username,
        settings.instapaper_password,
        timeout_seconds=settings.instapaper_timeout_seconds,
    )

    retry_after = timedelta(seconds=settings.stale_pending_retry_after_seconds)
    # Captured once so all stale-window checks in this run use the same reference point.
    now = utcnow()

    with SessionLocal() as session:
        feeds = session.scalars(select(Feed).order_by(Feed.id)).all()
        stats["feeds_total"] = len(feeds)

        # Preload processed-item rows once; this app is small and single-user.
        processed_rows = session.scalars(select(ProcessedItem)).all()
        processed_by_key = {row.item_key: row for row in processed_rows}

        feed_items_by_feed_id: dict[int, dict[str, FeedItem]] = {}

        # Fetch all feeds first so a broken feed doesn't interrupt the send loop.
        for feed in feeds:
            try:
                items = fetch_feed_items(feed, settings.feed_fetch_timeout_seconds)
                feed_items_by_feed_id[feed.id] = {item.key: item for item in items}
            except FeedFetchError:
                logger.exception("Feed fetch failed: feed_id=%s url=%s", feed.id, feed.url)
                stats["feeds_failed"] += 1

        for feed in feeds:
            feed_items = feed_items_by_feed_id.get(feed.id, {})

            for key, item in feed_items.items():
                stats["items_seen"] += 1

                row = processed_by_key.get(key)

                # Already done.
                if row and row.processed_at is not None:
                    stats["items_skipped"] += 1
                    continue

                # Pending but not stale yet.
                if row and row.processed_at is None and (now - row.attempted_at) < retry_after:
                    stats["items_skipped"] += 1
                    continue

                # Claim row if needed, or refresh the retry timestamp.
                if row is None:
                    row = ProcessedItem(
                        feed_id=feed.id,
                        item_key=key,
                        title=item.title,
                        attempted_at=now,
                        processed_at=None,
                    )
                    session.add(row)
                    try:
                        session.commit()
                    except IntegrityError:
                        # Another process inserted the same item_key between our preload
                        # and this insert. Reload and re-apply the skip/retry logic.
                        session.rollback()
                        row = session.scalar(
                            select(ProcessedItem).where(ProcessedItem.item_key == key)
                        )
                        if row is None:
                            stats["items_skipped"] += 1
                            continue
                        processed_by_key[key] = row
                        if row.processed_at is not None:
                            stats["items_skipped"] += 1
                            continue
                        if (now - row.attempted_at) < retry_after:
                            stats["items_skipped"] += 1
                            continue
                        row.attempted_at = now
                        session.commit()
                else:
                    row.attempted_at = now
                    session.commit()

                processed_by_key[key] = row

                try:
                    retry_call(
                        lambda: client.add_bookmark(
                            url=item.url,
                            title=item.title,
                        ),
                        attempts=settings.instapaper_retry_attempts,
                        base_delay=settings.instapaper_retry_base_delay_seconds,
                        max_delay=settings.instapaper_retry_max_delay_seconds,
                    )
                    row.processed_at = utcnow()
                    session.commit()
                    stats["items_sent"] += 1
                except InstapaperError:
                    # Roll back the uncommitted `processed_at` mutation so the row
                    # stays pending (processed_at=NULL) and is retried after the stale window.
                    session.rollback()
                    logger.exception(
                        "Instapaper add failed: feed_id=%s item_key=%s url=%s",
                        feed.id,
                        key,
                        item.url,
                    )
                    stats["items_failed"] += 1

    return stats