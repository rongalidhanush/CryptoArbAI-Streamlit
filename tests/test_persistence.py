"""Persistence tests for account-owned data models."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from database import Base
from database.models import User, Watchlist


class PersistenceTests(unittest.TestCase):
    """Verify data remains available from a fresh database session."""

    def test_user_and_watchlist_persist_across_sessions(self) -> None:
        """Persist an account/watchlist then retrieve it through a new session."""
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "persistence.db"
            engine = create_engine(f"sqlite:///{database_path.as_posix()}")
            Base.metadata.create_all(engine)
            first_session = Session(engine)
            user = User(username="persistent_user", email="user@example.com", password_hash="")
            user.set_password("secure-password")
            first_session.add(user)
            first_session.commit()
            first_session.add(Watchlist(user_id=user.id, coin="BTC"))
            first_session.commit()
            first_session.close()

            second_session = Session(engine)
            loaded_user = second_session.scalar(
                select(User).where(User.email == "user@example.com")
            )
            saved_watchlist = list(
                second_session.scalars(
                    select(Watchlist).where(Watchlist.user_id == loaded_user.id)
                )
            )
            self.assertTrue(loaded_user.check_password("secure-password"))
            self.assertEqual([item.coin for item in saved_watchlist], ["BTC"])
            second_session.close()
            engine.dispose()
