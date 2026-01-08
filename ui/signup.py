"""Signup page UI (Streamlit).

This is the user interface only.
It calls backend services to do the real work.
"""

import streamlit as st

from backend.auth.auth_service import signup


def render_signup_page() -> None:
    """Show signup form."""

    st.subheader("Signup")
    st.caption("Create a new account.")

    with st.form("signup_form"):
        name = st.text_input("Name", placeholder="Your full name")
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password")

        role = st.selectbox("Select Role", ["Admin", "Planner", "Viewer"])

        submitted = st.form_submit_button("Create Account")

    if submitted:
        success, message = signup(name=name, email=email, password=password, role=role)

        if not success:
            st.error(message)
            return

        st.success(message)
        st.info("Go to Login from the left sidebar.")
