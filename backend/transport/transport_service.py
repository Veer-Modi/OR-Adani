"""Transport service (business logic + validation).

Role access:
- Admin: full access
- Planner: add + edit
- Viewer: view only

Validations:
- No negative values
- SBQ <= capacity_per_trip
- Prevent duplicates for (from, to, mode)
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from backend.plant.plant_repository import find_plant_by_id
from backend.transport.transport_repository import (
    create_route,
    delete_route,
    find_duplicate,
    find_route_by_id,
    list_routes,
    set_route_enabled,
    update_route,
)


_ALLOWED_MODES = {"Truck", "Train", "Ship"}


def validate_transport_payload(payload: Dict[str, Any]) -> Tuple[bool, str]:
    from_plant_id = (payload.get("from_plant_id") or "").strip()
    to_plant_id = (payload.get("to_plant_id") or "").strip()

    if not from_plant_id or not to_plant_id:
        return False, "Both 'From plant' and 'To plant' are required."

    if from_plant_id == to_plant_id:
        return False, "From plant and To plant cannot be the same."

    from_plant = find_plant_by_id(from_plant_id)
    to_plant = find_plant_by_id(to_plant_id)

    if from_plant is None or to_plant is None:
        return False, "Selected plant does not exist."

    mode = (payload.get("transport_mode") or "").strip()
    if mode not in _ALLOWED_MODES:
        return False, "Invalid transport mode."

    try:
        cost = float(payload.get("cost_per_trip"))
        cap = float(payload.get("capacity_per_trip"))
        sbq = float(payload.get("sbq"))
    except Exception:
        return False, "Cost, capacity, and SBQ must be numbers."

    if cost < 0:
        return False, "Cost per trip cannot be negative."

    if cap < 0:
        return False, "Capacity per trip cannot be negative."

    if sbq < 0:
        return False, "Minimum shipment batch (SBQ) cannot be negative."

    if sbq > cap:
        return False, "SBQ must be less than or equal to capacity per trip."

    return True, ""


def get_all_routes(include_disabled: bool = True) -> List[Dict[str, Any]]:
    return list_routes(include_disabled=include_disabled)


def add_route(payload: Dict[str, Any]) -> Tuple[bool, str]:
    ok, msg = validate_transport_payload(payload)
    if not ok:
        return False, msg

    from_plant = find_plant_by_id(payload["from_plant_id"].strip())
    to_plant = find_plant_by_id(payload["to_plant_id"].strip())

    payload["from_plant_name"] = from_plant.get("name")
    payload["to_plant_name"] = to_plant.get("name")

    dup = find_duplicate(
        payload["from_plant_id"].strip(),
        payload["to_plant_id"].strip(),
        payload["transport_mode"].strip(),
    )
    if dup is not None:
        return False, "Duplicate route for same From, To, and Mode."

    try:
        create_route(payload)
        return True, "Transport route created successfully."
    except Exception:
        return False, "Failed to create transport route."


def edit_route(route_id: str, payload: Dict[str, Any]) -> Tuple[bool, str]:
    ok, msg = validate_transport_payload(payload)
    if not ok:
        return False, msg

    existing = find_route_by_id(route_id)
    if existing is None:
        return False, "Transport route not found."

    from_plant = find_plant_by_id(payload["from_plant_id"].strip())
    to_plant = find_plant_by_id(payload["to_plant_id"].strip())

    payload["from_plant_name"] = from_plant.get("name")
    payload["to_plant_name"] = to_plant.get("name")

    dup = find_duplicate(
        payload["from_plant_id"].strip(),
        payload["to_plant_id"].strip(),
        payload["transport_mode"].strip(),
        exclude_id=route_id,
    )
    if dup is not None:
        return False, "Duplicate route for same From, To, and Mode."

    try:
        updated = update_route(route_id, payload)
        if not updated:
            return False, "No changes were saved."
        return True, "Transport route updated successfully."
    except Exception:
        return False, "Failed to update transport route."


def remove_route(route_id: str) -> Tuple[bool, str]:
    existing = find_route_by_id(route_id)
    if existing is None:
        return False, "Transport route not found."

    try:
        deleted = delete_route(route_id)
        if not deleted:
            return False, "Failed to delete transport route."
        return True, "Transport route deleted successfully."
    except Exception:
        return False, "Failed to delete transport route."


def toggle_route_enabled(route_id: str, is_enabled: bool) -> Tuple[bool, str]:
    existing = find_route_by_id(route_id)
    if existing is None:
        return False, "Transport route not found."

    try:
        changed = set_route_enabled(route_id, is_enabled=is_enabled)
        if not changed:
            return False, "No changes were saved."
        return True, "Transport route updated successfully."
    except Exception:
        return False, "Failed to update transport route."
