"""Database engine and session management for CryptoArb AI."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, scoped_session, sessionmaker

from config import get_settings


class Base(DeclarativeBase):
    """Base class for the application's SQLAlchemy models."""


_engine = None
_session_factory: scoped_session[Session] | None = None


def initialize_database() -> None:
    """Create the configured database and all application tables once."""
    global _engine, _session_factory
    if _engine is not None:
        return

    _engine = create_engine(get_settings().database_url, pool_pre_ping=True)
    _session_factory = scoped_session(sessionmaker(bind=_engine, expire_on_commit=False))
    from database import models  # noqa: F401

    Base.metadata.create_all(_engine)


def get_session() -> Session:
    """Return the current thread-local database session."""
    initialize_database()
    assert _session_factory is not None
    return _session_factory()


def remove_session() -> None:
    """Release the current thread-local database session after a rerun."""
    if _session_factory is not None:
        _session_factory.remove()
