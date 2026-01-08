"""Results service.

This service:
- Saves solved optimization results into MongoDB
- Lists run history
- Loads a single run

We keep this logic away from Streamlit UI.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from backend.results.result_repository import create_run, find_run_by_id, list_runs


def _df_to_rows(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Convert a DataFrame to JSON-like rows for MongoDB."""

    if df is None or df.empty:
        return []

    return df.to_dict(orient="records")


def save_optimization_run(
    created_by_email: str,
    months: List[str],
    solver: str,
    demand_type: str,
    status: str,
    message: str,
    objective_value: float,
    cost_breakdown: Dict[str, float],
    production_df: pd.DataFrame,
    transport_df: pd.DataFrame,
    inventory_df: pd.DataFrame,
    optimization_type: str | None = None,
    scenarios: List[Dict[str, Any]] | None = None,
    scenario_probabilities: Dict[str, float] | None = None,
    summary_metrics: Dict[str, Any] | None = None,
) -> Tuple[bool, str, str | None]:
    """Save an optimization run to MongoDB."""

    try:
        run_id = create_run(
            {
                "created_by_email": created_by_email,
                "months": months,
                "solver": solver,
                "demand_type": demand_type,
                "optimization_type": optimization_type or "deterministic",
                "scenarios": scenarios or [],
                "scenario_probabilities": scenario_probabilities or {},
                "status": status,
                "message": message,
                "objective_value": float(objective_value),
                "cost_breakdown": {
                    "production": float(cost_breakdown.get("production", 0.0)),
                    "transport": float(cost_breakdown.get("transport", 0.0)),
                    "holding": float(cost_breakdown.get("holding", 0.0)),
                },
                "production_rows": _df_to_rows(production_df),
                "transport_rows": _df_to_rows(transport_df),
                "inventory_rows": _df_to_rows(inventory_df),
                "summary_metrics": summary_metrics or {},
            }
        )
        return True, "Optimization run saved.", run_id
    except Exception:
        return False, "Failed to save optimization run.", None


def get_recent_runs(limit: int = 20) -> List[Dict[str, Any]]:
    """List recent runs."""

    return list_runs(limit=limit)


def get_run(run_id: str) -> Optional[Dict[str, Any]]:
    """Load a run by id."""

    return find_run_by_id(run_id)
