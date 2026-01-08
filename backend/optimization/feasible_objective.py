"""Feasible optimization objective with demand slack penalties.

This file defines the objective function that includes penalties for unmet demand
to ensure the model can find a feasible solution even with constraints violations.
"""

from __future__ import annotations

import pyomo.environ as pyo


def add_feasible_objective(model: pyo.ConcreteModel) -> None:
    """Add objective function with demand slack penalties to the model."""

    # Production cost component
    production_cost = (
        sum(model.ProdCost[p] * model.Prod[p, t] for p in model.P for t in model.T)
    )

    # Transportation cost component
    transport_cost = (
        sum(model.RouteCost[i, j, k] * model.Ship[i, j, k, t] 
            for (i, j, k) in model.R for t in model.T)
    )

    # Inventory holding cost component
    holding_cost = (
        sum(model.HoldCost[p] * model.Inv[p, t] for p in model.P for t in model.T)
    )

    # Penalty for unmet demand (high penalty to minimize slack)
    demand_penalty = (
        sum(model.DemandPenalty * model.DemandSlack[p, t] 
            for p in model.P for t in model.T)
    )

    # Total objective: minimize total cost + demand penalties
    total_cost = production_cost + transport_cost + holding_cost + demand_penalty

    model.TotalCost = pyo.Objective(
        expr=total_cost,
        sense=pyo.minimize,
        doc="Minimize total cost including unmet demand penalties"
    )
