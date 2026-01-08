"""Database operations for users.

This file has ONLY database CRUD operations.
No Streamlit UI code and no business logic here.

A user document looks like:
{
  name: str,
  email: str,
  password_hash: str,
  role: str,
  is_active: bool,
  created_at: datetime
}
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pymongo.errors import DuplicateKeyError

from backend.database.mongo import get_users_collection


def find_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Find a single user by email."""

    users = get_users_collection()
    return users.find_one({"email": email})


def create_user(name: str, email: str, password_hash: str, role: str) -> bool:
    """Create a new user document.

    Returns:
- True  -> user created
- False -> email already exists
    """

    users = get_users_collection()

    doc = {
        "name": name,
        "email": email,
        "password_hash": password_hash,
        "role": role,
        # Accounts are enabled by default.
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
    }

    try:
        users.insert_one(doc)
        return True
    except DuplicateKeyError:
        # Email already exists (because of the unique index).
        return False


def list_users() -> List[Dict[str, Any]]:
    """List all users for admin UI."""

    users = get_users_collection()

    # Exclude password hash from UI results.
    projection = {"password_hash": 0}

    return list(users.find({}, projection).sort("created_at", -1))


def set_user_role(email: str, role: str) -> bool:
    """Update a user's role by email. Returns True if changed."""

    users = get_users_collection()
    result = users.update_one({"email": email}, {"$set": {"role": role}})
    return result.modified_count == 1


def set_user_active(email: str, is_active: bool) -> bool:
    """Enable/disable a user account by email."""

    users = get_users_collection()
    result = users.update_one({"email": email}, {"$set": {"is_active": bool(is_active)}})
    return result.modified_count == 1


def count_users() -> Dict[str, int]:
    """Return summary counts for dashboard cards."""

    users = get_users_collection()

    total = users.count_documents({})
    active = users.count_documents({"is_active": True})
    inactive = users.count_documents({"is_active": False})

    return {"total": total, "active": active, "inactive": inactive}


def role_distribution() -> Dict[str, int]:
    """Return counts per role."""

    users = get_users_collection()

    pipeline = [
        {"$group": {"_id": "$role", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]

    result = list(users.aggregate(pipeline))

    output: Dict[str, int] = {}
    for row in result:
        output[str(row.get("_id"))] = int(row.get("count", 0))

    return output
