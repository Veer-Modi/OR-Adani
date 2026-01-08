"""Plant Management page (Streamlit UI).

What this page does:
- Shows all plants in a table
- Lets authorized users add/edit/delete plants

Role access:
- Admin: full access
- Planner: add + edit
- Viewer: view only

Data flow:
UI -> backend.plant.plant_service -> backend.plant.plant_repository -> MongoDB
"""

from __future__ import annotations

import streamlit as st

from backend.middleware.role_guard import require_authentication, require_role
from backend.plant.plant_service import add_plant, edit_plant, get_all_plants, remove_plant


def render_plant_page(role: str) -> None:
    """Render the Plant Management page."""

    if not require_authentication():
        return

    st.header("Plant Management")
    st.caption("Create and manage plants used by other planning modules.")

    plants = get_all_plants(include_inactive=True)

    if plants:
        # Clean table for UI (hide MongoDB internal fields except _id).
        rows = []
        for p in plants:
            rows.append(
                {
                    "id": str(p.get("_id")),
                    "name": p.get("name"),
                    "plant_type": p.get("plant_type"),
                    "location": p.get("location"),
                    "storage_capacity": p.get("storage_capacity"),
                    "safety_stock": p.get("safety_stock"),
                    "initial_inventory": p.get("initial_inventory"),
                    "is_active": p.get("is_active", True),
                }
            )

        st.subheader("All Plants")
        st.dataframe(rows, use_container_width=True)
    else:
        st.info("No plants found yet. Add your first plant below.")

    # Viewer can only view.
    if role == "Viewer":
        st.warning("Viewer role: read-only access.")
        return

    # Planner and Admin can add/edit.
    st.divider()
    st.subheader("Add Plant")

    with st.form("add_plant_form"):
        name = st.text_input("Plant name")
        plant_type = st.selectbox("Plant type", ["Clinker Plant", "Grinding Plant"])
        location = st.text_input("Location")

        storage_capacity = st.number_input("Storage capacity", min_value=0.0, value=0.0, step=1.0)
        safety_stock = st.number_input("Safety stock", min_value=0.0, value=0.0, step=1.0)
        initial_inventory = st.number_input("Initial inventory", min_value=0.0, value=0.0, step=1.0)

        st.caption("Optional (Phase 3 Optimization): Only needed for Clinker Plant")
        production_capacity = st.number_input(
            "Production capacity per month",
            min_value=0.0,
            value=0.0,
            step=1.0,
        )
        production_cost = st.number_input(
            "Production cost per unit",
            min_value=0.0,
            value=0.0,
            step=1.0,
        )

        submitted = st.form_submit_button("Create Plant")

    if submitted:
        # Keep optimization fields optional. If user leaves them at 0 for a clinker plant,
        # optimization will later show a clear error if capacity/cost is missing.
        payload = {
            "name": name,
            "plant_type": plant_type,
            "location": location,
            "storage_capacity": storage_capacity,
            "safety_stock": safety_stock,
            "initial_inventory": initial_inventory,
        }

        if plant_type == "Clinker Plant":
            payload["production_capacity"] = production_capacity
            payload["production_cost"] = production_cost

        ok, msg = add_plant(
            payload
        )

        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

    if not plants:
        return

    st.divider()
    st.subheader("Edit Plant")

    plant_options = {f"{p.get('name')} ({p.get('plant_type')})": str(p.get("_id")) for p in plants}
    selected_label = st.selectbox("Select plant to edit", list(plant_options.keys()))
    selected_id = plant_options[selected_label]

    selected_doc = next((p for p in plants if str(p.get("_id")) == selected_id), None)

    if selected_doc is None:
        st.error("Selected plant not found.")
        return

    with st.form("edit_plant_form"):
        edit_name = st.text_input("Plant name", value=selected_doc.get("name") or "")
        edit_type = st.selectbox(
            "Plant type",
            ["Clinker Plant", "Grinding Plant"],
            index=0 if (selected_doc.get("plant_type") == "Clinker Plant") else 1,
        )
        edit_location = st.text_input("Location", value=selected_doc.get("location") or "")

        edit_storage_capacity = st.number_input(
            "Storage capacity",
            min_value=0.0,
            value=float(selected_doc.get("storage_capacity") or 0.0),
            step=1.0,
        )
        edit_safety_stock = st.number_input(
            "Safety stock",
            min_value=0.0,
            value=float(selected_doc.get("safety_stock") or 0.0),
            step=1.0,
        )
        edit_initial_inventory = st.number_input(
            "Initial inventory",
            min_value=0.0,
            value=float(selected_doc.get("initial_inventory") or 0.0),
            step=1.0,
        )

        st.caption("Optional (Phase 3 Optimization): Only needed for Clinker Plant")
        edit_production_capacity = st.number_input(
            "Production capacity per month",
            min_value=0.0,
            value=float(selected_doc.get("production_capacity") or 0.0),
            step=1.0,
        )
        edit_production_cost = st.number_input(
            "Production cost per unit",
            min_value=0.0,
            value=float(selected_doc.get("production_cost") or 0.0),
            step=1.0,
        )

        saved = st.form_submit_button("Save Changes")

    if saved:
        payload = {
            "name": edit_name,
            "plant_type": edit_type,
            "location": edit_location,
            "storage_capacity": edit_storage_capacity,
            "safety_stock": edit_safety_stock,
            "initial_inventory": edit_initial_inventory,
        }

        if edit_type == "Clinker Plant":
            payload["production_capacity"] = edit_production_capacity
            payload["production_cost"] = edit_production_cost

        ok, msg = edit_plant(
            plant_id=selected_id,
            payload=payload,
        )

        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

    # Delete is Admin-only.
    st.divider()
    st.subheader("Delete Plant")
    st.caption("Only Admin can delete plants.")

    if not require_role(["Admin"]):
        return

    confirm = st.checkbox("I understand this will permanently delete the plant.")

    if st.button("Delete selected plant", disabled=not confirm):
        ok, msg = remove_plant(selected_id)

        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)
