"""Stochastic (scenario-based) optimization model.

Business meaning:
- We pick ONE production & transport plan that we commit to.
- Demand can realize as Low/Normal/High.
- Inventory levels are allowed to differ by scenario (because the same plan will lead to different stock outcomes).

Goal:
- Minimize expected total cost = production + transport + expected holding cost.

Important modeling choice:
- Production/shipments are "here-and-now" (shared across scenarios).
- Inventory is "recourse" (scenario-specific state variable).

This keeps the model relatively small while capturing the key trade-off:
- Higher production/shipments can protect against high-demand scenarios, but increases cost.
"""

from __future__ import annotations

from typing import Tuple

import pyomo.environ as pyo

from backend.optimization.data_loader import OptimizationData
from backend.uncertainty.scenario_generator import ScenarioDemandData


def build_stochastic_model(data: OptimizationData, scen: ScenarioDemandData) -> pyo.ConcreteModel:
    m = pyo.ConcreteModel()

    # Sets
    m.P = pyo.Set(initialize=data.plant_ids, ordered=True)
    m.T = pyo.Set(initialize=data.months, ordered=True)
    m.R = pyo.Set(initialize=data.routes, dimen=3)
    m.CL = pyo.Set(initialize=data.clinker_plants, within=m.P)
    m.S = pyo.Set(initialize=scen.scenario_names, ordered=True)

    # Parameters
    m.StorageCap = pyo.Param(m.P, initialize=data.storage_capacity)
    m.InitialInv = pyo.Param(m.P, initialize=data.initial_inventory)

    m.SafetyStock = pyo.Param(m.P, initialize=data.safety_stock)
    m.MaxInv = pyo.Param(m.P, initialize=data.max_inventory)
    m.HoldCost = pyo.Param(m.P, initialize=data.holding_cost)

    m.ProdCap = pyo.Param(m.P, initialize=data.production_capacity)
    m.ProdCost = pyo.Param(m.P, initialize=data.production_cost)

    m.RouteEnabled = pyo.Param(m.R, initialize=data.route_enabled, within=pyo.Boolean)
    m.CostPerTrip = pyo.Param(m.R, initialize=data.transport_cost_per_trip)
    m.CapPerTrip = pyo.Param(m.R, initialize=data.transport_capacity_per_trip)
    m.SBQ = pyo.Param(m.R, initialize=data.transport_sbq)

    def _demand_init(mm, s, p, t):
        return float(scen.demand.get((s, p, t), 0.0) or 0.0)

    m.Demand = pyo.Param(m.S, m.P, m.T, initialize=_demand_init)
    m.Prob = pyo.Param(m.S, initialize=scen.probability)

    # Shared decisions
    m.Prod = pyo.Var(m.P, m.T, within=pyo.NonNegativeReals)
    m.Ship = pyo.Var(m.R, m.T, within=pyo.NonNegativeReals)
    m.Trips = pyo.Var(m.R, m.T, within=pyo.NonNegativeIntegers)
    m.UseMode = pyo.Var(m.R, m.T, within=pyo.Binary)

    # Scenario-specific inventory
    m.Inv = pyo.Var(m.S, m.P, m.T, within=pyo.NonNegativeReals)

    # Constraints
    def prod_cap_rule(mm, p, t):
        if p not in mm.CL:
            return mm.Prod[p, t] == 0
        return mm.Prod[p, t] <= mm.ProdCap[p]

    m.ProductionCapacity = pyo.Constraint(m.P, m.T, rule=prod_cap_rule)

    # If a route is disabled, force shipments, trips, and mode selection to 0.
    def route_enabled_ship_rule(mm, i, j, mode, t):
        if bool(mm.RouteEnabled[i, j, mode]):
            return pyo.Constraint.Skip
        return mm.Ship[i, j, mode, t] == 0

    def route_enabled_trips_rule(mm, i, j, mode, t):
        if bool(mm.RouteEnabled[i, j, mode]):
            return pyo.Constraint.Skip
        return mm.Trips[i, j, mode, t] == 0

    def route_enabled_use_rule(mm, i, j, mode, t):
        if bool(mm.RouteEnabled[i, j, mode]):
            return pyo.Constraint.Skip
        return mm.UseMode[i, j, mode, t] == 0

    m.RouteEnabledShip = pyo.Constraint(m.R, m.T, rule=route_enabled_ship_rule)
    m.RouteEnabledTrips = pyo.Constraint(m.R, m.T, rule=route_enabled_trips_rule)
    m.RouteEnabledUse = pyo.Constraint(m.R, m.T, rule=route_enabled_use_rule)

    def trip_capacity_rule(mm, i, j, mode, t):
        return mm.Ship[i, j, mode, t] <= mm.Trips[i, j, mode, t] * mm.CapPerTrip[i, j, mode]

    m.TripCapacity = pyo.Constraint(m.R, m.T, rule=trip_capacity_rule)

    def sbq_rule(mm, i, j, mode, t):
        return mm.Ship[i, j, mode, t] >= mm.Trips[i, j, mode, t] * mm.SBQ[i, j, mode]

    m.SBQConstr = pyo.Constraint(m.R, m.T, rule=sbq_rule)

    # Mode selection: at most 1 mode for each (i,j,t)
    def mode_selection_rule(mm, i, j, t):
        modes = [m for (ii, jj, m) in mm.R if ii == i and jj == j]
        if not modes:
            return pyo.Constraint.Skip
        return sum(mm.UseMode[i, j, m, t] for m in modes) <= 1

    ij_pairs = sorted({(i, j) for (i, j, _m) in data.routes})
    m.IJ = pyo.Set(initialize=ij_pairs, dimen=2)
    m.ModeSelection = pyo.Constraint(m.IJ, m.T, rule=mode_selection_rule)

    # Big-M linking trips and UseMode
    BIG_M = 10_000

    def trips_usemode_rule(mm, i, j, mode, t):
        return mm.Trips[i, j, mode, t] <= BIG_M * mm.UseMode[i, j, mode, t]

    m.TripsUseMode = pyo.Constraint(m.R, m.T, rule=trips_usemode_rule)

    # Inventory balance per scenario
    def inv_balance_rule(mm, s, p, t):
        t_list = list(mm.T)
        idx = t_list.index(t)
        prev_inv = mm.InitialInv[p] if idx == 0 else mm.Inv[s, p, t_list[idx - 1]]

        inbound = sum(mm.Ship[i, p, mode, t] for (i, j, mode) in mm.R if j == p)
        outbound = sum(mm.Ship[p, j, mode, t] for (i, j, mode) in mm.R if i == p)

        return mm.Inv[s, p, t] == prev_inv + mm.Prod[p, t] + inbound - outbound - mm.Demand[s, p, t]

    m.InventoryBalance = pyo.Constraint(m.S, m.P, m.T, rule=inv_balance_rule)

    def safety_stock_rule(mm, s, p, t):
        return mm.Inv[s, p, t] >= mm.SafetyStock[p]

    m.SafetyStockConstr = pyo.Constraint(m.S, m.P, m.T, rule=safety_stock_rule)

    def max_inv_rule(mm, s, p, t):
        return mm.Inv[s, p, t] <= mm.MaxInv[p]

    m.MaxInvConstr = pyo.Constraint(m.S, m.P, m.T, rule=max_inv_rule)

    # Objective: production + transport + expected holding
    def expected_cost_obj(mm):
        prod_cost = sum(mm.ProdCost[p] * mm.Prod[p, t] for p in mm.P for t in mm.T)
        trans_cost = sum(mm.CostPerTrip[i, j, mode] * mm.Trips[i, j, mode, t] for (i, j, mode) in mm.R for t in mm.T)
        hold_cost = sum(mm.Prob[s] * mm.HoldCost[p] * mm.Inv[s, p, t] for s in mm.S for p in mm.P for t in mm.T)
        return prod_cost + trans_cost + hold_cost

    m.Objective = pyo.Objective(rule=expected_cost_obj, sense=pyo.minimize)

    return m
