"""User service (Admin operations).

Role access:
- Admin only

Data flow:
UI -> user_service -> user_repository -> MongoDB

This service provides:
- list users (for admin dashboard)
- change role
- enable/disable user accounts
- summary counts
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from backend.database.user_repository import (
    count_users,
    list_users,
    role_distribution,
    set_user_active,
    set_user_role,
)


_ALLOWED_ROLES = {"Admin", "Planner", "Viewer"}


def get_user_summaries() -> Tuple[Dict[str, int], Dict[str, int]]:
    """Return (counts, role_distribution)."""

    return count_users(), role_distribution()


def get_all_users() -> List[Dict[str, Any]]:
    """List users for admin dashboard table."""

    return list_users()


def change_user_role(email: str, new_role: str) -> Tuple[bool, str]:
    """Change a user's role."""

    normalized_email = (email or "").strip().lower()
    role = (new_role or "").strip()

    if not normalized_email:
        return False, "Email is required."

    if role not in _ALLOWED_ROLES:
        return False, "Invalid role selected."

    try:
        changed = set_user_role(normalized_email, role)
        if not changed:
            return False, "No changes were saved (maybe same role)."
        return True, "User role updated successfully."
    except Exception:
        return False, "Failed to update user role."


def set_account_status(email: str, is_active: bool) -> Tuple[bool, str]:
    """Enable/disable a user."""

    normalized_email = (email or "").strip().lower()

    if not normalized_email:
        return False, "Email is required."

    try:
        changed = set_user_active(normalized_email, is_active=is_active)
        if not changed:
            return False, "No changes were saved."

        if is_active:
            return True, "User enabled successfully."

        return True, "User disabled successfully."
    except Exception:
        return False, "Failed to update user status."
