"""Demand Management page (Streamlit UI).

What this page does:
- Shows all demand rows in a table
- Lets authorized users add/edit/delete demand entries

Role access:
- Admin & Planner: full access
- Viewer: read-only

Data flow:
UI -> backend.demand.demand_service -> backend.demand.demand_repository -> MongoDB
"""

from __future__ import annotations

import streamlit as st

from backend.demand.demand_service import add_demand, edit_demand, get_all_demands, remove_demand
from backend.middleware.role_guard import require_authentication
from backend.plant.plant_service import get_all_plants


def render_demand_page(role: str) -> None:
    if not require_authentication():
        return

    st.header("Demand Management")
    st.caption("Add monthly demand per plant. Month format: YYYY-MM.")

    plants = get_all_plants(include_inactive=False)
    plant_options = {p.get("name"): str(p.get("_id")) for p in plants}

    if not plant_options:
        st.warning("Please add at least one plant before creating demand.")
        return

    demands = get_all_demands()

    if demands:
        rows = []
        for d in demands:
            rows.append(
                {
                    "id": str(d.get("_id")),
                    "plant": d.get("plant_name"),
                    "month": d.get("month"),
                    "demand_quantity": d.get("demand_quantity"),
                    "demand_type": d.get("demand_type"),
                }
            )

        st.subheader("All Demands")
        st.dataframe(rows, use_container_width=True)
    else:
        st.info("No demand rows found yet.")

    if role == "Viewer":
        st.warning("Viewer role: read-only access.")
        return

    st.divider()
    st.subheader("Add Demand")

    with st.form("add_demand_form"):
        plant_name = st.selectbox("Plant", list(plant_options.keys()))
        month = st.text_input("Month (YYYY-MM)", placeholder="2026-01")
        demand_quantity = st.number_input("Demand quantity", min_value=0.0, value=0.0, step=1.0)
        demand_type = st.selectbox(
            "Demand type",
            ["Fixed", "Scenario-Low", "Scenario-Normal", "Scenario-High"],
        )

        submitted = st.form_submit_button("Create Demand")

    if submitted:
        ok, msg = add_demand(
            {
                "plant_id": plant_options[plant_name],
                "month": month,
                "demand_quantity": demand_quantity,
                "demand_type": demand_type,
            }
        )

        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

    if not demands:
        return

    st.divider()
    st.subheader("Edit / Delete Demand")

    demand_options = {
        f"{d.get('plant_name')} | {d.get('month')} | {d.get('demand_type')}": str(d.get("_id"))
        for d in demands
    }

    selected_label = st.selectbox("Select demand record", list(demand_options.keys()))
    selected_id = demand_options[selected_label]

    selected_doc = next((d for d in demands if str(d.get("_id")) == selected_id), None)
    if selected_doc is None:
        st.error("Demand record not found.")
        return

    with st.form("edit_demand_form"):
        edit_plant_name = st.selectbox(
            "Plant",
            list(plant_options.keys()),
            index=list(plant_options.keys()).index(selected_doc.get("plant_name")),
        )
        edit_month = st.text_input("Month (YYYY-MM)", value=selected_doc.get("month") or "")
        edit_qty = st.number_input(
            "Demand quantity",
            min_value=0.0,
            value=float(selected_doc.get("demand_quantity") or 0.0),
            step=1.0,
        )
        edit_type = st.selectbox(
            "Demand type",
            ["Fixed", "Scenario-Low", "Scenario-Normal", "Scenario-High"],
            index=["Fixed", "Scenario-Low", "Scenario-Normal", "Scenario-High"].index(
                selected_doc.get("demand_type")
            ),
        )

        saved = st.form_submit_button("Save Changes")

    if saved:
        ok, msg = edit_demand(
            demand_id=selected_id,
            payload={
                "plant_id": plant_options[edit_plant_name],
                "month": edit_month,
                "demand_quantity": edit_qty,
                "demand_type": edit_type,
            },
        )

        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

    confirm = st.checkbox("I understand this will permanently delete the selected demand record.")
    if st.button("Delete selected demand", disabled=not confirm):
        ok, msg = remove_demand(selected_id)

        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)
