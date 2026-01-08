"""Simple result parser for simple feasible model.

This converts a solved simple model into:
- production table
- transport table
- inventory table
- cost breakdown
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import pandas as pd
import pyomo.environ as pyo


@dataclass
class SimpleOptimizationResults:
    production_df: pd.DataFrame
    transport_df: pd.DataFrame
    inventory_df: pd.DataFrame
    cost_breakdown: Dict[str, float]
    objective_value: float


def _safe_value(v) -> float:
    try:
        return float(pyo.value(v))
    except Exception:
        return 0.0


def parse_simple_results(model: pyo.ConcreteModel, plant_names: Dict[str, str]) -> SimpleOptimizationResults:
    """Parse a solved simple model into pandas DataFrames."""

    # Production plan
    prod_rows: List[Dict[str, Any]] = []
    for p in list(model.P):
        for t in list(model.T):
            qty = _safe_value(model.Prod[p, t])
            if qty != 0:
                prod_rows.append(
                    {
                        "plant_id": p,
                        "plant": plant_names.get(p, p),
                        "month": t,
                        "production": qty,
                    }
                )

    production_df = pd.DataFrame(prod_rows)

    # Transport plan
    ship_rows: List[Dict[str, Any]] = []
    for (i, j, k) in list(model.R):
        for t in list(model.T):
            ship_qty = _safe_value(model.Ship[i, j, k, t])
            trips = _safe_value(model.Trips[i, j, k, t])

            if ship_qty != 0:
                ship_rows.append(
                    {
                        "from_id": i,
                        "from": plant_names.get(i, i),
                        "to_id": j,
                        "to": plant_names.get(j, j),
                        "mode": k,
                        "month": t,
                        "shipment": ship_qty,
                        "trips": int(round(trips)) if trips > 0 else 0,
                    }
                )

    transport_df = pd.DataFrame(ship_rows)

    # Inventory plan
    inv_rows: List[Dict[str, Any]] = []
    for p in list(model.P):
        for t in list(model.T):
            inv = _safe_value(model.Inv[p, t])
            inv_rows.append(
                {
                    "plant_id": p,
                    "plant": plant_names.get(p, p),
                    "month": t,
                    "inventory": inv,
                }
            )

    inventory_df = pd.DataFrame(inv_rows)

    # Cost breakdown (simplified for simple model)
    prod_cost = sum(_safe_value(model.Prod[p, t]) * _safe_value(model.ProdCost[p]) for p in model.P for t in model.T)
    trans_cost = sum(_safe_value(model.RouteCost[i, j, k]) * _safe_value(model.Ship[i, j, k, t]) for (i, j, k) in model.R for t in model.T)
    hold_cost = sum(_safe_value(model.Inv[p, t]) * _safe_value(model.HoldCost[p]) for p in model.P for t in model.T)
    demand_penalty = sum(_safe_value(model.DemandPenalty) * _safe_value(model.DemandSlack[p, t]) for p in model.P for t in model.T)

    obj = _safe_value(model.TotalCost)

    return SimpleOptimizationResults(
        production_df=production_df,
        transport_df=transport_df,
        inventory_df=inventory_df,
        cost_breakdown={
            "production": float(prod_cost),
            "transport": float(trans_cost),
            "holding": float(hold_cost),
            "demand_penalty": float(demand_penalty),
        },
        objective_value=float(obj),
    )
