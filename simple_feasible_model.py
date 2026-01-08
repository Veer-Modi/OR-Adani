"""
Simple feasible Pyomo model for Streamlit app.
"""

import pyomo.environ as pyo
from simple_feasible_loader import SimpleFeasibleData


def build_simple_feasible_model(data: SimpleFeasibleData) -> pyo.ConcreteModel:
    """Build a simple feasible optimization model."""
    
    m = pyo.ConcreteModel()
    
    # Sets
    m.P = pyo.Set(initialize=data.plant_ids)
    m.T = pyo.Set(initialize=data.months)
    m.CL = pyo.Set(initialize=data.clinker_plants)
    m.R = pyo.Set(initialize=data.routes)
    
    # Parameters (with defaults for missing values)
    prod_cap_dict = {p: data.production_capacity.get(p, 0.0) for p in data.plant_ids}
    prod_cost_dict = {p: data.production_cost.get(p, 1800.0) for p in data.plant_ids}  # Default cost
    inv0_dict = {p: data.initial_inventory.get(p, 0.0) for p in data.plant_ids}
    hold_cost_dict = {p: 50.0 for p in data.plant_ids}  # Default holding cost
    
    m.ProdCap = pyo.Param(m.P, initialize=prod_cap_dict)
    m.ProdCost = pyo.Param(m.P, initialize=prod_cost_dict)
    m.Demand = pyo.Param(m.P, m.T, initialize=data.demand, default=0.0)
    m.Inv0 = pyo.Param(m.P, initialize=inv0_dict)
    m.HoldCost = pyo.Param(m.P, initialize=hold_cost_dict)  # Added missing parameter
    m.RouteCost = pyo.Param(m.R, initialize=data.transport_cost_per_trip)
    m.RouteCap = pyo.Param(m.R, initialize=data.transport_capacity_per_trip)
    
    # Variables
    m.Prod = pyo.Var(m.P, m.T, domain=pyo.NonNegativeReals)
    m.Ship = pyo.Var(m.R, m.T, domain=pyo.NonNegativeReals)
    m.Inv = pyo.Var(m.P, m.T, domain=pyo.NonNegativeReals)
    m.DemandSlack = pyo.Var(m.P, m.T, domain=pyo.NonNegativeReals)
    m.Trips = pyo.Var(m.R, m.T, domain=pyo.NonNegativeReals)  # Added missing variable
    
    # Fix production for non-clinker plants
    non_clinker = [p for p in data.plant_ids if p not in data.clinker_plants]
    for p in non_clinker:
        for t in data.months:
            m.Prod[p, t].fix(0.0)
    
    # Demand penalty
    m.DemandPenalty = pyo.Param(initialize=10000.0)
    
    # Constraints
    def production_capacity_rule(m, p, t):
        return m.Prod[p, t] <= m.ProdCap[p]
    m.ProductionCapacity = pyo.Constraint(m.CL, m.T, rule=production_capacity_rule)
    
    def inventory_balance_rule(m, p, t):
        inflow = sum(m.Ship[i, p, k, t] for (i, j, k) in m.R if j == p)
        outflow = sum(m.Ship[p, j, k, t] for (i, j, k) in m.R if i == p)
        return m.Inv[p, t] == m.Inv0[p] + m.Prod[p, t] + inflow - outflow - m.Demand[p, t] + m.DemandSlack[p, t]
    m.InventoryBalance = pyo.Constraint(m.P, m.T, rule=inventory_balance_rule)
    
    def transport_capacity_rule(m, i, j, k, t):
        return m.Ship[i, j, k, t] <= m.RouteCap[i, j, k] * 100  # Assume 100 trips max
    m.TransportCapacity = pyo.Constraint(m.R, m.T, rule=transport_capacity_rule)
    
    # Link trips to shipments (to initialize trips variables)
    def link_trips_to_shipments_rule(m, i, j, k, t):
        return m.Trips[i, j, k, t] >= m.Ship[i, j, k, t] / max(m.RouteCap[i, j, k], 1.0)
    m.LinkTripsToShipments = pyo.Constraint(m.R, m.T, rule=link_trips_to_shipments_rule)
    
    # Objective
    def total_cost_rule(m):
        prod_cost = sum(m.ProdCost[p] * m.Prod[p, t] for p in m.P for t in m.T)
        trans_cost = sum(m.RouteCost[i, j, k] * m.Ship[i, j, k, t] for (i, j, k) in m.R for t in m.T)
        demand_penalty = sum(m.DemandPenalty * m.DemandSlack[p, t] for p in m.P for t in m.T)
        return prod_cost + trans_cost + demand_penalty
    
    m.TotalCost = pyo.Objective(rule=total_cost_rule, sense=pyo.minimize)
    
    return m
