"""Analytics service.

This is the orchestration layer for Phase 5.

Responsibilities:
- Load a run from MongoDB
- Load required master data (plants, routes, inventory policies, demands)
- Compute KPIs, utilizations, bottlenecks, and cost drivers
- Persist analytics back to the run document

Important:
- We do NOT modify optimization logic.
- We do NOT require re-solving.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import pandas as pd

from backend.analytics.bottleneck_detector import detect_bottlenecks
from backend.analytics.cost_driver_analysis import compute_cost_drivers
from backend.analytics.kpi_engine import compute_kpis
from backend.analytics.utilization_analysis import compute_utilization
from backend.demand.demand_service import get_all_demands
from backend.inventory.inventory_service import get_all_policies
from backend.plant.plant_service import get_all_plants
from backend.results.result_repository import update_run_fields
from backend.results.result_service import get_run
from backend.transport.transport_service import get_all_routes


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


def _build_inventory_defaults(plants: List[Dict[str, Any]], policies: List[Dict[str, Any]]):
    storage_capacity = {str(p.get("_id")): _safe_float(p.get("storage_capacity", 0.0)) for p in plants}
    safety_stock = {str(p.get("_id")): _safe_float(p.get("safety_stock", 0.0)) for p in plants}

    policy_by_pid = {str(pol.get("plant_id")): pol for pol in policies}

    max_inventory: Dict[str, float] = {}
    holding_cost: Dict[str, float] = {}

    for p in plants:
        pid = str(p.get("_id"))
        pol = policy_by_pid.get(pid)
        if pol is None:
            max_inventory[pid] = float(storage_capacity.get(pid, 0.0))
            holding_cost[pid] = 0.0
        else:
            max_inventory[pid] = _safe_float(pol.get("max_inventory", 0.0))
            holding_cost[pid] = _safe_float(pol.get("holding_cost_per_month", 0.0))

    return safety_stock, max_inventory, holding_cost


def _demand_for_run(run: Dict[str, Any]) -> pd.DataFrame:
    """Return a demand dataframe for KPI calculations.

    For deterministic runs:
    - use Fixed demand for the run months.

    For uncertainty runs:
    - if scenario_probabilities exist, we compute expected demand = sum_s prob_s * (multiplier_s * base_demand)
      using the stored scenario definitions.
    """

    months = set(run.get("months", []) or [])
    demand_type = str(run.get("demand_type", "Fixed"))
    opt_type = str(run.get("optimization_type", "deterministic"))

    all_demands = get_all_demands()
    base_rows: List[Dict[str, Any]] = []

    # Base demand is always Fixed in our system.
    for d in all_demands:
        if str(d.get("demand_type")) != demand_type:
            continue
        m = str(d.get("month") or "")
        if m not in months:
            continue
        base_rows.append({"plant_id": str(d.get("plant_id")), "month": m, "demand_quantity": _safe_float(d.get("demand_quantity", 0.0))})

    base_df = pd.DataFrame(base_rows)

    if opt_type in {"stochastic", "robust"}:
        scenarios = run.get("scenarios", []) or []
        probs = run.get("scenario_probabilities", {}) or {}

        if base_df.empty or not scenarios or not probs:
            return base_df

        # Expected demand = sum_s prob_s * multiplier_s * base_demand
        exp_df = base_df.copy()
        exp_df["expected_multiplier"] = 0.0
        for s in scenarios:
            name = str(s.get("name"))
            mult = _safe_float(s.get("demand_multiplier", 1.0), 1.0)
            p = _safe_float(probs.get(name, 0.0))
            exp_df["expected_multiplier"] += p * mult

        exp_df["demand_quantity"] = exp_df["demand_quantity"] * exp_df["expected_multiplier"]
        exp_df = exp_df.drop(columns=["expected_multiplier"])
        return exp_df

    return base_df


def compute_and_store_analytics(run_id: str) -> Tuple[bool, str]:
    run = get_run(run_id)
    if run is None:
        return False, "Run not found."

    if str(run.get("status") or "").lower() != "success":
        return False, "Analytics is only computed for successful runs."

    plants = get_all_plants(include_inactive=False)
    routes = get_all_routes(include_disabled=True)
    policies = get_all_policies()

    plant_names = {str(p.get("_id")): str(p.get("name") or "") for p in plants}
    prod_cap = {str(p.get("_id")): _safe_float(p.get("production_capacity", 0.0)) for p in plants}
    prod_cost = {str(p.get("_id")): _safe_float(p.get("production_cost", 0.0)) for p in plants}

    safety_stock, max_inventory, _holding_cost = _build_inventory_defaults(plants, policies)

    route_cap = {}
    route_cost = {}
    for r in routes:
        key = (str(r.get("from_plant_id")), str(r.get("to_plant_id")), str(r.get("transport_mode")))
        route_cap[key] = _safe_float(r.get("capacity_per_trip", 0.0))
        route_cost[key] = _safe_float(r.get("cost_per_trip", 0.0))

    months = list(run.get("months", []) or [])

    demand_df = _demand_for_run(run)

    kpi_res = compute_kpis(
        run=run,
        demand_df=demand_df,
        safety_stock_by_plant=safety_stock,
        scenario_probabilities=(run.get("scenario_probabilities", {}) or None),
    )

    util_res = compute_utilization(
        run=run,
        months=months,
        plant_names=plant_names,
        production_capacity_by_plant=prod_cap,
        max_inventory_by_plant=max_inventory,
        route_capacity_per_trip=route_cap,
    )

    inv_df = pd.DataFrame(run.get("inventory_rows", []) or [])
    bottlenecks = detect_bottlenecks(
        production_utilization_df=util_res.production_utilization_df,
        transport_utilization_df=util_res.transport_utilization_df,
        inventory_df=inv_df,
        safety_stock_by_plant=safety_stock,
    )

    cost_drivers = compute_cost_drivers(
        run=run,
        plant_names=plant_names,
        production_cost_by_plant=prod_cost,
        route_cost_per_trip=route_cost,
    )

    def _avg_headroom(df: pd.DataFrame, col: str = "utilization_percent") -> Tuple[float | None, float | None]:
        if df is None or df.empty or col not in df.columns:
            return None, None
        avg_util = float(df[col].mean())
        headroom = max(0.0, 100.0 - avg_util)
        return avg_util, headroom

    prod_avg_util, prod_headroom = _avg_headroom(util_res.production_utilization_df)
    storage_avg_util, storage_headroom = _avg_headroom(util_res.storage_utilization_df)
    trans_avg_util, trans_headroom = _avg_headroom(util_res.transport_utilization_df)

    service_level = float(kpi_res.kpis.get("service_level_percent", 0.0) or 0.0)

    resilience_components: Dict[str, float | None] = {
        "service_level": service_level,
        "production_headroom": prod_headroom,
        "storage_headroom": storage_headroom,
        "transport_headroom": trans_headroom,
    }

    component_values = [v for v in resilience_components.values() if v is not None]
    resilience_score = float(sum(component_values) / len(component_values)) if component_values else 0.0

    if resilience_score >= 80:
        classification = "Resilient"
    elif resilience_score >= 60:
        classification = "Balanced"
    else:
        classification = "At Risk"

    alerts: List[str] = []
    recommendations: List[str] = []

    if prod_avg_util is not None and prod_avg_util > 90:
        alerts.append(f"Production network running hot ({prod_avg_util:.1f}% utilized).")
        if not util_res.production_utilization_df.empty:
            top_prod = util_res.production_utilization_df.sort_values("utilization_percent", ascending=False).iloc[0]
            recommendations.append(
                f"Shift volume away from {top_prod.get('plant', 'a plant')} (at {float(top_prod.get('utilization_percent', 0.0)):.1f}% load)."
            )

    if storage_avg_util is not None and storage_avg_util > 85:
        alerts.append(f"Storage cushion is thin (avg {storage_avg_util:.1f}% full).")
        if not util_res.storage_utilization_df.empty:
            top_storage = util_res.storage_utilization_df.sort_values("utilization_percent", ascending=False).iloc[0]
            recommendations.append(
                f"Pull forward shipments to relieve {top_storage.get('plant', 'one site')} holding {float(top_storage.get('utilization_percent', 0.0)):.1f}% fill."
            )

    if trans_avg_util is not None and trans_avg_util > 80:
        alerts.append(f"Transport routes near saturation (avg {trans_avg_util:.1f}% capacity used).")
        if not util_res.transport_utilization_df.empty:
            top_route = util_res.transport_utilization_df.sort_values("utilization_percent", ascending=False).iloc[0]
            route_name = f"{top_route.get('from', 'Origin')} → {top_route.get('to', 'Destination')}"
            recommendations.append(
                f"Add contingency capacity on {route_name} (utilization {float(top_route.get('utilization_percent', 0.0)):.1f}%)."
            )

    if service_level < 98:
        alerts.append(f"Service level below target ({service_level:.1f}%).")
        recommendations.append("Increase safety stock or reroute clinker to protect customer deliveries.")

    if not recommendations:
        recommendations.append("Maintain current plan; monitor weekly for demand spikes.")

    analytics_doc: Dict[str, Any] = {
        "kpis": kpi_res.kpis,
        "utilization": {
            "production": util_res.production_utilization_df.to_dict(orient="records") if not util_res.production_utilization_df.empty else [],
            "transport": util_res.transport_utilization_df.to_dict(orient="records") if not util_res.transport_utilization_df.empty else [],
            "storage": util_res.storage_utilization_df.to_dict(orient="records") if not util_res.storage_utilization_df.empty else [],
        },
        "bottlenecks": {
            "plants": bottlenecks.plant_bottlenecks,
            "routes": bottlenecks.route_bottlenecks,
            "inventory": bottlenecks.inventory_bottlenecks,
        },
        "cost_drivers": {
            "top_plants": cost_drivers.top_plants_df.to_dict(orient="records") if not cost_drivers.top_plants_df.empty else [],
            "top_routes": cost_drivers.top_routes_df.to_dict(orient="records") if not cost_drivers.top_routes_df.empty else [],
            "mode_cost": cost_drivers.mode_cost_df.to_dict(orient="records") if cost_drivers.mode_cost_df is not None and not cost_drivers.mode_cost_df.empty else [],
        },
        "resilience": {
            "score": resilience_score,
            "classification": classification,
            "components": resilience_components,
            "alerts": alerts,
            "recommendations": recommendations,
        },
    }

    summary_metrics = dict(run.get("summary_metrics") or {})
    summary_metrics["resilience_score"] = resilience_score
    summary_metrics["resilience_classification"] = classification

    update_payload = {
        "analytics": analytics_doc,
        "summary_metrics": summary_metrics,
    }

    ok = update_run_fields(run_id, update_payload)
    if not ok:
        return False, "Failed to store analytics."

    return True, "Analytics computed and stored."
