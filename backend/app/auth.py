"""Login, signed bearer tokens and role checks.

Roles: ADJUSTER (works claims, approves up to a limit), SUPERVISOR (no limit, decides escalated
claims, ingests policy wordings), AUDITOR (read-only). Passwords use PBKDF2-SHA256; tokens are
HMAC-SHA256 signed and expire.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import secrets
import threading
import time
from collections import deque
from decimal import Decimal

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .models import User

log = logging.getLogger("claimsense.auth")


class LoginThrottle:
    """In-process limit on failed sign-ins per (client address, username). One app instance holds the state;
    a multi-instance deployment would move this to a shared store."""

    def __init__(self) -> None:
        self._fails: dict[str, deque] = {}
        self._lock = threading.Lock()

    def _recent(self, key: str, now: float) -> deque:
        q = self._fails.setdefault(key, deque())
        while q and now - q[0] > settings.login_window_seconds:
            q.popleft()
        return q

    def retry_after(self, key: str) -> int:
        """Seconds until the key may try again, or 0 when it is not locked."""
        now = time.monotonic()
        with self._lock:
            q = self._recent(key, now)
            if len(q) < settings.login_max_failures:
                return 0
            return max(1, int(settings.login_window_seconds - (now - q[0])) + 1)

    def fail(self, key: str) -> None:
        with self._lock:
            self._recent(key, time.monotonic()).append(time.monotonic())

    def reset(self, key: str | None = None) -> None:
        with self._lock:
            if key is None:
                self._fails.clear()
            else:
                self._fails.pop(key, None)


throttle = LoginThrottle()
_secret = settings.auth_secret.encode() or secrets.token_bytes(32)
if not settings.auth_secret:
    log.warning("AUTH_SECRET not set: using a random per-process signing key")

WRITE_ROLES = ("ADJUSTER", "SUPERVISOR")
DEMO_USERS = [
    ("adjuster", "Adjuster A. Rao", "ADJUSTER", Decimal("200000")),
    ("supervisor", "Supervisor S. Menon", "SUPERVISOR", None),
    ("auditor", "Auditor K. Das", "AUDITOR", None),
]


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return f"pbkdf2_sha256$200000${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iters, salt, digest = stored.split("$")
        test = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(iters))
        return hmac.compare_digest(test.hex(), digest)
    except ValueError:
        return False


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def issue_token(user: User) -> str:
    payload = _b64(json.dumps({"sub": user.username, "role": user.role,
                               "exp": int(time.time()) + settings.token_ttl_hours * 3600}).encode())
    sig = _b64(hmac.new(_secret, payload.encode(), hashlib.sha256).digest())
    return f"{payload}.{sig}"


def read_token(token: str) -> dict | None:
    try:
        payload, sig = token.split(".")
    except ValueError:
        return None
    expected = _b64(hmac.new(_secret, payload.encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(sig, expected):
        return None
    data = json.loads(_unb64(payload))
    return data if data.get("exp", 0) > time.time() else None


def seed_users(db: Session) -> None:
    for username, name, role, limit in DEMO_USERS:
        if not db.query(User).filter_by(username=username).first():
            db.add(User(username=username, display_name=name, role=role, approval_limit=limit,
                        password_hash=hash_password(settings.demo_password)))
    db.commit()


def user_view(u: User) -> dict:
    return {"username": u.username, "display_name": u.display_name, "role": u.role,
            "approval_limit": str(u.approval_limit) if u.approval_limit is not None else None,
            "can_write": u.role in WRITE_ROLES, "is_supervisor": u.role == "SUPERVISOR"}


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    header = request.headers.get("authorization", "")
    data = read_token(header[7:]) if header.lower().startswith("bearer ") else None
    user = db.query(User).filter_by(username=data["sub"], active=True).first() if data else None
    if user is None:
        raise HTTPException(401, "Sign in to continue")
    return user


def writer(user: User = Depends(current_user)) -> User:
    if user.role not in WRITE_ROLES:
        raise HTTPException(403, "Your role is read-only")
    return user


def supervisor(user: User = Depends(current_user)) -> User:
    if user.role != "SUPERVISOR":
        raise HTTPException(403, "Only a supervisor can do this")
    return user
