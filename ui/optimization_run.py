"""Optimization Run page (Streamlit UI).

What this page does:
- Lets user select planning horizon (months)
- Select solver (CBC)
- Run optimization

Role access:
- Admin & Planner: can run
- Viewer: cannot run

Data flow:
UI -> optimization.data_loader -> optimization.model -> optimization.solver -> optimization.result_parser
   -> results.result_service (save run)
"""

from __future__ import annotations

from typing import List

import streamlit as st

from backend.middleware.role_guard import require_authentication, require_role
from backend.optimization.feasible_excel_loader import load_feasible_excel_data
from backend.optimization.feasible_model import build_feasible_model
# Simple fallback without backend dependencies
from simple_feasible_loader import load_simple_feasible_data
from simple_feasible_model import build_simple_feasible_model
from simple_result_parser import parse_simple_results
from backend.optimization.result_parser import parse_results
from backend.optimization.solver import SolverConfig, solve_model
from backend.uncertainty.scenario_generator import DemandScenario, generate_demand_scenarios
from backend.uncertainty.stochastic_model import build_stochastic_model
from backend.uncertainty.robust_model import build_robust_model
from backend.uncertainty.result_parser import parse_uncertainty_results
from backend.uncertainty.uncertainty_service import get_scenarios_for_optimization
from backend.core.logger import audit_log
from backend.results.result_service import save_optimization_run
from backend.demand.demand_service import get_all_demands


def _get_available_months() -> List[str]:
    """Collect months from existing demand records."""

    demands = get_all_demands()
    months = sorted({(d.get("month") or "").strip() for d in demands if (d.get("month") or "").strip()})
    return months


def render_optimization_run(role: str) -> None:
    """Render the optimization run page."""

    if not require_authentication():
        return

    st.header("Run Optimization")
    st.caption("Solve deterministic multi-period clinker allocation and transport planning.")

    if not require_role(["Admin", "Planner"]):
        st.warning("Viewer role: you cannot run optimization. Open Optimization Results to view runs.")
        return

    available_months = _get_available_months()

    if not available_months:
        st.warning("No demand months found. Please create Demand records first.")
        return

    selected_months = st.multiselect("Select planning months", options=available_months, default=available_months[:1])

    demand_type = st.selectbox(
        "Demand type to optimize",
        ["Fixed"],
        index=0,
        help="Phase 3 is deterministic. Scenario demand will be added in a later phase.",
    )

    # Only expose CBC in the UI to avoid confusion with unavailable solvers.
    solver_choice = st.selectbox("Solver", ["CBC"], index=0)

    time_limit = st.number_input("Time limit (seconds)", min_value=10, value=60, step=10)
    mip_gap = st.number_input("MIP gap (example: 0.01 = 1%)", min_value=0.0, value=0.01, step=0.01)

    # Phase 4: uncertainty settings are optional and stored in MongoDB.
    scen_ok, scen_msg, uncertainty_enabled, configured_scenarios = get_scenarios_for_optimization()
    if not scen_ok:
        st.warning(f"Uncertainty settings invalid: {scen_msg}")
        uncertainty_enabled = False
        configured_scenarios = []

    st.divider()
    st.subheader("Uncertainty mode (Phase 4)")

    if not uncertainty_enabled:
        st.info("Demand uncertainty is disabled. Runs will be deterministic (Phase 3 behavior).")
        optimization_mode = "Deterministic"
    else:
        optimization_mode = st.selectbox(
            "Optimization mode",
            ["Deterministic", "Stochastic (Expected Cost)", "Robust (Worst Case)"],
            index=1,
            help=(
                "Deterministic uses the base Fixed demand. "
                "Stochastic minimizes expected cost across scenarios. "
                "Robust minimizes worst-case cost while remaining feasible in every scenario."
            ),
        )

    if st.button("Run Optimization"):
        with st.spinner("Running optimization..."):
            try:
                # Try to use simple feasible model first (no backend dependencies)
                data = load_simple_feasible_data(
                    file_path="Dataset_Dummy_Clinker_3MPlan.xlsx",
                    selected_months=selected_months
                )
                use_simple_model = True
                st.info("Using simplified feasible optimization model")
            except Exception as e:
                st.warning(f"Simplified model failed, trying full backend: {e}")
                try:
                    # Fallback to full backend model
                    data = load_feasible_excel_data(
                        file_path="Dataset_Dummy_Clinker_3MPlan.xlsx",
                        selected_months=selected_months
                    )
                    use_simple_model = False
                except Exception as e2:
                    st.error(f"Both models failed: {e2}")
                    return

            # Internally we always use CBC (installed and configured).
            solver_name = "cbc"

            # -----------------------------
            # Deterministic (Phase 3) - Using Feasible Model
            # -----------------------------
            if optimization_mode == "Deterministic":
                # Use appropriate model based on data loader
                if use_simple_model:
                    model = build_simple_feasible_model(data)
                else:
                    model = build_feasible_model(data)

                outcome = solve_model(
                    model,
                    SolverConfig(
                        solver_name=solver_name,
                        time_limit_seconds=int(time_limit),
                        mip_gap=float(mip_gap),
                    ),
                )

                if not outcome.ok:
                    st.error(outcome.message)

                    audit_log(
                        event_type="optimization_failed",
                        actor_email=str(st.session_state.get("user_email") or ""),
                        details={
                            "mode": "deterministic",
                            "requested_solver": solver_name,
                            "solver_used": outcome.solver_used,
                            "termination": outcome.termination_condition,
                        },
                    )

                    save_optimization_run(
                        created_by_email=str(st.session_state.get("user_email")),
                        months=list(selected_months),
                        solver=solver_name,
                        demand_type=demand_type,
                        status="failed",
                        message=outcome.message,
                        objective_value=0.0,
                        cost_breakdown={"production": 0.0, "transport": 0.0, "holding": 0.0},
                        production_df=None,
                        transport_df=None,
                        inventory_df=None,
                        optimization_type="deterministic",
                    )

                    return

                # Use appropriate result parser based on model type
                if use_simple_model:
                    results = parse_simple_results(model, plant_names=data.plant_names)
                else:
                    results = parse_results(model, plant_names=data.plant_names)

                # Simple summary metrics for comparison dashboards.
                inv_df = results.inventory_df.copy() if results.inventory_df is not None else None
                avg_inventory = float(inv_df["inventory"].mean()) if inv_df is not None and not inv_df.empty else 0.0
                avg_buffer = 0.0
                if inv_df is not None and (not inv_df.empty) and ("plant_id" in inv_df.columns):
                    # Handle safety stock for both simple and full models
                    if use_simple_model:
                        # Simple model doesn't have safety_stock data, use default
                        inv_df["safety_stock"] = inv_df["plant_id"].map(lambda pid: 0.0)
                    else:
                        inv_df["safety_stock"] = inv_df["plant_id"].map(lambda pid: float(data.safety_stock.get(pid, 0.0)))
                    avg_buffer = float((inv_df["inventory"] - inv_df["safety_stock"]).mean())

                st.success(outcome.message)
                if outcome.runtime_seconds is not None:
                    st.caption(f"Solve runtime: {round(float(outcome.runtime_seconds), 2)} seconds")
                if outcome.solver_log_path:
                    st.caption(f"Solver log saved to: {outcome.solver_log_path}")
                st.metric("Objective value (total cost)", round(results.objective_value, 2))

                ok, msg, run_id = save_optimization_run(
                    created_by_email=str(st.session_state.get("user_email")),
                    months=list(selected_months),
                    solver=solver_name,
                    demand_type=demand_type,
                    status="success",
                    message=outcome.message,
                    objective_value=results.objective_value,
                    cost_breakdown=results.cost_breakdown,
                    production_df=results.production_df,
                    transport_df=results.transport_df,
                    inventory_df=results.inventory_df,
                    optimization_type="deterministic",
                    summary_metrics={
                        "avg_inventory": avg_inventory,
                        "avg_buffer": avg_buffer,
                        "solver_used": outcome.solver_used,
                        "runtime_seconds": outcome.runtime_seconds,
                        "solver_log_path": outcome.solver_log_path,
                    },
                )

                audit_log(
                    event_type="optimization_success",
                    actor_email=str(st.session_state.get("user_email") or ""),
                    details={
                        "mode": "deterministic",
                        "requested_solver": solver_name,
                        "solver_used": outcome.solver_used,
                        "months": list(selected_months),
                        "runtime_seconds": outcome.runtime_seconds,
                    },
                )

                if ok and run_id:
                    st.session_state.last_optimization_run_id = run_id
                    st.info("Run saved. Open Optimization Results to view and export.")
                    
                    # Also display results directly on this page
                    st.divider()
                    st.subheader("📊 Optimization Results")
                    
                    # Display cost breakdown
                    cost = results.cost_breakdown
                    cost_df = pd.DataFrame([
                        {"type": "production", "cost": float(cost.get("production", 0.0))},
                        {"type": "transport", "cost": float(cost.get("transport", 0.0))},
                        {"type": "holding", "cost": float(cost.get("holding", 0.0))},
                        {"type": "demand_penalty", "cost": float(cost.get("demand_penalty", 0.0))},
                    ])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Objective value (total cost)", round(results.objective_value, 2))
                    with col2:
                        st.metric("Active production plans", len(results.production_df))
                    
                    st.subheader("Cost Breakdown")
                    st.dataframe(cost_df, use_container_width=True)
                    
                    # Display production plan
                    st.subheader("🏭 Production Plan")
                    if not results.production_df.empty:
                        st.dataframe(results.production_df, use_container_width=True)
                    else:
                        st.warning("No production data available")
                    
                    # Display transport plan
                    st.subheader("🚚 Transport Plan")
                    if not results.transport_df.empty:
                        st.dataframe(results.transport_df, use_container_width=True)
                    else:
                        st.warning("No transport data available")
                    
                    # Display inventory plan
                    st.subheader("📦 Inventory Plan")
                    if not results.inventory_df.empty:
                        st.dataframe(results.inventory_df, use_container_width=True)
                    else:
                        st.warning("No inventory data available")
                        
                else:
                    st.warning(msg)

                return

            # -----------------------------
            # Uncertainty models (Phase 4)
            # -----------------------------
            if not uncertainty_enabled:
                st.error("Uncertainty is disabled. Enable it in Demand Uncertainty Settings to run stochastic/robust.")
                return

            scenarios = [
                DemandScenario(
                    name=str(s.get("name")),
                    probability=float(s.get("probability")),
                    demand_multiplier=float(s.get("demand_multiplier")),
                )
                for s in (configured_scenarios or [])
            ]

            scen_data = generate_demand_scenarios(base_data=data, scenarios=scenarios)

            if optimization_mode == "Stochastic (Expected Cost)":
                model = build_stochastic_model(data, scen_data)
                optimization_type = "stochastic"
            else:
                model = build_robust_model(data, scen_data)
                optimization_type = "robust"

            outcome = solve_model(
                model,
                SolverConfig(
                    solver_name=solver_name,
                    time_limit_seconds=int(time_limit),
                    mip_gap=float(mip_gap),
                ),
            )

            if not outcome.ok:
                st.error(outcome.message)

                audit_log(
                    event_type="optimization_failed",
                    actor_email=str(st.session_state.get("user_email") or ""),
                    details={
                        "mode": optimization_type,
                        "requested_solver": solver_name,
                        "solver_used": outcome.solver_used,
                        "termination": outcome.termination_condition,
                    },
                )

                # Save failed run for history.
                save_optimization_run(
                    created_by_email=str(st.session_state.get("user_email")),
                    months=list(selected_months),
                    solver=solver_name,
                    demand_type=demand_type,
                    status="failed",
                    message=outcome.message,
                    objective_value=0.0,
                    cost_breakdown={"production": 0.0, "transport": 0.0, "holding": 0.0},
                    production_df=None,
                    transport_df=None,
                    inventory_df=None,
                    optimization_type=optimization_type,
                    scenarios=configured_scenarios,
                    scenario_probabilities=scen_data.probability,
                )

                return

            results_u = parse_uncertainty_results(model, plant_names=data.plant_names)

            inv_df = results_u.inventory_df.copy() if results_u.inventory_df is not None else None
            avg_inventory = float(inv_df["inventory"].mean()) if inv_df is not None and not inv_df.empty else 0.0
            avg_buffer = 0.0
            if inv_df is not None and (not inv_df.empty) and ("plant_id" in inv_df.columns):
                inv_df["safety_stock"] = inv_df["plant_id"].map(lambda pid: float(data.safety_stock.get(pid, 0.0)))
                avg_buffer = float((inv_df["inventory"] - inv_df["safety_stock"]).mean())

            st.success(outcome.message)
            if outcome.runtime_seconds is not None:
                st.caption(f"Solve runtime: {round(float(outcome.runtime_seconds), 2)} seconds")
            if outcome.solver_log_path:
                st.caption(f"Solver log saved to: {outcome.solver_log_path}")
            st.metric("Objective value (total cost)", round(results_u.objective_value, 2))

            ok, msg, run_id = save_optimization_run(
                created_by_email=str(st.session_state.get("user_email")),
                months=list(selected_months),
                solver=solver_name,
                demand_type=demand_type,
                status="success",
                message=outcome.message,
                objective_value=results_u.objective_value,
                cost_breakdown=results_u.cost_breakdown,
                production_df=results_u.production_df,
                transport_df=results_u.transport_df,
                inventory_df=results_u.inventory_df,
                optimization_type=optimization_type,
                scenarios=configured_scenarios,
                scenario_probabilities=scen_data.probability,
                summary_metrics={
                    "avg_inventory": avg_inventory,
                    "avg_buffer": avg_buffer,
                    "solver_used": outcome.solver_used,
                    "runtime_seconds": outcome.runtime_seconds,
                    "solver_log_path": outcome.solver_log_path,
                },
            )

            audit_log(
                event_type="optimization_success",
                actor_email=str(st.session_state.get("user_email") or ""),
                details={
                    "mode": optimization_type,
                    "requested_solver": solver_name,
                    "solver_used": outcome.solver_used,
                    "months": list(selected_months),
                    "runtime_seconds": outcome.runtime_seconds,
                },
            )

            if ok and run_id:
                st.session_state.last_optimization_run_id = run_id
                st.info("Run saved. Open Optimization Results to view and export.")
            else:
                st.warning(msg)
