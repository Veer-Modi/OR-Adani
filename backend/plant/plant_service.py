"""Plant service (business logic + validation).

Role access:
- Admin: full access
- Planner: add + edit
- Viewer: view only

Data flow:
UI -> plant_service -> plant_repository -> MongoDB

Validations implemented here:
- No negative numbers
- storage_capacity >= safety_stock
- Prevent duplicate plant names
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from pymongo.errors import DuplicateKeyError

from backend.plant.plant_repository import (
    create_plant,
    delete_plant,
    find_plant_by_id,
    find_plant_by_name,
    list_plants,
    update_plant,
)


_ALLOWED_PLANT_TYPES = {"Clinker Plant", "Grinding Plant"}


def _validate_non_negative(value: float, field_name: str) -> Tuple[bool, str]:
    """Reject negative numbers."""

    if value < 0:
        return False, f"{field_name} cannot be negative."

    return True, ""


def validate_plant_payload(payload: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate plant fields."""

    name = (payload.get("name") or "").strip()
    if len(name) < 2:
        return False, "Plant name must be at least 2 characters."

    if len(name) > 80:
        return False, "Plant name is too long (max 80 characters)."

    plant_type = (payload.get("plant_type") or "").strip()
    if plant_type not in _ALLOWED_PLANT_TYPES:
        return False, "Invalid plant type."

    location = (payload.get("location") or "").strip()
    if len(location) < 2:
        return False, "Location must be at least 2 characters."

    try:
        storage_capacity = float(payload.get("storage_capacity"))
        safety_stock = float(payload.get("safety_stock"))
        initial_inventory = float(payload.get("initial_inventory"))
    except Exception:
        return False, "Capacity, safety stock, and initial inventory must be numbers."

    ok, msg = _validate_non_negative(storage_capacity, "Storage capacity")
    if not ok:
        return False, msg

    ok, msg = _validate_non_negative(safety_stock, "Safety stock")
    if not ok:
        return False, msg

    ok, msg = _validate_non_negative(initial_inventory, "Initial inventory")
    if not ok:
        return False, msg

    if storage_capacity < safety_stock:
        return False, "Storage capacity must be greater than or equal to safety stock."

    if initial_inventory > storage_capacity:
        return False, "Initial inventory cannot be greater than storage capacity."

    # Phase 3 optimization fields:
    # These fields are OPTIONAL in Phase 2 UI so we don't break existing data.
    # They will be REQUIRED only when you run optimization (see optimization/data_loader.py).
    production_capacity_value = payload.get("production_capacity")
    production_cost_value = payload.get("production_cost")

    if production_capacity_value is not None:
        try:
            production_capacity = float(production_capacity_value)
        except Exception:
            return False, "Production capacity must be a number."

        ok, msg = _validate_non_negative(production_capacity, "Production capacity")
        if not ok:
            return False, msg

    if production_cost_value is not None:
        try:
            production_cost = float(production_cost_value)
        except Exception:
            return False, "Production cost must be a number."

        ok, msg = _validate_non_negative(production_cost, "Production cost")
        if not ok:
            return False, msg

    return True, ""


def get_all_plants(include_inactive: bool = True) -> List[Dict[str, Any]]:
    """List plants for UI tables."""

    return list_plants(include_inactive=include_inactive)


def add_plant(payload: Dict[str, Any]) -> Tuple[bool, str]:
    """Create a new plant."""

    ok, msg = validate_plant_payload(payload)
    if not ok:
        return False, msg

    name = payload["name"].strip()

    # Prevent duplicates at the service level (fast user feedback).
    if find_plant_by_name(name) is not None:
        return False, "A plant with this name already exists."

    try:
        create_plant(payload)
        return True, "Plant created successfully."
    except DuplicateKeyError:
        # Also protected by MongoDB unique index.
        return False, "A plant with this name already exists."
    except Exception:
        return False, "Failed to create plant. Please try again."


def edit_plant(plant_id: str, payload: Dict[str, Any]) -> Tuple[bool, str]:
    """Edit an existing plant."""

    ok, msg = validate_plant_payload(payload)
    if not ok:
        return False, msg

    existing = find_plant_by_id(plant_id)
    if existing is None:
        return False, "Plant not found."

    new_name = payload["name"].strip()
    other = find_plant_by_name(new_name)
    if other is not None and str(other.get("_id")) != str(existing.get("_id")):
        return False, "Another plant with this name already exists."

    try:
        updated = update_plant(plant_id, payload)
        if not updated:
            return False, "No changes were saved."
        return True, "Plant updated successfully."
    except DuplicateKeyError:
        return False, "A plant with this name already exists."
    except Exception:
        return False, "Failed to update plant."


def remove_plant(plant_id: str) -> Tuple[bool, str]:
    """Delete a plant."""

    existing = find_plant_by_id(plant_id)
    if existing is None:
        return False, "Plant not found."

    try:
        deleted = delete_plant(plant_id)
        if not deleted:
            return False, "Failed to delete plant."
        return True, "Plant deleted successfully."
    except Exception:
        return False, "Failed to delete plant."
