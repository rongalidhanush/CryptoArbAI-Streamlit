"""Account validation and persistence helpers for the Streamlit UI."""

from __future__ import annotations

from re import fullmatch

from sqlalchemy import or_, select

from database import get_session
from database.models import User


USERNAME_PATTERN = r"^[A-Za-z0-9_]{3,80}$"
PASSWORD_MIN_LENGTH = 8


def normalize_email(email: str) -> str:
    """Return a normalized email value for lookup and storage."""
    return email.strip().lower()


def validate_registration(
    username: str,
    email: str,
    password: str,
    confirm_password: str,
) -> list[str]:
    """Validate registration details before persisting a new account."""
    errors: list[str] = []
    username = username.strip()
    email = normalize_email(email)
    session = get_session()

    if not fullmatch(USERNAME_PATTERN, username):
        errors.append(
            "Username must be 3-80 characters and use letters, numbers, or underscores."
        )
    if "@" not in email or "." not in email.rsplit("@", maxsplit=1)[-1]:
        errors.append("Enter a valid email address.")
    if len(password) < PASSWORD_MIN_LENGTH:
        errors.append("Password must be at least 8 characters long.")
    if password != confirm_password:
        errors.append("Passwords do not match.")
    if session.scalar(select(User).where(User.username == username)):
        errors.append("Username is already registered.")
    if session.scalar(select(User).where(User.email == email)):
        errors.append("Email is already registered.")
    return errors


def create_user(username: str, email: str, password: str) -> User:
    """Create and persist a user using the original password hashing behavior."""
    user = User(username=username.strip(), email=normalize_email(email), password_hash="")
    user.set_password(password)
    session = get_session()
    session.add(user)
    session.commit()
    return user


def authenticate_user(identifier: str, password: str) -> User | None:
    """Return the matching user when credentials are valid."""
    normalized_identifier = normalize_email(identifier)
    session = get_session()
    user = session.scalar(
        select(User).where(
            or_(User.email == normalized_identifier, User.username == identifier.strip())
        )
    )
    return user if user and user.check_password(password) else None
