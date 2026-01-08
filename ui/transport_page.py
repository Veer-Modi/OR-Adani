"""Transport Configuration page (Streamlit UI).

What this page does:
- Shows all transport routes
- Lets authorized users add/edit/delete routes
- Lets Admin enable/disable a route

Role access:
- Admin: full access
- Planner: add + edit
- Viewer: view only

Data flow:
UI -> backend.transport.transport_service -> backend.transport.transport_repository -> MongoDB
"""

from __future__ import annotations

import streamlit as st

from backend.middleware.role_guard import require_authentication, require_role
from backend.plant.plant_service import get_all_plants
from backend.transport.transport_service import (
    add_route,
    edit_route,
    get_all_routes,
    remove_route,
    toggle_route_enabled,
)


def render_transport_page(role: str) -> None:
    if not require_authentication():
        return

    st.header("Transport Configuration")
    st.caption("Define routes between plants with mode, costs, and capacity.")

    plants = get_all_plants(include_inactive=False)
    plant_options = {p.get("name"): str(p.get("_id")) for p in plants}

    if len(plant_options) < 2:
        st.warning("Please add at least two plants before creating routes.")
        return

    routes = get_all_routes(include_disabled=True)

    if routes:
        rows = []
        for r in routes:
            rows.append(
                {
                    "id": str(r.get("_id")),
                    "from": r.get("from_plant_name"),
                    "to": r.get("to_plant_name"),
                    "mode": r.get("transport_mode"),
                    "cost_per_trip": r.get("cost_per_trip"),
                    "capacity_per_trip": r.get("capacity_per_trip"),
                    "sbq": r.get("sbq"),
                    "is_enabled": r.get("is_enabled", True),
                }
            )

        st.subheader("All Routes")
        st.dataframe(rows, use_container_width=True)
    else:
        st.info("No transport routes found yet.")

    if role == "Viewer":
        st.warning("Viewer role: read-only access.")
        return

    st.divider()
    st.subheader("Add Route")

    with st.form("add_route_form"):
        from_plant_name = st.selectbox("From plant", list(plant_options.keys()))
        to_plant_name = st.selectbox("To plant", list(plant_options.keys()))
        mode = st.selectbox("Transport mode", ["Truck", "Train", "Ship"])

        cost = st.number_input("Cost per trip", min_value=0.0, value=0.0, step=1.0)
        capacity = st.number_input("Capacity per trip", min_value=0.0, value=0.0, step=1.0)
        sbq = st.number_input("Minimum shipment batch (SBQ)", min_value=0.0, value=0.0, step=1.0)

        submitted = st.form_submit_button("Create Route")

    if submitted:
        ok, msg = add_route(
            {
                "from_plant_id": plant_options[from_plant_name],
                "to_plant_id": plant_options[to_plant_name],
                "transport_mode": mode,
                "cost_per_trip": cost,
                "capacity_per_trip": capacity,
                "sbq": sbq,
            }
        )

        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

    if not routes:
        return

    st.divider()
    st.subheader("Edit / Delete Route")

    route_options = {
        f"{r.get('from_plant_name')} -> {r.get('to_plant_name')} | {r.get('transport_mode')}": str(r.get("_id"))
        for r in routes
    }

    selected_label = st.selectbox("Select route", list(route_options.keys()))
    selected_id = route_options[selected_label]

    selected_doc = next((r for r in routes if str(r.get("_id")) == selected_id), None)
    if selected_doc is None:
        st.error("Route not found.")
        return

    from_names = list(plant_options.keys())
    to_names = list(plant_options.keys())

    with st.form("edit_route_form"):
        edit_from_name = st.selectbox(
            "From plant",
            from_names,
            index=from_names.index(selected_doc.get("from_plant_name")),
        )
        edit_to_name = st.selectbox(
            "To plant",
            to_names,
            index=to_names.index(selected_doc.get("to_plant_name")),
        )
        edit_mode = st.selectbox(
            "Transport mode",
            ["Truck", "Train", "Ship"],
            index=["Truck", "Train", "Ship"].index(selected_doc.get("transport_mode")),
        )

        edit_cost = st.number_input(
            "Cost per trip",
            min_value=0.0,
            value=float(selected_doc.get("cost_per_trip") or 0.0),
            step=1.0,
        )
        edit_capacity = st.number_input(
            "Capacity per trip",
            min_value=0.0,
            value=float(selected_doc.get("capacity_per_trip") or 0.0),
            step=1.0,
        )
        edit_sbq = st.number_input(
            "Minimum shipment batch (SBQ)",
            min_value=0.0,
            value=float(selected_doc.get("sbq") or 0.0),
            step=1.0,
        )

        saved = st.form_submit_button("Save Changes")

    if saved:
        ok, msg = edit_route(
            route_id=selected_id,
            payload={
                "from_plant_id": plant_options[edit_from_name],
                "to_plant_id": plant_options[edit_to_name],
                "transport_mode": edit_mode,
                "cost_per_trip": edit_cost,
                "capacity_per_trip": edit_capacity,
                "sbq": edit_sbq,
            },
        )

        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

    # Admin can enable/disable.
    st.divider()
    st.subheader("Enable / Disable Route")
    st.caption("Only Admin can enable or disable transport routes.")

    if require_role(["Admin"]):
        enabled_now = bool(selected_doc.get("is_enabled", True))
        new_enabled = st.toggle("Enabled", value=enabled_now)

        if st.button("Save route status"):
            ok, msg = toggle_route_enabled(selected_id, is_enabled=new_enabled)

            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    st.divider()
    st.subheader("Delete Route")
    st.caption("Only Admin can delete routes.")

    if not require_role(["Admin"]):
        return

    confirm = st.checkbox("I understand this will permanently delete the route.")

    if st.button("Delete selected route", disabled=not confirm):
        ok, msg = remove_route(selected_id)

        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)
