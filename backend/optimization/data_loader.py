"""Optimization data loader.

Goal:
- Fetch plants, demands, transport routes, and inventory policies from MongoDB
- Convert MongoDB documents into simple Python structures that Pyomo can use
- Validate data BEFORE optimization so the user gets clear errors

Data flow:
UI -> data_loader -> (validated data dict) -> model builder

Beginner note:
Pyomo works best when you provide "clean" inputs:
- sets (lists of IDs)
- parameters (dictionaries)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from backend.core.cache import cached_get_all_plants, cached_get_all_routes
from backend.demand.demand_service import get_all_demands
from backend.inventory.inventory_service import get_all_policies



@dataclass
class OptimizationData:
    """All validated data required by the optimization model."""

    months: List[str]

    plant_ids: List[str]
    plant_names: Dict[str, str]
    plant_type: Dict[str, str]

    clinker_plants: List[str]

    storage_capacity: Dict[str, float]
    initial_inventory: Dict[str, float]

    safety_stock: Dict[str, float]
    max_inventory: Dict[str, float]
    holding_cost: Dict[str, float]

    production_capacity: Dict[str, float]
    production_cost: Dict[str, float]

    demand: Dict[Tuple[str, str], float]

    # Route keys use: (from_id, to_id, mode)
    routes: List[Tuple[str, str, str]]
    transport_cost_per_trip: Dict[Tuple[str, str, str], float]
    transport_capacity_per_trip: Dict[Tuple[str, str, str], float]
    transport_sbq: Dict[Tuple[str, str, str], float]
    route_enabled: Dict[Tuple[str, str, str], bool]


def _to_float(value: Any, field_name: str) -> float:
    """Convert a value to float with a clear error."""

    try:
        return float(value)
    except Exception:
        raise ValueError(f"{field_name} must be a number.")


def assemble_optimization_data(
    selected_months: List[str],
    demand_type_filter: str = "Fixed",
) -> OptimizationData:
    """Load and validate all data needed for optimization.

    Args:
        selected_months: list of months in YYYY-MM format.
        demand_type_filter: which demand type to optimize (default: Fixed).

    Returns:
        OptimizationData (validated)

    Raises:
        ValueError: if any data consistency issue is found.
    """

    months = [m.strip() for m in selected_months if (m or "").strip()]
    if not months:
        raise ValueError("Please select at least one month.")

    # Phase 6: use cached master data to avoid repeated DB reads on Streamlit reruns.
    plants = cached_get_all_plants(include_inactive=False)
    if not plants:
        raise ValueError("No plants found. Please create plants first.")

    plant_ids = [str(p.get("_id")) for p in plants]
    plant_names = {str(p.get("_id")): (p.get("name") or "") for p in plants}
    plant_type = {str(p.get("_id")): (p.get("plant_type") or "") for p in plants}

    clinker_plants = [pid for pid in plant_ids if plant_type.get(pid) == "Clinker Plant"]

    # Storage capacity and initial inventory come from Plant module.
    storage_capacity = {
        str(p.get("_id")): _to_float(p.get("storage_capacity", 0.0), "Storage capacity")
        for p in plants
    }
    initial_inventory = {
        str(p.get("_id")): _to_float(p.get("initial_inventory", 0.0), "Initial inventory")
        for p in plants
    }

    # Inventory policies are optional; if missing, we derive defaults:
    # - safety_stock from plant.safety_stock
    # - max_inventory from plant.storage_capacity
    # - holding_cost default 0
    policies = get_all_policies()
    policy_by_plant_id = {str(p.get("plant_id")): p for p in policies}

    safety_stock: Dict[str, float] = {}
    max_inventory: Dict[str, float] = {}
    holding_cost: Dict[str, float] = {}

    for p in plants:
        pid = str(p.get("_id"))
        pol = policy_by_plant_id.get(pid)

        if pol is None:
            safety_stock[pid] = _to_float(p.get("safety_stock", 0.0), "Safety stock")
            max_inventory[pid] = storage_capacity[pid]
            holding_cost[pid] = 0.0
        else:
            safety_stock[pid] = _to_float(pol.get("safety_stock", 0.0), "Safety stock")
            max_inventory[pid] = _to_float(pol.get("max_inventory", 0.0), "Max inventory")
            holding_cost[pid] = _to_float(pol.get("holding_cost_per_month", 0.0), "Holding cost")

    # Production capacity/cost fields:
    # We read optional values from plant doc. If missing for clinker plants, we error.
    production_capacity: Dict[str, float] = {}
    production_cost: Dict[str, float] = {}

    for pid in plant_ids:
        production_capacity[pid] = 0.0
        production_cost[pid] = 0.0

    for p in plants:
        pid = str(p.get("_id"))

        if plant_type.get(pid) == "Clinker Plant":
            if p.get("production_capacity") is None:
                raise ValueError(
                    f"Missing production_capacity for clinker plant: {plant_names.get(pid)}. "
                    "Please edit the plant and set a monthly production capacity."
                )
            if p.get("production_cost") is None:
                raise ValueError(
                    f"Missing production_cost for clinker plant: {plant_names.get(pid)}. "
                    "Please edit the plant and set a production cost per unit."
                )

            production_capacity[pid] = _to_float(p.get("production_capacity"), "Production capacity")
            production_cost[pid] = _to_float(p.get("production_cost"), "Production cost")

    # Demand: we will build demand[(plant_id, month)]
    all_demands = get_all_demands()

    demand: Dict[Tuple[str, str], float] = {}

    # Default 0 demand unless specified.
    for pid in plant_ids:
        for m in months:
            demand[(pid, m)] = 0.0

    for d in all_demands:
        if (d.get("demand_type") or "") != demand_type_filter:
            continue

        month = (d.get("month") or "").strip()
        if month not in months:
            continue

        # Demand docs store plant_id as ObjectId.
        plant_id_value = d.get("plant_id")
        plant_id_str = str(plant_id_value)

        if plant_id_str not in plant_ids:
            continue

        qty = _to_float(d.get("demand_quantity", 0.0), "Demand quantity")
        if qty < 0:
            raise ValueError("Demand quantity cannot be negative.")

        demand[(plant_id_str, month)] += qty

    # Transport routes
    all_routes = cached_get_all_routes(include_disabled=True)
    if not all_routes:
        raise ValueError("No transport routes found. Please create routes first.")

    routes: List[Tuple[str, str, str]] = []
    transport_cost_per_trip: Dict[Tuple[str, str, str], float] = {}
    transport_capacity_per_trip: Dict[Tuple[str, str, str], float] = {}
    transport_sbq: Dict[Tuple[str, str, str], float] = {}
    route_enabled: Dict[Tuple[str, str, str], bool] = {}

    for r in all_routes:
        from_id = str(r.get("from_plant_id"))
        to_id = str(r.get("to_plant_id"))
        mode = (r.get("transport_mode") or "").strip()

        if from_id not in plant_ids or to_id not in plant_ids:
            continue

        key = (from_id, to_id, mode)

        routes.append(key)
        transport_cost_per_trip[key] = _to_float(r.get("cost_per_trip", 0.0), "Cost per trip")
        transport_capacity_per_trip[key] = _to_float(r.get("capacity_per_trip", 0.0), "Capacity per trip")
        transport_sbq[key] = _to_float(r.get("sbq", 0.0), "SBQ")
        route_enabled[key] = bool(r.get("is_enabled", True))

        if transport_capacity_per_trip[key] < 0 or transport_cost_per_trip[key] < 0 or transport_sbq[key] < 0:
            raise ValueError("Transport cost/capacity/SBQ cannot be negative.")

        if transport_sbq[key] > transport_capacity_per_trip[key]:
            raise ValueError(
                f"SBQ cannot exceed capacity for route {plant_names.get(from_id)} -> {plant_names.get(to_id)} ({mode})."
            )

    # Basic feasibility checks:
    # 1) For any month, total demand must be <= total potential production + initial inventory.
    # This is a quick sanity check, not a proof of feasibility.
    for m in months:
        total_demand = sum(demand[(pid, m)] for pid in plant_ids)
        total_initial = sum(initial_inventory[pid] for pid in plant_ids)
        total_prod_cap = sum(production_capacity[pid] for pid in clinker_plants)

        if total_demand > total_initial + total_prod_cap:
            raise ValueError(
                f"Demand seems too high for month {m}. "
                f"Total demand={total_demand}, total initial inventory={total_initial}, total clinker production capacity={total_prod_cap}."
            )

    # 2) Storage feasibility (initial inventory must fit inside max inventory).
    for pid in plant_ids:
        if initial_inventory[pid] > max_inventory[pid]:
            raise ValueError(
                f"Initial inventory for plant {plant_names.get(pid)} is greater than max inventory capacity."
            )

    # 3) Missing transport connectivity (simple check):
    # If a plant has demand but no inflow route and no production, it will fail.
    has_inflow = {pid: False for pid in plant_ids}
    for (i, j, mode) in routes:
        if route_enabled[(i, j, mode)]:
            has_inflow[j] = True

    for pid in plant_ids:
        for m in months:
            if demand[(pid, m)] > 0 and (pid not in clinker_plants) and not has_inflow.get(pid, False):
                raise ValueError(
                    f"Plant {plant_names.get(pid)} has demand in {m} but no enabled inbound transport route and no clinker production."
                )

    return OptimizationData(
        months=months,
        plant_ids=plant_ids,
        plant_names=plant_names,
        plant_type=plant_type,
        clinker_plants=clinker_plants,
        storage_capacity=storage_capacity,
        initial_inventory=initial_inventory,
        safety_stock=safety_stock,
        max_inventory=max_inventory,
        holding_cost=holding_cost,
        production_capacity=production_capacity,
        production_cost=production_cost,
        demand=demand,
        routes=routes,
        transport_cost_per_trip=transport_cost_per_trip,
        transport_capacity_per_trip=transport_capacity_per_trip,
        transport_sbq=transport_sbq,
        route_enabled=route_enabled,
    )
