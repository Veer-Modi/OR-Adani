"""Uncertainty result parser.

We keep this separate from backend/optimization/result_parser.py because:
- deterministic model has Inv[p,t]
- stochastic/robust models have Inv[s,p,t]

This module converts a solved uncertainty model into pandas DataFrames that the UI can display.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pandas as pd
import pyomo.environ as pyo


@dataclass
class UncertaintyResults:
    production_df: pd.DataFrame
    transport_df: pd.DataFrame
    inventory_df: pd.DataFrame
    cost_breakdown: Dict[str, float]
    objective_value: float
    scenario_probabilities: Dict[str, float]


def _safe_value(v) -> float:
    try:
        return float(pyo.value(v))
    except Exception:
        return 0.0


def parse_uncertainty_results(model: pyo.ConcreteModel, plant_names: Dict[str, str]) -> UncertaintyResults:
    """Parse a solved stochastic/robust model.

    Expected model components:
    - P, T, R, S sets
    - Prod[p,t], Ship[i,j,mode,t], Trips[i,j,mode,t]
    - Inv[s,p,t]

    Optional:
    - Prob[s] for expected-cost model
    - WorstHoldCost for robust model
    """

    # Production plan (shared)
    prod_rows: List[Dict[str, Any]] = []
    for p in list(model.P):
        for t in list(model.T):
            qty = _safe_value(model.Prod[p, t])
            if qty != 0:
                prod_rows.append({"plant_id": p, "plant": plant_names.get(p, p), "month": t, "production": qty})
    production_df = pd.DataFrame(prod_rows)

    # Transport plan (shared)
    ship_rows: List[Dict[str, Any]] = []
    for (i, j, k) in list(model.R):
        for t in list(model.T):
            ship_qty = _safe_value(model.Ship[i, j, k, t])
            trips = _safe_value(model.Trips[i, j, k, t])
            if ship_qty != 0 or trips != 0:
                ship_rows.append(
                    {
                        "from_id": i,
                        "from": plant_names.get(i, i),
                        "to_id": j,
                        "to": plant_names.get(j, j),
                        "mode": k,
                        "month": t,
                        "shipment": ship_qty,
                        "trips": int(round(trips)),
                    }
                )
    transport_df = pd.DataFrame(ship_rows)

    # Inventory plan (scenario-specific)
    inv_rows: List[Dict[str, Any]] = []
    for s in list(model.S):
        for p in list(model.P):
            for t in list(model.T):
                inv = _safe_value(model.Inv[s, p, t])
                inv_rows.append(
                    {
                        "scenario": s,
                        "plant_id": p,
                        "plant": plant_names.get(p, p),
                        "month": t,
                        "inventory": inv,
                    }
                )
    inventory_df = pd.DataFrame(inv_rows)

    # Scenario probabilities (if present)
    scen_prob: Dict[str, float] = {}
    if hasattr(model, "Prob"):
        for s in list(model.S):
            scen_prob[str(s)] = _safe_value(model.Prob[s])

    # Cost breakdown
    prod_cost = sum(_safe_value(model.Prod[p, t]) * _safe_value(model.ProdCost[p]) for p in model.P for t in model.T)
    trans_cost = sum(
        _safe_value(model.Trips[i, j, k, t]) * _safe_value(model.CostPerTrip[i, j, k])
        for (i, j, k) in model.R
        for t in model.T
    )

    hold_cost: float = 0.0
    if hasattr(model, "Prob"):
        hold_cost = sum(
            _safe_value(model.Prob[s]) * _safe_value(model.HoldCost[p]) * _safe_value(model.Inv[s, p, t])
            for s in model.S
            for p in model.P
            for t in model.T
        )
    else:
        # Robust model does not use expected holding; it minimizes WorstHoldCost.
        if hasattr(model, "WorstHoldCost"):
            hold_cost = _safe_value(model.WorstHoldCost)

    obj = _safe_value(model.Objective)

    return UncertaintyResults(
        production_df=production_df,
        transport_df=transport_df,
        inventory_df=inventory_df,
        cost_breakdown={"production": float(prod_cost), "transport": float(trans_cost), "holding": float(hold_cost)},
        objective_value=float(obj),
        scenario_probabilities=scen_prob,
    )
