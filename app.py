"""Main Streamlit entry point.

This file is responsible for:
- Setting up Streamlit page settings
- Creating simple navigation (Login / Signup / Dashboard)
- Managing Logout

The actual authentication logic lives in backend/auth/*.
The actual database logic lives in backend/database/*.
"""

import os
import streamlit as st

# Ensure CBC solver is in PATH before any checks
_cbc_path = r"C:\solvers\cbc\bin"
if os.path.exists(_cbc_path):
    current_path = os.environ.get("PATH", "")
    if _cbc_path not in current_path:
        os.environ["PATH"] = _cbc_path + os.pathsep + current_path

# Fix statsmodels import issue for plotly trendline functions
try:
    import statsmodels.api as sm
except ImportError:
    # Apply comprehensive statsmodels fix
    from statsmodels_fix import patch_statsmodels, patch_plotly_trendline
    patch_statsmodels()
    patch_plotly_trendline()

from backend.auth.session import (
    ensure_session_defaults,
    is_authenticated,
    logout_user,
)
from backend.core.error_handler import safe_page
from backend.core.logger import get_logger
from backend.core.logger import audit_log
from backend.utils.health_check import run_startup_checks
from ui.login import render_login_page
from ui.signup import render_signup_page
from ui.dashboards import render_dashboard
from ui.plant_page import render_plant_page
from ui.demand_page import render_demand_page
from ui.transport_page import render_transport_page
from ui.inventory_page import render_inventory_page
from ui.optimization_run import render_optimization_run
from ui.optimization_results import render_optimization_results
from ui.uncertainty_settings import render_uncertainty_settings
from ui.scenario_comparison import render_scenario_comparison
from ui.management_dashboard import render_management_dashboard
from ui.run_comparison import render_run_comparison
from ui.demand_uncertainty_ui import render_demand_uncertainty_analysis


def main() -> None:
    """Streamlit apps rerun top-to-bottom on every interaction."""

    logger = get_logger()

    st.set_page_config(
        page_title="Role-Based Auth System",
        page_icon="Auth",
        layout="centered",
    )

    ensure_session_defaults()

    # Phase 6: startup checks (DB + solver availability).
    checks = run_startup_checks()
    if not checks.get("mongo", {}).get("ok", False):
        logger.error("Startup check failed: %s", checks)
        st.error("Database is not reachable. Please check configuration and try again.")
        return

    solver_check = checks.get("solvers", {})
    if not solver_check.get("ok", False):
        solver_status = solver_check.get("message", "Unknown")
        st.warning(f"No solver is available on this machine. {solver_status} Optimization will not run.")
    else:
        # Show which solver is available
        available_solvers = []
        if solver_check.get("cbc", False):
            available_solvers.append("CBC")
        if solver_check.get("gurobi", False):
            available_solvers.append("Gurobi")
        if solver_check.get("highs", False):
            available_solvers.append("HiGHS")
        if solver_check.get("scip", False):
            available_solvers.append("SCIP")
        if available_solvers:
            st.success(f"✓ Optimization solver available: {', '.join(available_solvers)}")

    st.title("Role-Based Authentication System")

    # Simple navigation based on session status.
    if is_authenticated():
        role = st.session_state.get("user_role")

        st.sidebar.markdown("## Navigation")

        # Pages available after login.
        pages = [
            "Dashboard",
            "Plants",
            "Demands",
            "Transport",
            "Inventory Policies",
            "Run Optimization",
            "Optimization Results",
            "Demand Uncertainty Settings",
            "Scenario Comparison",
            "Demand Uncertainty Analysis",
            "Management Insights Dashboard",
            "Run Comparison",
        ]

        # Sidebar page selection.
        choice = st.sidebar.radio("Go to", pages)

        # Logout should always be visible.
        if st.sidebar.button("Logout"):
            audit_log(
                event_type="logout",
                actor_email=str(st.session_state.get("user_email") or ""),
                details={"role": str(st.session_state.get("user_role") or "")},
            )
            logout_user()
            st.success("You have been logged out.")
            st.info("Please login again to continue.")
            render_login_page()
            return

        # Route to the selected page.
        if choice == "Dashboard":
            safe_page("Dashboard")(render_dashboard)()
        elif choice == "Plants":
            safe_page("Plants")(render_plant_page)(role=role)
        elif choice == "Demands":
            safe_page("Demands")(render_demand_page)(role=role)
        elif choice == "Transport":
            safe_page("Transport")(render_transport_page)(role=role)
        elif choice == "Inventory Policies":
            safe_page("Inventory Policies")(render_inventory_page)(role=role)
        elif choice == "Run Optimization":
            safe_page("Run Optimization")(render_optimization_run)(role=role)
        elif choice == "Demand Uncertainty Settings":
            safe_page("Demand Uncertainty Settings")(render_uncertainty_settings)(role=role)
        elif choice == "Scenario Comparison":
            safe_page("Scenario Comparison")(render_scenario_comparison)(role=role)
        elif choice == "Demand Uncertainty Analysis":
            safe_page("Demand Uncertainty Analysis")(render_demand_uncertainty_analysis)()
        elif choice == "Management Insights Dashboard":
            safe_page("Management Insights Dashboard")(render_management_dashboard)(role=role)
        elif choice == "Run Comparison":
            safe_page("Run Comparison")(render_run_comparison)(role=role)
        else:
            safe_page("Optimization Results")(render_optimization_results)(role=role)
    else:
        choice = st.sidebar.radio("Navigation", ["Login", "Signup"])

        if choice == "Login":
            render_login_page()
        else:
            render_signup_page()


if __name__ == "__main__":
    main()
