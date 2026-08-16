"""SQLAlchemy models retained from the original CryptoArb AI application."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from database import Base


class User(Base):
    """Registered application user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    portfolios: Mapped[list[Portfolio]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    watchlist_items: Mapped[list[Watchlist]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    trade_history: Mapped[list[TradeHistory]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def set_password(self, password: str) -> None:
        """Hash and store a user password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Return whether the provided password matches the stored hash."""
        return check_password_hash(self.password_hash, password)


class Portfolio(Base):
    """A user's cryptocurrency holding."""

    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    coin: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    buy_price: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    user: Mapped[User] = relationship(back_populates="portfolios")


class Watchlist(Base):
    """A coin tracked by a user."""

    __tablename__ = "watchlist"
    __table_args__ = (
        UniqueConstraint("user_id", "coin", name="uq_watchlist_user_coin"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    coin: Mapped[str] = mapped_column(String(20), nullable=False)
    user: Mapped[User] = relationship(back_populates="watchlist_items")


class TradeHistory(Base):
    """Historical arbitrage trade saved for a user."""

    __tablename__ = "trade_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    coin: Mapped[str] = mapped_column(String(20), nullable=False)
    buy_exchange: Mapped[str] = mapped_column(String(80), nullable=False)
    sell_exchange: Mapped[str] = mapped_column(String(80), nullable=False)
    gross_profit: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    fees: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    net_profit: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    user: Mapped[User] = relationship(back_populates="trade_history")
