"""Demand service (business logic + validation).

Role access:
- Admin & Planner: full access
- Viewer: view only

Data flow:
UI -> demand_service -> demand_repository -> MongoDB

Validations:
- No negative demand
- Prevent duplicates for (plant, month, demand_type)
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from backend.demand.demand_repository import (
    create_demand,
    delete_demand,
    find_demand_by_id,
    find_duplicate,
    list_demands,
    update_demand,
)
from backend.plant.plant_repository import find_plant_by_id


_ALLOWED_DEMAND_TYPES = {
    "Fixed",
    "Scenario-Low",
    "Scenario-Normal",
    "Scenario-High",
}


def _validate_month(value: str) -> Tuple[bool, str]:
    """Validate month as YYYY-MM."""

    text = (value or "").strip()
    if not re.match(r"^\d{4}-\d{2}$", text):
        return False, "Month must be in format YYYY-MM (example: 2026-01)."

    year = int(text.split("-")[0])
    month = int(text.split("-")[1])

    if year < 2000 or year > 2100:
        return False, "Year must be between 2000 and 2100."

    if month < 1 or month > 12:
        return False, "Month must be between 01 and 12."

    return True, ""


def validate_demand_payload(payload: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate demand fields."""

    plant_id = (payload.get("plant_id") or "").strip()
    if not plant_id:
        return False, "Plant is required."

    plant = find_plant_by_id(plant_id)
    if plant is None:
        return False, "Selected plant does not exist."

    ok, msg = _validate_month(payload.get("month") or "")
    if not ok:
        return False, msg

    demand_type = (payload.get("demand_type") or "").strip()
    if demand_type not in _ALLOWED_DEMAND_TYPES:
        return False, "Invalid demand type."

    try:
        qty = float(payload.get("demand_quantity"))
    except Exception:
        return False, "Demand quantity must be a number."

    if qty < 0:
        return False, "Demand quantity cannot be negative."

    return True, ""


def get_all_demands() -> List[Dict[str, Any]]:
    return list_demands()


def add_demand(payload: Dict[str, Any]) -> Tuple[bool, str]:
    ok, msg = validate_demand_payload(payload)
    if not ok:
        return False, msg

    plant = find_plant_by_id(payload["plant_id"].strip())
    payload["plant_name"] = plant.get("name")

    dup = find_duplicate(payload["plant_id"].strip(), payload["month"].strip(), payload["demand_type"].strip())
    if dup is not None:
        return False, "Duplicate demand entry for the same plant, month, and demand type."

    try:
        create_demand(payload)
        return True, "Demand created successfully."
    except Exception:
        return False, "Failed to create demand."


def edit_demand(demand_id: str, payload: Dict[str, Any]) -> Tuple[bool, str]:
    ok, msg = validate_demand_payload(payload)
    if not ok:
        return False, msg

    existing = find_demand_by_id(demand_id)
    if existing is None:
        return False, "Demand record not found."

    plant = find_plant_by_id(payload["plant_id"].strip())
    payload["plant_name"] = plant.get("name")

    dup = find_duplicate(
        payload["plant_id"].strip(),
        payload["month"].strip(),
        payload["demand_type"].strip(),
        exclude_id=demand_id,
    )
    if dup is not None:
        return False, "Duplicate demand entry for the same plant, month, and demand type."

    try:
        updated = update_demand(demand_id, payload)
        if not updated:
            return False, "No changes were saved."
        return True, "Demand updated successfully."
    except Exception:
        return False, "Failed to update demand."


def remove_demand(demand_id: str) -> Tuple[bool, str]:
    existing = find_demand_by_id(demand_id)
    if existing is None:
        return False, "Demand record not found."

    try:
        deleted = delete_demand(demand_id)
        if not deleted:
            return False, "Failed to delete demand."
        return True, "Demand deleted successfully."
    except Exception:
        return False, "Failed to delete demand."
