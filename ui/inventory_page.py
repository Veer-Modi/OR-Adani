"""Inventory Policy Management page (Streamlit UI).

What this page does:
- Shows inventory policies per plant
- Lets authorized users create/edit/delete policies

Role access:
- Admin & Planner: full access
- Viewer: read-only

Data flow:
UI -> backend.inventory.inventory_service -> backend.inventory.inventory_repository -> MongoDB
"""

from __future__ import annotations

import streamlit as st

from backend.inventory.inventory_service import (
    add_policy,
    edit_policy,
    get_all_policies,
    remove_policy,
)
from backend.middleware.role_guard import require_authentication
from backend.plant.plant_service import get_all_plants


def render_inventory_page(role: str) -> None:
    if not require_authentication():
        return

    st.header("Inventory Policies")
    st.caption("Define safety stock, max inventory, and holding cost per plant.")

    plants = get_all_plants(include_inactive=False)
    plant_options = {p.get("name"): str(p.get("_id")) for p in plants}

    if not plant_options:
        st.warning("Please add at least one plant before creating inventory policies.")
        return

    policies = get_all_policies()

    if policies:
        rows = []
        for pol in policies:
            rows.append(
                {
                    "id": str(pol.get("_id")),
                    "plant": pol.get("plant_name"),
                    "safety_stock": pol.get("safety_stock"),
                    "max_inventory": pol.get("max_inventory"),
                    "holding_cost_per_month": pol.get("holding_cost_per_month"),
                }
            )

        st.subheader("All Inventory Policies")
        st.dataframe(rows, use_container_width=True)
    else:
        st.info("No inventory policies found yet.")

    if role == "Viewer":
        st.warning("Viewer role: read-only access.")
        return

    st.divider()
    st.subheader("Add Inventory Policy")

    with st.form("add_policy_form"):
        plant_name = st.selectbox("Plant", list(plant_options.keys()))
        safety = st.number_input("Safety stock", min_value=0.0, value=0.0, step=1.0)
        max_inv = st.number_input("Max inventory", min_value=0.0, value=0.0, step=1.0)
        holding = st.number_input("Holding cost per month", min_value=0.0, value=0.0, step=1.0)

        submitted = st.form_submit_button("Create Policy")

    if submitted:
        ok, msg = add_policy(
            {
                "plant_id": plant_options[plant_name],
                "safety_stock": safety,
                "max_inventory": max_inv,
                "holding_cost_per_month": holding,
            }
        )

        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

    if not policies:
        return

    st.divider()
    st.subheader("Edit / Delete Policy")

    policy_options = {f"{p.get('plant_name')}": str(p.get("_id")) for p in policies}
    selected_label = st.selectbox("Select policy", list(policy_options.keys()))
    selected_id = policy_options[selected_label]

    selected_doc = next((p for p in policies if str(p.get("_id")) == selected_id), None)
    if selected_doc is None:
        st.error("Policy not found.")
        return

    with st.form("edit_policy_form"):
        edit_plant_name = st.selectbox(
            "Plant",
            list(plant_options.keys()),
            index=list(plant_options.keys()).index(selected_doc.get("plant_name")),
        )
        edit_safety = st.number_input(
            "Safety stock",
            min_value=0.0,
            value=float(selected_doc.get("safety_stock") or 0.0),
            step=1.0,
        )
        edit_max = st.number_input(
            "Max inventory",
            min_value=0.0,
            value=float(selected_doc.get("max_inventory") or 0.0),
            step=1.0,
        )
        edit_holding = st.number_input(
            "Holding cost per month",
            min_value=0.0,
            value=float(selected_doc.get("holding_cost_per_month") or 0.0),
            step=1.0,
        )

        saved = st.form_submit_button("Save Changes")

    if saved:
        ok, msg = edit_policy(
            policy_id=selected_id,
            payload={
                "plant_id": plant_options[edit_plant_name],
                "safety_stock": edit_safety,
                "max_inventory": edit_max,
                "holding_cost_per_month": edit_holding,
            },
        )

        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

    confirm = st.checkbox("I understand this will permanently delete the selected policy.")
    if st.button("Delete selected policy", disabled=not confirm):
        ok, msg = remove_policy(selected_id)

        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)
