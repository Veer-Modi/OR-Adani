"""Bottleneck detector.

A bottleneck is a constraint that limits performance.
In supply chains, bottlenecks usually appear as:
- plants operating near maximum capacity
- transport routes that are fully utilized
- inventory running near safety stock (little buffer)

This module produces clear, explainable flags that can be shown in a management dashboard.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import pandas as pd


@dataclass
class BottleneckResults:
    plant_bottlenecks: List[Dict[str, Any]]
    route_bottlenecks: List[Dict[str, Any]]
    inventory_bottlenecks: List[Dict[str, Any]]


def detect_bottlenecks(
    production_utilization_df: pd.DataFrame,
    transport_utilization_df: pd.DataFrame,
    inventory_df: pd.DataFrame,
    safety_stock_by_plant: Dict[str, float],
    plant_threshold_percent: float = 90.0,
    route_threshold_percent: float = 90.0,
    inventory_buffer_threshold: float = 1e-6,
) -> BottleneckResults:
    plant_bottlenecks: List[Dict[str, Any]] = []
    route_bottlenecks: List[Dict[str, Any]] = []
    inventory_bottlenecks: List[Dict[str, Any]] = []

    # Plants near max capacity
    if production_utilization_df is not None and not production_utilization_df.empty:
        df = production_utilization_df.copy()
        df = df[df["utilization_percent"] >= float(plant_threshold_percent)]
        for _, r in df.iterrows():
            plant_bottlenecks.append(
                {
                    "plant": r.get("plant"),
                    "utilization_percent": float(r.get("utilization_percent", 0.0) or 0.0),
                    "message": "Plant operating near max production capacity.",
                }
            )

    # Routes fully utilized (trip fill rate)
    if transport_utilization_df is not None and not transport_utilization_df.empty:
        df = transport_utilization_df.copy()
        df = df[(df["trips"] > 0) & (df["utilization_percent"] >= float(route_threshold_percent))]
        for _, r in df.iterrows():
            route_bottlenecks.append(
                {
                    "from": r.get("from"),
                    "to": r.get("to"),
                    "mode": r.get("mode"),
                    "month": r.get("month"),
                    "utilization_percent": float(r.get("utilization_percent", 0.0) or 0.0),
                    "message": "Route trips are near full capacity.",
                }
            )

    # Inventory consistently at safety stock (low buffer)
    if inventory_df is not None and not inventory_df.empty and "inventory" in inventory_df.columns and "plant_id" in inventory_df.columns:
        inv_df = inventory_df.copy()
        inv_df["safety_stock"] = inv_df["plant_id"].map(lambda pid: float(safety_stock_by_plant.get(str(pid), 0.0)))
        inv_df["buffer"] = inv_df["inventory"] - inv_df["safety_stock"]

        # If scenario exists, we treat each row independently and then group.
        grp_cols = ["plant_id", "plant"] if "plant" in inv_df.columns else ["plant_id"]
        min_buf = inv_df.groupby(grp_cols, as_index=False)["buffer"].min()
        min_buf = min_buf[min_buf["buffer"] <= float(inventory_buffer_threshold)]

        for _, r in min_buf.iterrows():
            inventory_bottlenecks.append(
                {
                    "plant": r.get("plant") or r.get("plant_id"),
                    "min_buffer": float(r.get("buffer", 0.0) or 0.0),
                    "message": "Inventory hits safety stock (low buffer).",
                }
            )

    return BottleneckResults(
        plant_bottlenecks=plant_bottlenecks,
        route_bottlenecks=route_bottlenecks,
        inventory_bottlenecks=inventory_bottlenecks,
    )
