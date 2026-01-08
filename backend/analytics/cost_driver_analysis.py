"""Cost driver analysis.

Goal:
- Identify where cost is coming from (top plants, top routes, top modes)

Why management cares:
- It answers "what should we optimize operationally next?"
  - renegotiate a route contract?
  - increase capacity at a plant?
  - shift to a cheaper mode?

All calculations are based on:
- stored optimization outputs
- master data (production cost, route cost)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import pandas as pd


@dataclass
class CostDriverResults:
    top_plants_df: pd.DataFrame
    top_routes_df: pd.DataFrame
    mode_cost_df: pd.DataFrame


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


def compute_cost_drivers(
    run: Dict[str, Any],
    plant_names: Dict[str, str],
    production_cost_by_plant: Dict[str, float],
    route_cost_per_trip: Dict[Tuple[str, str, str], float],
) -> CostDriverResults:
    prod_df = pd.DataFrame(run.get("production_rows", []) or [])
    trans_df = pd.DataFrame(run.get("transport_rows", []) or [])

    # Plant production cost contribution
    plant_rows: List[Dict[str, Any]] = []
    if prod_df is not None and not prod_df.empty and "plant_id" in prod_df.columns:
        prod_df2 = prod_df.copy()
        prod_df2["unit_cost"] = prod_df2["plant_id"].map(lambda pid: _safe_float(production_cost_by_plant.get(str(pid), 0.0)))
        prod_df2["cost"] = prod_df2["production"].map(_safe_float) * prod_df2["unit_cost"]
        grp = prod_df2.groupby(["plant_id"], as_index=False)["cost"].sum().sort_values("cost", ascending=False)
        for _, r in grp.head(3).iterrows():
            pid = str(r.get("plant_id"))
            plant_rows.append({"plant": plant_names.get(pid, pid), "plant_id": pid, "cost": float(r.get("cost", 0.0) or 0.0)})
    top_plants_df = pd.DataFrame(plant_rows)

    # Route transport cost contribution
    route_rows: List[Dict[str, Any]] = []
    if trans_df is not None and not trans_df.empty:
        trans_df2 = trans_df.copy()
        trans_df2["route_cost_per_trip"] = trans_df2.apply(
            lambda r: _safe_float(route_cost_per_trip.get((str(r.get("from_id")), str(r.get("to_id")), str(r.get("mode"))), 0.0)),
            axis=1,
        )
        trans_df2["cost"] = trans_df2["route_cost_per_trip"] * trans_df2["trips"].map(_safe_float)
        grp_cols = ["from_id", "to_id", "mode"]
        grp = trans_df2.groupby(grp_cols, as_index=False)["cost"].sum().sort_values("cost", ascending=False)
        for _, r in grp.head(3).iterrows():
            i = str(r.get("from_id"))
            j = str(r.get("to_id"))
            mode = str(r.get("mode"))
            route_rows.append(
                {
                    "from": plant_names.get(i, i),
                    "to": plant_names.get(j, j),
                    "mode": mode,
                    "cost": float(r.get("cost", 0.0) or 0.0),
                }
            )
    top_routes_df = pd.DataFrame(route_rows)

    # Most expensive transport mode
    mode_df = pd.DataFrame()
    if trans_df is not None and not trans_df.empty and "mode" in trans_df.columns:
        trans_df3 = trans_df.copy()
        trans_df3["route_cost_per_trip"] = trans_df3.apply(
            lambda r: _safe_float(route_cost_per_trip.get((str(r.get("from_id")), str(r.get("to_id")), str(r.get("mode"))), 0.0)),
            axis=1,
        )
        trans_df3["cost"] = trans_df3["route_cost_per_trip"] * trans_df3["trips"].map(_safe_float)
        mode_df = trans_df3.groupby(["mode"], as_index=False)["cost"].sum().sort_values("cost", ascending=False)

    return CostDriverResults(
        top_plants_df=top_plants_df,
        top_routes_df=top_routes_df,
        mode_cost_df=mode_df,
    )
