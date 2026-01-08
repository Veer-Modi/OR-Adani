"""Authentication service.

This file contains the "business logic" for:
- signup
- login

It talks to:
- validators (to validate input)
- user_repository (to read/write the database)
- password (to hash and verify passwords)

It does NOT contain Streamlit UI code.
"""

from __future__ import annotations

from typing import Tuple

from backend.auth.password import hash_password, verify_password
from backend.database.user_repository import create_user, find_user_by_email
from utils.validators import (
    validate_email,
    validate_name,
    validate_password,
    validate_role,
)


def signup(name: str, email: str, password: str, role: str) -> Tuple[bool, str]:
    """Create a new user.

    Returns:
- (True, message) on success
- (False, error_message) on failure
    """

    ok, msg = validate_name(name)
    if not ok:
        return False, msg

    ok, msg = validate_email(email)
    if not ok:
        return False, msg

    ok, msg = validate_password(password)
    if not ok:
        return False, msg

    ok, msg = validate_role(role)
    if not ok:
        return False, msg

    normalized_email = email.strip().lower()

    password_hash = hash_password(password)

    created = create_user(
        name=name.strip(),
        email=normalized_email,
        password_hash=password_hash,
        role=role.strip(),
    )

    if not created:
        return False, "An account with this email already exists."

    return True, "Account created successfully. You can now login."


def login(email: str, password: str) -> Tuple[bool, str, object]:
    """Login a user.

    Returns:
- (True, message, user_doc) on success
- (False, error_message, None) on failure
    """

    ok, msg = validate_email(email)
    if not ok:
        return False, msg, None

    if not password:
        return False, "Password is required.", None

    normalized_email = email.strip().lower()

    user = find_user_by_email(normalized_email)
    if user is None:
        # Do not reveal whether the email exists (small security best practice).
        return False, "Invalid email or password.", None

    # If a user is disabled by Admin, they should not be allowed to login.
    # We default missing values to True to keep older accounts working.
    if user.get("is_active", True) is False:
        return False, "Your account is disabled. Please contact an administrator.", None

    if not verify_password(password, user.get("password_hash", "")):
        return False, "Invalid email or password.", None

    return True, "Login successful.", user
