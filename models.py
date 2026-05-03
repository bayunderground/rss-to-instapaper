from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Feed(Base):
    __tablename__ = "feeds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    regex_filter: Mapped[str | None] = mapped_column(Text, nullable=True)

    processed_items: Mapped[list["ProcessedItem"]] = relationship(
        back_populates="feed",
        cascade="all, delete-orphan",
    )


class ProcessedItem(Base):
    __tablename__ = "processed_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    feed_id: Mapped[int] = mapped_column(ForeignKey("feeds.id"), nullable=False, index=True)

    # Store guid if present, else fallback to link.
    item_key: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Lifecycle: attempted_at is set when the row is first claimed; processed_at is
    # set only on confirmed success. processed_at=NULL means pending or failed —
    # the row will be retried once attempted_at is older than the stale window (2 h).
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    feed: Mapped["Feed"] = relationship(back_populates="processed_items")