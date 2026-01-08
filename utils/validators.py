"""Input validation helpers.

Validation is a security feature:
- It prevents bad data from entering your database.
- It reduces unexpected errors.

We validate:
- name
- email
- password
- role
"""

from __future__ import annotations

import re
from typing import Tuple


_ALLOWED_ROLES = {"Admin", "Planner", "Viewer"}


def validate_name(name: str) -> Tuple[bool, str]:
    """Validate user name."""

    cleaned = (name or "").strip()

    if len(cleaned) < 2:
        return False, "Name must be at least 2 characters."

    if len(cleaned) > 60:
        return False, "Name is too long (max 60 characters)."

    return True, ""


def validate_email(email: str) -> Tuple[bool, str]:
    """Validate email format (simple, beginner-friendly)."""

    cleaned = (email or "").strip().lower()

    # Simple regex for an email-like string.
    # This is not perfect, but works for common cases.
    pattern = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"

    if not re.match(pattern, cleaned):
        return False, "Please enter a valid email address."

    if len(cleaned) > 254:
        return False, "Email is too long."

    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """Validate password strength.

    For a foundation project we enforce:
- Minimum length
- Must contain letters and numbers
    """

    value = password or ""

    if len(value) < 8:
        return False, "Password must be at least 8 characters."

    if len(value) > 128:
        return False, "Password is too long (max 128 characters)."

    has_letter = any(ch.isalpha() for ch in value)
    has_number = any(ch.isdigit() for ch in value)

    if not (has_letter and has_number):
        return False, "Password must contain at least 1 letter and 1 number."

    return True, ""


def validate_role(role: str) -> Tuple[bool, str]:
    """Validate that role is one of the allowed roles."""

    value = (role or "").strip()

    if value not in _ALLOWED_ROLES:
        return False, "Invalid role selected."

    return True, ""
