"""Password hashing and verification.

Security rule:
- NEVER store plain-text passwords.
- Always store a salted hash.

We use bcrypt:
- It automatically generates a salt.
- It is designed to be slow (makes brute-force harder).
"""

from __future__ import annotations

import bcrypt


def hash_password(plain_password: str) -> str:
    """Hash a password and return a UTF-8 string for storage."""

    password_bytes = plain_password.encode("utf-8")

    # gensalt() creates a random salt.
    salt = bcrypt.gensalt(rounds=12)

    hashed = bcrypt.hashpw(password_bytes, salt)

    # Store as string in DB.
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a password against a stored hash."""

    plain_bytes = plain_password.encode("utf-8")
    hash_bytes = password_hash.encode("utf-8")

    return bcrypt.checkpw(plain_bytes, hash_bytes)
