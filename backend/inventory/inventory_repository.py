"""Inventory policy repository (MongoDB CRUD).

Inventory policy document shape:
{
  plant_id: ObjectId,
  plant_name: str,
  safety_stock: float,
  max_inventory: float,
  holding_cost_per_month: float,
  created_at: datetime
}

Rule:
- One policy per plant (enforced by unique index).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId

from backend.database.mongo import get_inventory_policies_collection


def list_policies() -> List[Dict[str, Any]]:
    policies = get_inventory_policies_collection()
    return list(policies.find({}).sort("plant_name", 1))


def find_policy_by_id(policy_id: str) -> Optional[Dict[str, Any]]:
    policies = get_inventory_policies_collection()

    try:
        oid = ObjectId(policy_id)
    except Exception:
        return None

    return policies.find_one({"_id": oid})


def find_policy_by_plant(plant_id: str, exclude_id: str | None = None):
    policies = get_inventory_policies_collection()

    query: Dict[str, Any] = {"plant_id": ObjectId(plant_id)}
    if exclude_id:
        query["_id"] = {"$ne": ObjectId(exclude_id)}

    return policies.find_one(query)


def create_policy(data: Dict[str, Any]) -> str:
    policies = get_inventory_policies_collection()

    doc = {
        "plant_id": ObjectId(data["plant_id"]),
        "plant_name": data["plant_name"],
        "safety_stock": float(data["safety_stock"]),
        "max_inventory": float(data["max_inventory"]),
        "holding_cost_per_month": float(data["holding_cost_per_month"]),
        "created_at": datetime.now(timezone.utc),
    }

    result = policies.insert_one(doc)
    return str(result.inserted_id)


def update_policy(policy_id: str, data: Dict[str, Any]) -> bool:
    policies = get_inventory_policies_collection()

    try:
        oid = ObjectId(policy_id)
    except Exception:
        return False

    update_doc = {
        "$set": {
            "plant_id": ObjectId(data["plant_id"]),
            "plant_name": data["plant_name"],
            "safety_stock": float(data["safety_stock"]),
            "max_inventory": float(data["max_inventory"]),
            "holding_cost_per_month": float(data["holding_cost_per_month"]),
        }
    }

    result = policies.update_one({"_id": oid}, update_doc)
    return result.modified_count == 1


def delete_policy(policy_id: str) -> bool:
    policies = get_inventory_policies_collection()

    try:
        oid = ObjectId(policy_id)
    except Exception:
        return False

    result = policies.delete_one({"_id": oid})
    return result.deleted_count == 1
