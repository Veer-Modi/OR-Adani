"""Utilization analysis.

This module computes utilization percentages for key assets:
- Production capacity utilization per plant
- Transport capacity utilization per route/mode (how full trips are)
- Storage utilization per plant

Why management cares:
- High utilization can indicate bottlenecks and risk of disruption.
- Low utilization can indicate wasted fixed assets.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import pandas as pd


@dataclass
class UtilizationResults:
    production_utilization_df: pd.DataFrame
    transport_utilization_df: pd.DataFrame
    storage_utilization_df: pd.DataFrame


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


def compute_utilization(
    run: Dict[str, Any],
    months: List[str],
    plant_names: Dict[str, str],
    production_capacity_by_plant: Dict[str, float],
    max_inventory_by_plant: Dict[str, float],
    route_capacity_per_trip: Dict[Tuple[str, str, str], float],
) -> UtilizationResults:
    prod_df = pd.DataFrame(run.get("production_rows", []) or [])
    trans_df = pd.DataFrame(run.get("transport_rows", []) or [])
    inv_df = pd.DataFrame(run.get("inventory_rows", []) or [])

    # Production utilization per plant (aggregated over months)
    prod_util_rows: List[Dict[str, Any]] = []
    if prod_df is not None and not prod_df.empty:
        prod_group = prod_df.groupby(["plant_id"], as_index=False)["production"].sum()
        for _, r in prod_group.iterrows():
            pid = str(r.get("plant_id"))
            produced = _safe_float(r.get("production"))
            cap = _safe_float(production_capacity_by_plant.get(pid, 0.0)) * max(len(months), 1)
            util = (produced / cap * 100.0) if cap > 0 else 0.0
            prod_util_rows.append(
                {
                    "plant_id": pid,
                    "plant": plant_names.get(pid, pid),
                    "production_total": produced,
                    "capacity_total": cap,
                    "utilization_percent": util,
                }
            )
    production_utilization_df = pd.DataFrame(prod_util_rows)

    # Transport utilization per route/mode: shipped / (trips * cap_per_trip)
    trans_util_rows: List[Dict[str, Any]] = []
    if trans_df is not None and not trans_df.empty:
        for _, r in trans_df.iterrows():
            i = str(r.get("from_id"))
            j = str(r.get("to_id"))
            mode = str(r.get("mode"))
            month = str(r.get("month"))
            shipped = _safe_float(r.get("shipment"))
            trips = _safe_float(r.get("trips"))
            cap_trip = _safe_float(route_capacity_per_trip.get((i, j, mode), 0.0))
            denom = trips * cap_trip
            util = (shipped / denom * 100.0) if denom > 0 else 0.0
            trans_util_rows.append(
                {
                    "from": plant_names.get(i, i),
                    "to": plant_names.get(j, j),
                    "from_id": i,
                    "to_id": j,
                    "mode": mode,
                    "month": month,
                    "shipment": shipped,
                    "trips": trips,
                    "cap_per_trip": cap_trip,
                    "trip_capacity_used": denom,
                    "utilization_percent": util,
                }
            )
    transport_utilization_df = pd.DataFrame(trans_util_rows)

    # Storage utilization per plant: avg inventory / max inventory
    storage_rows: List[Dict[str, Any]] = []
    if inv_df is not None and not inv_df.empty and "inventory" in inv_df.columns and "plant_id" in inv_df.columns:
        # If scenarios exist, use average across all rows (simple, consistent).
        inv_group = inv_df.groupby(["plant_id"], as_index=False)["inventory"].mean()
        for _, r in inv_group.iterrows():
            pid = str(r.get("plant_id"))
            avg_inv = _safe_float(r.get("inventory"))
            max_inv = _safe_float(max_inventory_by_plant.get(pid, 0.0))
            util = (avg_inv / max_inv * 100.0) if max_inv > 0 else 0.0
            storage_rows.append(
                {
                    "plant_id": pid,
                    "plant": plant_names.get(pid, pid),
                    "avg_inventory": avg_inv,
                    "max_inventory": max_inv,
                    "utilization_percent": util,
                }
            )
    storage_utilization_df = pd.DataFrame(storage_rows)

    return UtilizationResults(
        production_utilization_df=production_utilization_df,
        transport_utilization_df=transport_utilization_df,
        storage_utilization_df=storage_utilization_df,
    )
