from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

import models


COOKIE_NAME = "brafoot_session"
SESSION_LIFETIME = timedelta(days=180)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def find_browser_session(
    session: Session, token: str | None
) -> models.BrowserSession | None:
    if not token:
        return None
    return (
        session.query(models.BrowserSession)
        .filter_by(token_hash=hash_session_token(token))
        .filter(models.BrowserSession.expires_at > datetime.now(timezone.utc))
        .one_or_none()
    )


def create_browser_session(session: Session) -> tuple[models.BrowserSession, str]:
    token = secrets.token_urlsafe(32)
    browser_session = models.BrowserSession(
        token_hash=hash_session_token(token),
        expires_at=datetime.now(timezone.utc) + SESSION_LIFETIME,
    )
    session.add(browser_session)
    session.flush()
    return browser_session, token
