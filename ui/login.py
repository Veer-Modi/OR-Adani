"""Login page UI (Streamlit).

This is the user interface only.
It calls backend services to do the real work.
"""

import streamlit as st

from backend.auth.auth_service import login
from backend.auth.session import ensure_session_defaults, login_user
from backend.core.logger import audit_log


def render_login_page() -> None:
    """Show login form."""

    ensure_session_defaults()

    st.subheader("Login")
    st.caption("Enter your email and password to login.")

    with st.form("login_form"):
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password")

        submitted = st.form_submit_button("Login")

    if submitted:
        success, message, user = login(email=email, password=password)

        if not success:
            audit_log(
                event_type="login_failed",
                actor_email=(email or "").strip().lower(),
                details={"reason": message},
            )
            st.error(message)
            return

        # Save user info to session (user is now logged in).
        login_user(user)
        audit_log(
            event_type="login_success",
            actor_email=str(user.get("email") or ""),
            details={"role": str(user.get("role") or "")},
        )
        st.success(message)
        st.info("Open the Dashboard from the left sidebar.")
