"""Role-based dashboards.

After login, the user is sent here.
We show different content based on role.
"""

import streamlit as st

from backend.middleware.role_guard import require_authentication, require_role
from backend.user.user_service import (
    change_user_role,
    get_all_users,
    get_user_summaries,
    set_account_status,
)


def render_dashboard() -> None:
    """Main dashboard router."""

    if not require_authentication():
        return

    name = st.session_state.get("user_name")
    role = st.session_state.get("user_role")

    st.subheader("Dashboard")
    st.write(f"Welcome, **{name}**")
    st.write(f"Your role: **{role}**")

    if role == "Admin":
        _render_admin_dashboard()
    elif role == "Planner":
        _render_planner_dashboard()
    elif role == "Viewer":
        _render_viewer_dashboard()
    else:
        # This should not happen if roles are validated.
        st.error("Unknown role. Please contact an administrator.")


def _render_admin_dashboard() -> None:
    st.markdown("### Admin Dashboard")
    st.caption("Admin tools: manage users and monitor role distribution.")

    if not require_role(["Admin"]):
        return

    counts, distribution = get_user_summaries()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total users", counts.get("total", 0))
    col2.metric("Active users", counts.get("active", 0))
    col3.metric("Inactive users", counts.get("inactive", 0))

    st.subheader("Role distribution")
    if distribution:
        dist_rows = []
        for role, count in distribution.items():
            dist_rows.append({"role": role, "count": count})
        st.dataframe(dist_rows, use_container_width=True)
    else:
        st.info("No users found yet.")

    st.divider()
    st.subheader("User management")
    st.caption("Change roles or disable/enable accounts. Disabled accounts cannot login.")

    users = get_all_users()
    if not users:
        st.info("No users found.")
        return

    # Display users in a clean table.
    user_rows = []
    for u in users:
        user_rows.append(
            {
                "name": u.get("name"),
                "email": u.get("email"),
                "role": u.get("role"),
                "is_active": u.get("is_active", True),
                "created_at": u.get("created_at"),
            }
        )

    st.dataframe(user_rows, use_container_width=True)

    emails = [u.get("email") for u in users if u.get("email")]
    selected_email = st.selectbox("Select user", emails)

    selected_user = next((u for u in users if u.get("email") == selected_email), None)
    if selected_user is None:
        st.error("Selected user not found.")
        return

    st.markdown("#### Change role")
    new_role = st.selectbox("New role", ["Admin", "Planner", "Viewer"], index=["Admin", "Planner", "Viewer"].index(selected_user.get("role")))
    if st.button("Save role"):
        ok, msg = change_user_role(selected_email, new_role)
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

    st.markdown("#### Enable / Disable account")
    current_active = bool(selected_user.get("is_active", True))
    desired_active = st.toggle("Account is active", value=current_active)
    if st.button("Save account status"):
        ok, msg = set_account_status(selected_email, desired_active)
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)


def _render_planner_dashboard() -> None:
    st.markdown("### Planner Dashboard")
    st.info("You can add and edit operational data (Plants, Demands, Transport, Inventory Policies).")
    st.write("Use the left sidebar to open modules.")


def _render_viewer_dashboard() -> None:
    st.markdown("### Viewer Dashboard")
    st.info("Read-only access. You can view tables and reports, but you cannot edit or delete data.")
    st.write("Use the left sidebar to open modules.")
