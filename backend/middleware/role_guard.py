"""Role-based access checks.

We use this to block unauthorized users from seeing pages.

Rules:
- Not logged in -> blocked
- Logged in but wrong role -> blocked
"""

from __future__ import annotations

from typing import Iterable

import streamlit as st

from backend.auth.session import is_authenticated


def require_authentication() -> bool:
    """Return True if logged in, else show a message and return False."""

    if not is_authenticated():
        st.error("You must login to access this page. Your session may have expired.")
        return False

    return True


def require_role(allowed_roles: Iterable[str]) -> bool:
    """Return True if current user role is allowed, else show a message."""

    if not require_authentication():
        return False

    user_role = st.session_state.get("user_role")

    if user_role not in set(allowed_roles):
        st.error("You are not authorized to view this page.")
        return False

    return True
