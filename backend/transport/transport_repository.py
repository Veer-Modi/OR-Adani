"""Transport routes repository (MongoDB CRUD).

Transport route document shape:
{
  from_plant_id: ObjectId,
  from_plant_name: str,
  to_plant_id: ObjectId,
  to_plant_name: str,
  transport_mode: str,  # Truck / Train / Ship
  cost_per_trip: float,
  capacity_per_trip: float,
  sbq: float,
  is_enabled: bool,
  created_at: datetime
}
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId

from backend.database.mongo import get_transport_routes_collection


def list_routes(include_disabled: bool = True) -> List[Dict[str, Any]]:
    routes = get_transport_routes_collection()

    query = {} if include_disabled else {"is_enabled": True}

    return list(
        routes.find(query).sort(
            [
                ("from_plant_name", 1),
                ("to_plant_name", 1),
                ("transport_mode", 1),
            ]
        )
    )


def find_route_by_id(route_id: str) -> Optional[Dict[str, Any]]:
    routes = get_transport_routes_collection()

    try:
        oid = ObjectId(route_id)
    except Exception:
        return None

    return routes.find_one({"_id": oid})


def find_duplicate(from_plant_id: str, to_plant_id: str, transport_mode: str, exclude_id: str | None = None):
    routes = get_transport_routes_collection()

    query: Dict[str, Any] = {
        "from_plant_id": ObjectId(from_plant_id),
        "to_plant_id": ObjectId(to_plant_id),
        "transport_mode": transport_mode,
    }

    if exclude_id:
        query["_id"] = {"$ne": ObjectId(exclude_id)}

    return routes.find_one(query)


def create_route(data: Dict[str, Any]) -> str:
    routes = get_transport_routes_collection()

    doc = {
        "from_plant_id": ObjectId(data["from_plant_id"]),
        "from_plant_name": data["from_plant_name"],
        "to_plant_id": ObjectId(data["to_plant_id"]),
        "to_plant_name": data["to_plant_name"],
        "transport_mode": data["transport_mode"],
        "cost_per_trip": float(data["cost_per_trip"]),
        "capacity_per_trip": float(data["capacity_per_trip"]),
        "sbq": float(data["sbq"]),
        "is_enabled": True,
        "created_at": datetime.now(timezone.utc),
    }

    result = routes.insert_one(doc)
    return str(result.inserted_id)


def update_route(route_id: str, data: Dict[str, Any]) -> bool:
    routes = get_transport_routes_collection()

    try:
        oid = ObjectId(route_id)
    except Exception:
        return False

    update_doc = {
        "$set": {
            "from_plant_id": ObjectId(data["from_plant_id"]),
            "from_plant_name": data["from_plant_name"],
            "to_plant_id": ObjectId(data["to_plant_id"]),
            "to_plant_name": data["to_plant_name"],
            "transport_mode": data["transport_mode"],
            "cost_per_trip": float(data["cost_per_trip"]),
            "capacity_per_trip": float(data["capacity_per_trip"]),
            "sbq": float(data["sbq"]),
        }
    }

    result = routes.update_one({"_id": oid}, update_doc)
    return result.modified_count == 1


def delete_route(route_id: str) -> bool:
    routes = get_transport_routes_collection()

    try:
        oid = ObjectId(route_id)
    except Exception:
        return False

    result = routes.delete_one({"_id": oid})
    return result.deleted_count == 1


def set_route_enabled(route_id: str, is_enabled: bool) -> bool:
    routes = get_transport_routes_collection()

    try:
        oid = ObjectId(route_id)
    except Exception:
        return False

    result = routes.update_one({"_id": oid}, {"$set": {"is_enabled": bool(is_enabled)}})
    return result.modified_count == 1
