"""Inventory policy service (business logic + validation).

Role access:
- Admin & Planner: full access
- Viewer: view only

Validations:
- No negative values
- max_inventory >= safety_stock
- One policy per plant (no duplicates)
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from backend.inventory.inventory_repository import (
    create_policy,
    delete_policy,
    find_policy_by_id,
    find_policy_by_plant,
    list_policies,
    update_policy,
)
from backend.plant.plant_repository import find_plant_by_id


def validate_policy_payload(payload: Dict[str, Any]) -> Tuple[bool, str]:
    plant_id = (payload.get("plant_id") or "").strip()
    if not plant_id:
        return False, "Plant is required."

    plant = find_plant_by_id(plant_id)
    if plant is None:
        return False, "Selected plant does not exist."

    try:
        safety = float(payload.get("safety_stock"))
        max_inv = float(payload.get("max_inventory"))
        holding = float(payload.get("holding_cost_per_month"))
    except Exception:
        return False, "Safety stock, max inventory, and holding cost must be numbers."

    if safety < 0:
        return False, "Safety stock cannot be negative."

    if max_inv < 0:
        return False, "Max inventory cannot be negative."

    if holding < 0:
        return False, "Holding cost cannot be negative."

    if max_inv < safety:
        return False, "Max inventory must be greater than or equal to safety stock."

    return True, ""


def get_all_policies() -> List[Dict[str, Any]]:
    return list_policies()


def add_policy(payload: Dict[str, Any]) -> Tuple[bool, str]:
    ok, msg = validate_policy_payload(payload)
    if not ok:
        return False, msg

    plant = find_plant_by_id(payload["plant_id"].strip())
    payload["plant_name"] = plant.get("name")

    if find_policy_by_plant(payload["plant_id"].strip()) is not None:
        return False, "An inventory policy for this plant already exists."

    try:
        create_policy(payload)
        return True, "Inventory policy created successfully."
    except Exception:
        return False, "Failed to create inventory policy."


def edit_policy(policy_id: str, payload: Dict[str, Any]) -> Tuple[bool, str]:
    ok, msg = validate_policy_payload(payload)
    if not ok:
        return False, msg

    existing = find_policy_by_id(policy_id)
    if existing is None:
        return False, "Inventory policy not found."

    plant = find_plant_by_id(payload["plant_id"].strip())
    payload["plant_name"] = plant.get("name")

    if find_policy_by_plant(payload["plant_id"].strip(), exclude_id=policy_id) is not None:
        return False, "An inventory policy for this plant already exists."

    try:
        updated = update_policy(policy_id, payload)
        if not updated:
            return False, "No changes were saved."
        return True, "Inventory policy updated successfully."
    except Exception:
        return False, "Failed to update inventory policy."


def remove_policy(policy_id: str) -> Tuple[bool, str]:
    existing = find_policy_by_id(policy_id)
    if existing is None:
        return False, "Inventory policy not found."

    try:
        deleted = delete_policy(policy_id)
        if not deleted:
            return False, "Failed to delete inventory policy."
        return True, "Inventory policy deleted successfully."
    except Exception:
        return False, "Failed to delete inventory policy."
