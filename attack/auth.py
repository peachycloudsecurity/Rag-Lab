"""
Auth helpers. Intentionally vulnerable for OWASP demos:
- A02: Weak password hashing (MD5)
- A07: No rate limit, session handling issues
- A09: No security-relevant logging
- JWT access_token cookie: DEVNOTES_JWT_VERIFY_SIGNATURE defaults off (lab only)
"""
import hashlib
import os
from datetime import datetime, timedelta, timezone

import jwt

JWT_COOKIE_NAME = "access_token"
JWT_TTL_HOURS = 24


def jwt_verify_signature_enabled():
    """When false (default), tokens decode without signature check (intentional lab weakness)."""
    v = os.environ.get("DEVNOTES_JWT_VERIFY_SIGNATURE", "0").strip().lower()
    return v in ("1", "true", "yes", "on")


def issue_access_token(user_id, secret, username):
    """HS256 JWT; sub is user id, username for jwt.io visibility (and lab trust bug when verify is off)."""
    exp = datetime.now(timezone.utc) + timedelta(hours=JWT_TTL_HOURS)
    payload = {
        "sub": str(int(user_id)),
        "username": (username or "").strip(),
        "exp": exp,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_access_token(token, secret, verify_signature):
    """
    Return claims dict or None.
    When verify_signature is False: accepts HS256 and alg none (lab only).
    """
    if not token or not isinstance(token, str):
        return None
    try:
        if verify_signature:
            return jwt.decode(token, secret, algorithms=["HS256"])
        return jwt.decode(
            token,
            options={"verify_signature": False},
            algorithms=["HS256", "none"],
        )
    except (jwt.PyJWTError, ValueError, TypeError):
        return None

# A02 Cryptographic Failures: MD5 is broken, no salt
def hash_password(plain):
    return hashlib.md5(plain.encode()).hexdigest()


def check_password(plain, stored_hash):
    return hash_password(plain) == stored_hash


def ensure_admin_user():
    """Create default admin and alice for demo if missing."""
    import db as db_mod
    import os

    admin_username = os.environ.get("ADMIN_USERNAME", "admin")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@devnotes.local")

    conn = db_mod.get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE username = ?", (admin_username,))
    if cur.fetchone() is None:
        cur.execute(
            "INSERT INTO users (username, password_hash, email, is_admin) VALUES (?, ?, ?, 1)",
            (admin_username, hash_password(admin_password), admin_email),
        )
        conn.commit()

    cur.execute("SELECT id FROM users WHERE username = ?", ("alice",))
    if cur.fetchone() is None:
        cur.execute(
            "INSERT INTO users (username, password_hash, email, is_admin) VALUES (?, ?, ?, 0)",
            ("alice", hash_password("alice123"), "alice@devnotes.local"),
        )
        conn.commit()

    conn.close()
    print(f"[*] Demo credentials — admin: {admin_username} / {admin_password} | attacker: alice / alice123", flush=True)
