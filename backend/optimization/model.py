"""Pyomo model builder.

This file creates the Pyomo model:
- sets (plants, months, routes)
- parameters (demand, costs, capacities)
- decision variables (production, shipping, trips, inventory)

We keep constraints and objective in separate files for readability.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import pyomo.environ as pyo

from backend.optimization.constraints import add_constraints
from backend.optimization.data_loader import OptimizationData
from backend.optimization.excel_loader import ExcelOptimizationData
from backend.optimization.objective import add_objective


def build_model(data: OptimizationData) -> pyo.ConcreteModel:
    """Build a deterministic multi-period clinker allocation model."""

    m = pyo.ConcreteModel()

    # -----------------------------
    # Sets
    # -----------------------------

    m.P = pyo.Set(initialize=data.plant_ids, ordered=True)  # all plants
    m.T = pyo.Set(initialize=data.months, ordered=True)  # time periods (months)

    # Route keys are tuples: (from_id, to_id, mode)
    m.R = pyo.Set(initialize=data.routes, dimen=3)

    # Clinker plants (subset of plants)
    m.CL = pyo.Set(initialize=data.clinker_plants, within=m.P)

    # For convenience: set of (i,j) pairs that exist in routes
    ij_pairs = sorted({(i, j) for (i, j, k) in data.routes})
    m.IJ = pyo.Set(initialize=ij_pairs, dimen=2)

    # Previous time mapping (for inventory balance)
    months = list(data.months)
    prev_map: Dict[str, str | None] = {}
    for idx, t in enumerate(months):
        if idx == 0:
            prev_map[t] = None
        else:
            prev_map[t] = months[idx - 1]

    m.PREV_T = prev_map

    # -----------------------------
    # Parameters
    # -----------------------------

    m.Inv0 = pyo.Param(m.P, initialize=data.initial_inventory, within=pyo.NonNegativeReals)

    m.Safety = pyo.Param(m.P, initialize=data.safety_stock, within=pyo.NonNegativeReals)
    m.MaxInv = pyo.Param(m.P, initialize=data.max_inventory, within=pyo.NonNegativeReals)
    m.HoldCost = pyo.Param(m.P, initialize=data.holding_cost, within=pyo.NonNegativeReals)

    m.ProdCap = pyo.Param(m.P, initialize=data.production_capacity, within=pyo.NonNegativeReals)
    m.ProdCost = pyo.Param(m.P, initialize=data.production_cost, within=pyo.NonNegativeReals)

    # Demand parameter: dict keyed by (plant_id, month)
    m.Demand = pyo.Param(m.P, m.T, initialize=data.demand, within=pyo.NonNegativeReals)

    m.RouteCost = pyo.Param(m.R, initialize=data.transport_cost_per_trip, within=pyo.NonNegativeReals)
    m.RouteCap = pyo.Param(m.R, initialize=data.transport_capacity_per_trip, within=pyo.NonNegativeReals)
    m.RouteSBQ = pyo.Param(m.R, initialize=data.transport_sbq, within=pyo.NonNegativeReals)

    # Route enabled flag (bool)
    m.RouteEnabled = pyo.Param(m.R, initialize=data.route_enabled, within=pyo.Boolean)
    
    # Excel-specific parameters (if using ExcelOptimizationData)
    if isinstance(data, ExcelOptimizationData):
        # Min fulfillment percentage (optional)
        min_fulfillment_dict = {}
        for (iugu_code, period), pct in data.min_fulfillment.items():
            if iugu_code in data.plant_ids and period in data.months:
                min_fulfillment_dict[(iugu_code, period)] = pct
        if min_fulfillment_dict:
            m.MinFulfillment = pyo.Param(m.P, m.T, initialize=min_fulfillment_dict, default=0.0, within=pyo.NonNegativeReals)
        
        # Min closing stock (optional)
        min_closing_dict = {}
        for (iugu_code, period), value in data.min_closing_stock.items():
            if iugu_code in data.plant_ids and period in data.months:
                min_closing_dict[(iugu_code, period)] = value
        if min_closing_dict:
            m.MinClosingStock = pyo.Param(m.P, m.T, initialize=min_closing_dict, default=0.0, within=pyo.NonNegativeReals)
        
        # Max closing stock (optional)
        max_closing_dict = {}
        for (iugu_code, period), value in data.max_closing_stock.items():
            if iugu_code in data.plant_ids and period in data.months:
                max_closing_dict[(iugu_code, period)] = value
        if max_closing_dict:
            m.MaxClosingStock = pyo.Param(m.P, m.T, initialize=max_closing_dict, default=float('inf'), within=pyo.NonNegativeReals)
        
        # Transport code limits
        transport_code_limit_set = []
        transport_code_limit_dict = {}
        for (iu_code, transport_code, period), limits in data.transport_code_limits.items():
            if iu_code in data.plant_ids and period in data.months:
                transport_code_limit_set.append((iu_code, transport_code, period))
                transport_code_limit_dict[(iu_code, transport_code, period)] = limits
        if transport_code_limit_set:
            m.TransportCodeLimitSet = pyo.Set(initialize=transport_code_limit_set, dimen=3)
            m.TransportCodeLimits = pyo.Param(m.TransportCodeLimitSet, initialize=transport_code_limit_dict)
        
        # Transport bounds (route-specific)
        transport_bound_set = []
        transport_bound_dict = {}
        for (iu_code, transport_code, iugu_code, period), bounds in data.transport_bounds.items():
            if (iu_code, iugu_code, transport_code) in data.routes and period in data.months:
                transport_bound_set.append((iu_code, iugu_code, transport_code, period))
                transport_bound_dict[(iu_code, iugu_code, transport_code, period)] = bounds
        if transport_bound_set:
            m.TransportBoundSet = pyo.Set(initialize=transport_bound_set, dimen=4)
            m.TransportBounds = pyo.Param(m.TransportBoundSet, initialize=transport_bound_dict)

    # -----------------------------
    # Decision variables
    # -----------------------------

    # Production for each plant and month.
    # For non-clinker plants, we will fix production to 0.
    m.Prod = pyo.Var(m.P, m.T, domain=pyo.NonNegativeReals)

    # Shipped clinker quantity per route and month.
    m.Ship = pyo.Var(m.R, m.T, domain=pyo.NonNegativeReals)

    # Integer trips per route and month.
    m.Trips = pyo.Var(m.R, m.T, domain=pyo.NonNegativeIntegers)

    # Mode selection binary variable.
    m.Use = pyo.Var(m.R, m.T, domain=pyo.Binary)

    # Inventory at each plant per month.
    m.Inv = pyo.Var(m.P, m.T, domain=pyo.NonNegativeReals)

    # Fix production to 0 for non-clinker plants.
    non_clinker = [pid for pid in data.plant_ids if pid not in set(data.clinker_plants)]
    for p in non_clinker:
        for t in data.months:
            m.Prod[p, t].fix(0)

    # -----------------------------
    # Constraints + Objective
    # -----------------------------

    add_constraints(m)
    add_objective(m)

    return m
