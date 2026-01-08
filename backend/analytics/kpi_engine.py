"""KPI engine.

This module computes management KPIs from a stored optimization run.

Design goals:
- Transparent and explainable calculations.
- Uses the stored run outputs (production_rows / transport_rows / inventory_rows) plus the demand inputs.

Beginner note:
A KPI (Key Performance Indicator) is a single number that helps management answer:
- What happened?
- Is it good or bad?
- Where should we focus attention?
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import pandas as pd


@dataclass
class KPIResults:
    kpis: Dict[str, Any]


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


def _run_tables(run: Dict[str, Any]) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    prod_df = pd.DataFrame(run.get("production_rows", []) or [])
    trans_df = pd.DataFrame(run.get("transport_rows", []) or [])
    inv_df = pd.DataFrame(run.get("inventory_rows", []) or [])
    return prod_df, trans_df, inv_df


def compute_kpis(
    run: Dict[str, Any],
    demand_df: pd.DataFrame,
    safety_stock_by_plant: Dict[str, float],
    scenario_probabilities: Dict[str, float] | None = None,
) -> KPIResults:
    """Compute KPIs for a run.

    Args:
        run: optimization run document from MongoDB.
        demand_df: demand records for the same months and demand_type (or expected demand for uncertainty).
                  Must have columns: [plant_id, month, demand_quantity]
        safety_stock_by_plant: used for buffer metrics.
        scenario_probabilities: if scenario inventory exists and probabilities exist, we compute expected inventory.

    Returns:
        KPIResults with explainable KPI values.
    """

    prod_df, trans_df, inv_df = _run_tables(run)

    total_cost = _safe_float(run.get("objective_value", 0.0))
    cost_breakdown = run.get("cost_breakdown", {}) or {}

    prod_cost = _safe_float(cost_breakdown.get("production", 0.0))
    trans_cost = _safe_float(cost_breakdown.get("transport", 0.0))
    hold_cost = _safe_float(cost_breakdown.get("holding", 0.0))

    demand_total = 0.0
    if demand_df is not None and not demand_df.empty and "demand_quantity" in demand_df.columns:
        demand_total = float(demand_df["demand_quantity"].sum())

    # Service level:
    # In our optimization models, demand satisfaction is enforced as a hard constraint.
    # Therefore a successful solve implies 100% fulfillment.
    status = (run.get("status") or "").lower()
    service_level = 100.0 if status == "success" else 0.0

    cost_per_ton = 0.0
    if demand_total > 0:
        cost_per_ton = total_cost / demand_total

    # Average inventory:
    # - deterministic: average over (plant,month)
    # - uncertainty: if scenario exists, compute expected average using scenario probabilities if provided.
    avg_inventory = 0.0
    if inv_df is not None and not inv_df.empty and "inventory" in inv_df.columns:
        if "scenario" in inv_df.columns and scenario_probabilities:
            inv_df2 = inv_df.copy()
            inv_df2["prob"] = inv_df2["scenario"].map(lambda s: float(scenario_probabilities.get(str(s), 0.0)))
            # Expected inventory across scenarios:
            # E[Inv] = sum_s prob_s * Inv_s
            weighted = inv_df2["inventory"] * inv_df2["prob"]
            denom = inv_df2["prob"].sum()
            avg_inventory = float(weighted.sum() / denom) if denom > 0 else float(inv_df2["inventory"].mean())
        else:
            avg_inventory = float(inv_df["inventory"].mean())

    # Inventory turnover ratio (simple):
    # turnover = total demand / average inventory
    # High turnover usually means inventory is used efficiently.
    # Very low turnover may mean excess stock.
    inventory_turnover = 0.0
    if avg_inventory > 0:
        inventory_turnover = demand_total / avg_inventory

    # Buffer KPI (how far above safety stock inventory is on average)
    avg_buffer = 0.0
    if inv_df is not None and not inv_df.empty and "plant_id" in inv_df.columns and "inventory" in inv_df.columns:
        inv_df3 = inv_df.copy()
        inv_df3["safety_stock"] = inv_df3["plant_id"].map(lambda pid: float(safety_stock_by_plant.get(str(pid), 0.0)))
        inv_df3["buffer"] = inv_df3["inventory"] - inv_df3["safety_stock"]
        avg_buffer = float(inv_df3["buffer"].mean())

    kpis: Dict[str, Any] = {
        "total_cost": float(total_cost),
        "cost_production": float(prod_cost),
        "cost_transport": float(trans_cost),
        "cost_holding": float(hold_cost),
        "cost_per_ton": float(cost_per_ton),
        "service_level_percent": float(service_level),
        "total_demand": float(demand_total),
        "avg_inventory": float(avg_inventory),
        "inventory_turnover": float(inventory_turnover),
        "avg_inventory_buffer": float(avg_buffer),
    }

    return KPIResults(kpis=kpis)
