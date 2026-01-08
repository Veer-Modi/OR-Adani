"""Demand repository (MongoDB CRUD).

This file only talks to MongoDB.

Demand document shape:
{
  plant_id: ObjectId,
  plant_name: str,  # denormalized for simple tables
  month: str,       # "YYYY-MM" for simplicity
  demand_quantity: float,
  demand_type: str, # "Fixed" or "Scenario-Low"/"Scenario-Normal"/"Scenario-High"
  created_at: datetime
}
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId

from backend.database.mongo import get_demands_collection


def list_demands() -> List[Dict[str, Any]]:
    """Return all demand documents."""

    demands = get_demands_collection()
    return list(demands.find({}).sort([("month", 1), ("plant_name", 1)]))


def find_demand_by_id(demand_id: str) -> Optional[Dict[str, Any]]:
    """Find a demand by _id."""

    demands = get_demands_collection()

    try:
        oid = ObjectId(demand_id)
    except Exception:
        return None

    return demands.find_one({"_id": oid})


def find_duplicate(plant_id: str, month: str, demand_type: str, exclude_id: str | None = None):
    """Find a record with same (plant_id, month, demand_type)."""

    demands = get_demands_collection()

    query: Dict[str, Any] = {
        "plant_id": ObjectId(plant_id),
        "month": month,
        "demand_type": demand_type,
    }

    if exclude_id:
        query["_id"] = {"$ne": ObjectId(exclude_id)}

    return demands.find_one(query)


def create_demand(data: Dict[str, Any]) -> str:
    """Insert a new demand document."""

    demands = get_demands_collection()

    doc = {
        "plant_id": ObjectId(data["plant_id"]),
        "plant_name": data["plant_name"],
        "month": data["month"],
        "demand_quantity": float(data["demand_quantity"]),
        "demand_type": data["demand_type"],
        "created_at": datetime.now(timezone.utc),
    }

    result = demands.insert_one(doc)
    return str(result.inserted_id)


def update_demand(demand_id: str, data: Dict[str, Any]) -> bool:
    """Update an existing demand."""

    demands = get_demands_collection()

    try:
        oid = ObjectId(demand_id)
    except Exception:
        return False

    update_doc = {
        "$set": {
            "plant_id": ObjectId(data["plant_id"]),
            "plant_name": data["plant_name"],
            "month": data["month"],
            "demand_quantity": float(data["demand_quantity"]),
            "demand_type": data["demand_type"],
        }
    }

    result = demands.update_one({"_id": oid}, update_doc)
    return result.modified_count == 1


def delete_demand(demand_id: str) -> bool:
    """Delete a demand document."""

    demands = get_demands_collection()

    try:
        oid = ObjectId(demand_id)
    except Exception:
        return False

    result = demands.delete_one({"_id": oid})
    return result.deleted_count == 1
