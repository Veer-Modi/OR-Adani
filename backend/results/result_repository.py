"""Optimization results repository (MongoDB CRUD).

We store optimization runs so users can view history.

Document shape (simplified):
{
  created_at: datetime,
  created_by_email: str,
  months: ["YYYY-MM", ...],
  solver: str,
  demand_type: str,
  status: str,
  message: str,
  objective_value: float,
  cost_breakdown: {production: float, transport: float, holding: float},
  production_rows: [ ... ],
  transport_rows: [ ... ],
  inventory_rows: [ ... ]
}
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId

from backend.database.mongo import get_optimization_results_collection


def create_run(doc: Dict[str, Any]) -> str:
    """Insert a new optimization run document and return its id."""

    results = get_optimization_results_collection()

    final_doc = dict(doc)
    final_doc["created_at"] = datetime.now(timezone.utc)

    inserted = results.insert_one(final_doc)
    return str(inserted.inserted_id)


def list_runs(limit: int = 20) -> List[Dict[str, Any]]:
    """List recent optimization runs."""

    results = get_optimization_results_collection()

    return list(results.find({}).sort("created_at", -1).limit(int(limit)))


def find_run_by_id(run_id: str) -> Optional[Dict[str, Any]]:
    """Fetch one run by its MongoDB _id."""

    results = get_optimization_results_collection()

    try:
        oid = ObjectId(run_id)
    except Exception:
        return None

    return results.find_one({"_id": oid})


def update_run_fields(run_id: str, fields: Dict[str, Any]) -> bool:
    """Update selected fields on an existing run.

    This is used by Phase 5 analytics to store computed KPIs and insights.
    """

    results = get_optimization_results_collection()

    try:
        oid = ObjectId(run_id)
    except Exception:
        return False

    update_doc = {"$set": dict(fields or {})}
    res = results.update_one({"_id": oid}, update_doc)
    return res.matched_count == 1
