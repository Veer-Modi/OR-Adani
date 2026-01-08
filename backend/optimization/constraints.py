"""Optimization constraints.

This file defines the mathematical constraints.

Beginner tip:
- A constraint is a rule the plan must follow.
- Pyomo constraints are written as Python functions returning an equation.

Real-world meaning of key constraints:
- Production capacity: you cannot produce more than a plant can make
- Inventory balance: inventory today = inventory yesterday + in - out - demand
- Safety stock: keep minimum inventory to avoid stockouts
- Max inventory: storage tanks/silos have limits
- Transport trip capacity: each trip can only carry so much
- SBQ: if you decide to ship, there is a minimum shipment batch
- Mode selection: you can choose at most one mode per route per month
"""

from __future__ import annotations

from typing import Tuple

import pyomo.environ as pyo


def add_constraints(model: pyo.ConcreteModel, big_m_trips: int = 10_000) -> None:
    """Add all constraints to the model."""

    # Production capacity for clinker plants.
    def production_capacity_rule(m: pyo.ConcreteModel, p: str, t: str):
        return m.Prod[p, t] <= m.ProdCap[p]

    model.ProductionCapacity = pyo.Constraint(model.CL, model.T, rule=production_capacity_rule)

    # Inventory balance (multi-period).
    def inventory_balance_rule(m: pyo.ConcreteModel, p: str, t: str):
        prev_t = m.PREV_T[t]

        inflow = sum(m.Ship[i, p, k, t] for (i, j, k) in m.R if j == p)
        outflow = sum(m.Ship[p, j, k, t] for (i, j, k) in m.R if i == p)

        # Only clinker plants can produce. For grinding plants, Prod is fixed at 0.
        prod = m.Prod[p, t]

        if prev_t is None:
            return m.Inv[p, t] == m.Inv0[p] + prod + inflow - outflow - m.Demand[p, t]

        return m.Inv[p, t] == m.Inv[p, prev_t] + prod + inflow - outflow - m.Demand[p, t]

    model.InventoryBalance = pyo.Constraint(model.P, model.T, rule=inventory_balance_rule)

    # Inventory must be at least safety stock.
    def safety_stock_rule(m: pyo.ConcreteModel, p: str, t: str):
        return m.Inv[p, t] >= m.Safety[p]

    model.SafetyStock = pyo.Constraint(model.P, model.T, rule=safety_stock_rule)

    # Inventory cannot exceed max storage.
    def max_inventory_rule(m: pyo.ConcreteModel, p: str, t: str):
        return m.Inv[p, t] <= m.MaxInv[p]

    model.MaxInventory = pyo.Constraint(model.P, model.T, rule=max_inventory_rule)

    # Trip capacity: shipped quantity cannot exceed capacity per trip * number of trips.
    def trip_capacity_rule(m: pyo.ConcreteModel, i: str, j: str, k: str, t: str):
        return m.Ship[i, j, k, t] <= m.Trips[i, j, k, t] * m.RouteCap[i, j, k]

    model.TripCapacity = pyo.Constraint(model.R, model.T, rule=trip_capacity_rule)

    # SBQ: if you send trips, each trip must carry at least SBQ.
    def sbq_rule(m: pyo.ConcreteModel, i: str, j: str, k: str, t: str):
        return m.Ship[i, j, k, t] >= m.Trips[i, j, k, t] * m.RouteSBQ[i, j, k]

    model.SBQ = pyo.Constraint(model.R, model.T, rule=sbq_rule)

    # If a route is disabled, force shipments and trips to 0.
    def route_enabled_ship_rule(m: pyo.ConcreteModel, i: str, j: str, k: str, t: str):
        if bool(m.RouteEnabled[i, j, k]):
            return pyo.Constraint.Skip
        return m.Ship[i, j, k, t] == 0

    def route_enabled_trips_rule(m: pyo.ConcreteModel, i: str, j: str, k: str, t: str):
        if bool(m.RouteEnabled[i, j, k]):
            return pyo.Constraint.Skip
        return m.Trips[i, j, k, t] == 0

    def route_enabled_use_rule(m: pyo.ConcreteModel, i: str, j: str, k: str, t: str):
        if bool(m.RouteEnabled[i, j, k]):
            return pyo.Constraint.Skip
        return m.Use[i, j, k, t] == 0

    model.RouteEnabledShip = pyo.Constraint(model.R, model.T, rule=route_enabled_ship_rule)
    model.RouteEnabledTrips = pyo.Constraint(model.R, model.T, rule=route_enabled_trips_rule)
    model.RouteEnabledUse = pyo.Constraint(model.R, model.T, rule=route_enabled_use_rule)

    # Mode selection:
    # If Use[i,j,k,t] = 0 then Trips must be 0.
    def link_use_trips_rule(m: pyo.ConcreteModel, i: str, j: str, k: str, t: str):
        return m.Trips[i, j, k, t] <= big_m_trips * m.Use[i, j, k, t]

    model.LinkUseTrips = pyo.Constraint(model.R, model.T, rule=link_use_trips_rule)

    # At most one mode per (i,j) per month.
    def one_mode_rule(m: pyo.ConcreteModel, i: str, j: str, t: str):
        modes = [k for (ii, jj, k) in m.R if ii == i and jj == j]
        if not modes:
            return pyo.Constraint.Skip
        return sum(m.Use[i, j, k, t] for k in modes) <= 1

    model.OneModePerRoute = pyo.Constraint(model.IJ, model.T, rule=one_mode_rule)

    # Non-negativity is already enforced by variable domains.
    
    # Additional constraints for Excel dataset compatibility
    
    # Min fulfillment constraint: demand fulfillment must meet minimum percentage
    if hasattr(model, 'MinFulfillment'):
        def min_fulfillment_rule(m: pyo.ConcreteModel, p: str, t: str):
            if (p, t) not in m.MinFulfillment:
                return pyo.Constraint.Skip
            min_fulfill_pct = m.MinFulfillment[p, t]
            # Total supply = production + inflow - outflow
            inflow = sum(m.Ship[i, p, k, t] for (i, j, k) in m.R if j == p)
            prod = m.Prod[p, t]
            total_supply = prod + inflow
            return total_supply >= min_fulfill_pct * m.Demand[p, t]
        
        model.MinFulfillmentConstraint = pyo.Constraint(model.P, model.T, rule=min_fulfillment_rule)
    
    # Closing stock constraints (min and max)
    if hasattr(model, 'MinClosingStock'):
        def min_closing_stock_rule(m: pyo.ConcreteModel, p: str, t: str):
            if (p, t) not in m.MinClosingStock:
                return pyo.Constraint.Skip
            return m.Inv[p, t] >= m.MinClosingStock[p, t]
        
        model.MinClosingStockConstraint = pyo.Constraint(model.P, model.T, rule=min_closing_stock_rule)
    
    if hasattr(model, 'MaxClosingStock'):
        def max_closing_stock_rule(m: pyo.ConcreteModel, p: str, t: str):
            if (p, t) not in m.MaxClosingStock:
                return pyo.Constraint.Skip
            return m.Inv[p, t] <= m.MaxClosingStock[p, t]
        
        model.MaxClosingStockConstraint = pyo.Constraint(model.P, model.T, rule=max_closing_stock_rule)
    
    # Transport code limits (aggregate limits per transport code)
    if hasattr(model, 'TransportCodeLimits'):
        def transport_code_limit_lower_rule(m: pyo.ConcreteModel, i: str, k: str, t: str):
            if (i, k, t) not in m.TransportCodeLimits:
                return pyo.Constraint.Skip
            limits = m.TransportCodeLimits[i, k, t]
            if 'lower' not in limits or limits['lower'] is None:
                return pyo.Constraint.Skip
            total_shipped = sum(m.Ship[ii, jj, k, t] for (ii, jj, kk) in m.R if ii == i and kk == k)
            return total_shipped >= limits['lower']
        
        def transport_code_limit_upper_rule(m: pyo.ConcreteModel, i: str, k: str, t: str):
            if (i, k, t) not in m.TransportCodeLimits:
                return pyo.Constraint.Skip
            limits = m.TransportCodeLimits[i, k, t]
            if 'upper' not in limits or limits['upper'] is None:
                return pyo.Constraint.Skip
            total_shipped = sum(m.Ship[ii, jj, k, t] for (ii, jj, kk) in m.R if ii == i and kk == k)
            return total_shipped <= limits['upper']
        
        if hasattr(model, 'TransportCodeLimitSet'):
            model.TransportCodeLimitLower = pyo.Constraint(
                model.TransportCodeLimitSet, 
                rule=transport_code_limit_lower_rule
            )
            model.TransportCodeLimitUpper = pyo.Constraint(
                model.TransportCodeLimitSet,
                rule=transport_code_limit_upper_rule
            )
    
    # Transport bounds (route-specific bounds from IUGUConstraint)
    if hasattr(model, 'TransportBounds'):
        def transport_bound_lower_rule(m: pyo.ConcreteModel, i: str, j: str, k: str, t: str):
            if (i, j, k, t) not in m.TransportBounds:
                return pyo.Constraint.Skip
            bounds = m.TransportBounds[i, j, k, t]
            if 'L' not in bounds:
                return pyo.Constraint.Skip
            return m.Ship[i, j, k, t] >= bounds['L']
        
        def transport_bound_upper_rule(m: pyo.ConcreteModel, i: str, j: str, k: str, t: str):
            if (i, j, k, t) not in m.TransportBounds:
                return pyo.Constraint.Skip
            bounds = m.TransportBounds[i, j, k, t]
            if 'U' not in bounds:
                return pyo.Constraint.Skip
            return m.Ship[i, j, k, t] <= bounds['U']
        
        def transport_bound_equal_rule(m: pyo.ConcreteModel, i: str, j: str, k: str, t: str):
            if (i, j, k, t) not in m.TransportBounds:
                return pyo.Constraint.Skip
            bounds = m.TransportBounds[i, j, k, t]
            if 'E' not in bounds:
                return pyo.Constraint.Skip
            return m.Ship[i, j, k, t] == bounds['E']
        
        if hasattr(model, 'TransportBoundSet'):
            model.TransportBoundLower = pyo.Constraint(
                model.TransportBoundSet,
                rule=transport_bound_lower_rule
            )
            model.TransportBoundUpper = pyo.Constraint(
                model.TransportBoundSet,
                rule=transport_bound_upper_rule
            )
            model.TransportBoundEqual = pyo.Constraint(
                model.TransportBoundSet,
                rule=transport_bound_equal_rule
            )