"""Optimization objective.

Business goal:
Minimize total cost:
- Production cost
- Transport cost
- Inventory holding cost

Beginner tip:
- An objective tells the solver what to optimize.
- The solver finds the cheapest plan that satisfies all constraints.
"""

from __future__ import annotations

import pyomo.environ as pyo


def add_objective(model: pyo.ConcreteModel) -> None:
    """Add the objective function to the model."""

    def total_cost_rule(m: pyo.ConcreteModel):
        production_cost = sum(m.Prod[p, t] * m.ProdCost[p] for p in m.P for t in m.T)

        transport_cost = sum(
            m.Trips[i, j, k, t] * m.RouteCost[i, j, k]
            for (i, j, k) in m.R
            for t in m.T
        )

        holding_cost = sum(m.Inv[p, t] * m.HoldCost[p] for p in m.P for t in m.T)

        return production_cost + transport_cost + holding_cost

    model.TotalCost = pyo.Objective(rule=total_cost_rule, sense=pyo.minimize)
