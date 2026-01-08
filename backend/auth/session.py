"""Session helpers.

Streamlit does not provide classic server sessions like Flask/Django.
Instead, we use st.session_state, which is per-user in the browser session.

We store:
- authenticated: bool
- user_id: str (MongoDB ObjectId as string)
- user_name: str
- user_email: str
- user_role: str
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import streamlit as st

from backend.core.config_manager import get_config


def ensure_session_defaults() -> None:
    """Initialize session keys if they do not exist yet."""

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if "user_id" not in st.session_state:
        st.session_state.user_id = None

    if "user_name" not in st.session_state:
        st.session_state.user_name = None

    if "user_email" not in st.session_state:
        st.session_state.user_email = None

    if "user_role" not in st.session_state:
        st.session_state.user_role = None

    # Phase 6: session timeout support.
    # We store last_activity as an ISO timestamp.
    if "last_activity" not in st.session_state:
        st.session_state.last_activity = None


def is_authenticated() -> bool:
    """Return True if the user is logged in."""

    if not bool(st.session_state.get("authenticated")):
        return False

    # Enforce timeout.
    cfg = get_config()
    last = st.session_state.get("last_activity")
    if last:
        try:
            last_dt = datetime.fromisoformat(str(last))
        except Exception:
            last_dt = None

        if last_dt is not None:
            now = datetime.now(timezone.utc)
            if now - last_dt > timedelta(minutes=int(cfg.session_timeout_minutes)):
                logout_user()
                return False

    # Update activity timestamp on access.
    touch_session_activity()
    return True


def touch_session_activity() -> None:
    """Update the session's last activity timestamp."""

    st.session_state.last_activity = datetime.now(timezone.utc).isoformat()


def login_user(user_doc) -> None:
    """Save user details into session state."""

    st.session_state.authenticated = True
    st.session_state.user_id = str(user_doc.get("_id"))
    st.session_state.user_name = user_doc.get("name")
    st.session_state.user_email = user_doc.get("email")
    st.session_state.user_role = user_doc.get("role")

    touch_session_activity()


def logout_user() -> None:
    """Clear authentication from session state."""

    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.user_email = None
    st.session_state.user_role = None
    st.session_state.last_activity = None
