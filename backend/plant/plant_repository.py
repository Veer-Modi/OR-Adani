"""Plant repository (MongoDB CRUD).

This file only talks to MongoDB.
No Streamlit UI code and no business validations here.

Plant document shape:
{
  name: str,
  plant_type: str,  # "Clinker Plant" or "Grinding Plant"
  location: str,
  storage_capacity: float,
  safety_stock: float,
  initial_inventory: float,
  is_active: bool,
  created_at: datetime
}
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId

from backend.database.mongo import get_plants_collection


def list_plants(include_inactive: bool = True) -> List[Dict[str, Any]]:
    """Return all plant documents."""

    plants = get_plants_collection()

    query = {} if include_inactive else {"is_active": True}

    # Sort by name for a clean UI.
    return list(plants.find(query).sort("name", 1))


def find_plant_by_id(plant_id: str) -> Optional[Dict[str, Any]]:
    """Find a plant by MongoDB _id."""

    plants = get_plants_collection()

    try:
        oid = ObjectId(plant_id)
    except Exception:
        return None

    return plants.find_one({"_id": oid})


def find_plant_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Find a plant by name."""

    plants = get_plants_collection()
    return plants.find_one({"name": name})


def create_plant(data: Dict[str, Any]) -> str:
    """Insert a new plant.

    Returns the new plant_id as string.
    """

    plants = get_plants_collection()

    doc = {
        "name": data["name"],
        "plant_type": data["plant_type"],
        "location": data["location"],
        "storage_capacity": float(data["storage_capacity"]),
        "safety_stock": float(data["safety_stock"]),
        "initial_inventory": float(data["initial_inventory"]),
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
    }

    # Optional optimization fields (Phase 3).
    if data.get("production_capacity") is not None:
        doc["production_capacity"] = float(data["production_capacity"])

    if data.get("production_cost") is not None:
        doc["production_cost"] = float(data["production_cost"])

    result = plants.insert_one(doc)
    return str(result.inserted_id)


def update_plant(plant_id: str, data: Dict[str, Any]) -> bool:
    """Update an existing plant. Returns True if updated."""

    plants = get_plants_collection()

    try:
        oid = ObjectId(plant_id)
    except Exception:
        return False

    update_doc = {
        "$set": {
            "name": data["name"],
            "plant_type": data["plant_type"],
            "location": data["location"],
            "storage_capacity": float(data["storage_capacity"]),
            "safety_stock": float(data["safety_stock"]),
            "initial_inventory": float(data["initial_inventory"]),
        }
    }

    # Optional optimization fields (Phase 3).
    if data.get("production_capacity") is not None:
        update_doc["$set"]["production_capacity"] = float(data["production_capacity"])

    if data.get("production_cost") is not None:
        update_doc["$set"]["production_cost"] = float(data["production_cost"])

    result = plants.update_one({"_id": oid}, update_doc)
    return result.modified_count == 1


def delete_plant(plant_id: str) -> bool:
    """Delete a plant document."""

    plants = get_plants_collection()

    try:
        oid = ObjectId(plant_id)
    except Exception:
        return False

    result = plants.delete_one({"_id": oid})
    return result.deleted_count == 1
