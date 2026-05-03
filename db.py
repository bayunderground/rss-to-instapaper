from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import load_settings

settings = load_settings()

# pool_pre_ping issues a cheap SELECT before each connection checkout to detect
# stale connections — important for Neon, which drops idle connections aggressively.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)


# session_scope() is not used — job.py uses `with SessionLocal() as session` directly,
# which is equivalent (SQLAlchemy 2.0 Session supports the context manager protocol).
@contextmanager
def session_scope():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()