"""Uncertainty service.

This service is the single place that:
- stores / loads demand uncertainty settings from MongoDB
- validates settings (probabilities, multipliers)
- exposes scenario definitions to the UI and optimization run page

We store a SINGLE document ("global settings") to keep Phase 4 simple.
If later you want site-specific scenarios, you can extend the schema.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from backend.database.mongo import get_demand_uncertainty_collection


_DEFAULT_SETTINGS = {
    "key": "global",
    "is_enabled": False,
    "scenarios": [
        {"name": "Low", "probability": 0.2, "demand_multiplier": 0.9},
        {"name": "Normal", "probability": 0.6, "demand_multiplier": 1.0},
        {"name": "High", "probability": 0.2, "demand_multiplier": 1.1},
    ],
}


def _validate_settings(settings: Dict[str, Any]) -> Tuple[bool, str]:
    scenarios = settings.get("scenarios") or []
    if not isinstance(scenarios, list) or not scenarios:
        return False, "At least one scenario is required."

    names = []
    total_p = 0.0

    for s in scenarios:
        name = (s.get("name") or "").strip()
        if not name:
            return False, "Scenario name is required."
        names.append(name)

        try:
            p = float(s.get("probability"))
        except Exception:
            return False, f"Probability for {name} must be a number."
        if p < 0:
            return False, f"Probability for {name} cannot be negative."
        total_p += p

        try:
            mult = float(s.get("demand_multiplier"))
        except Exception:
            return False, f"Demand multiplier for {name} must be a number."
        if mult < 0:
            return False, f"Demand multiplier for {name} cannot be negative."

    if len(set(names)) != len(names):
        return False, "Scenario names must be unique."

    if abs(total_p - 1.0) > 1e-6:
        return False, "Scenario probabilities must sum to 1."

    return True, ""


def get_uncertainty_settings() -> Dict[str, Any]:
    coll = get_demand_uncertainty_collection()
    doc = coll.find_one({"key": "global"})
    if doc is None:
        # Create defaults on first use.
        coll.insert_one(dict(_DEFAULT_SETTINGS))
        doc = coll.find_one({"key": "global"})
    return doc or dict(_DEFAULT_SETTINGS)


def upsert_uncertainty_settings(payload: Dict[str, Any]) -> Tuple[bool, str]:
    doc = {
        "key": "global",
        "is_enabled": bool(payload.get("is_enabled", False)),
        "scenarios": payload.get("scenarios") or [],
    }

    ok, msg = _validate_settings(doc)
    if not ok:
        return False, msg

    coll = get_demand_uncertainty_collection()
    coll.update_one({"key": "global"}, {"$set": doc}, upsert=True)
    return True, "Uncertainty settings saved."


def get_scenarios_for_optimization() -> Tuple[bool, str, bool, List[Dict[str, Any]]]:
    """Return scenarios for the optimizer.

    Returns:
        (ok, message, is_enabled, scenarios)
    """

    settings = get_uncertainty_settings()
    is_enabled = bool(settings.get("is_enabled", False))
    scenarios = settings.get("scenarios") or []

    ok, msg = _validate_settings({"scenarios": scenarios})
    if not ok:
        return False, msg, is_enabled, []

    # Normalize values (float conversion)
    norm: List[Dict[str, Any]] = []
    for s in scenarios:
        norm.append(
            {
                "name": (s.get("name") or "").strip(),
                "probability": float(s.get("probability")),
                "demand_multiplier": float(s.get("demand_multiplier")),
            }
        )

    return True, "", is_enabled, norm
