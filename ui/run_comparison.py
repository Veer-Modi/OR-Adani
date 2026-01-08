"""Run comparison analytics.

This page compares two optimization runs:
- deterministic vs stochastic
- expected vs robust
- any two selected runs

It focuses on explainable business deltas:
- total cost difference
- cost per ton difference
- average inventory difference
- inventory buffer difference

Role access:
- Admin/Planner/Viewer: view
"""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd
import plotly.express as px
import streamlit as st

from backend.analytics.analytics_service import compute_and_store_analytics
from backend.middleware.role_guard import require_authentication, require_role
from backend.results.result_service import get_recent_runs, get_run


def _label(r: Dict[str, Any]) -> str:
    run_id = str(r.get("_id"))
    created_at = r.get("created_at")
    status = r.get("status")
    opt_type = r.get("optimization_type", "deterministic")
    months = r.get("months", [])
    return f"{run_id[:8]} | {status} | {opt_type} | {months} | {created_at}"


def _ensure_analytics(run_id: str, role: str) -> None:
    run = get_run(run_id)
    if not run:
        return
    if run.get("analytics"):
        return
    if role != "Admin":
        return
    compute_and_store_analytics(run_id)


def render_run_comparison(role: str) -> None:
    if not require_authentication():
        return

    st.header("Run Comparison")
    st.caption("Compare KPIs between two runs (deterministic vs stochastic vs robust).")

    if not require_role(["Admin", "Planner", "Viewer"]):
        return

    runs = get_recent_runs(limit=60)
    runs = [r for r in runs if str(r.get("status") or "") == "success"]
    if len(runs) < 2:
        st.info("Need at least two successful runs to compare.")
        return

    labels = [_label(r) for r in runs]
    label_to_id = {labels[i]: str(runs[i].get("_id")) for i in range(len(runs))}

    col1, col2 = st.columns(2)
    label_a = col1.selectbox("Run A", labels, index=0)
    label_b = col2.selectbox("Run B", labels, index=1)

    run_a_id = label_to_id[label_a]
    run_b_id = label_to_id[label_b]

    _ensure_analytics(run_a_id, role)
    _ensure_analytics(run_b_id, role)

    run_a = get_run(run_a_id)
    run_b = get_run(run_b_id)

    if not run_a or not run_b:
        st.error("Selected runs could not be loaded.")
        return

    kpi_a = (run_a.get("analytics") or {}).get("kpis") or {}
    kpi_b = (run_b.get("analytics") or {}).get("kpis") or {}

    if not kpi_a or not kpi_b:
        st.warning("Analytics missing for one or both runs. Admin can compute analytics via Management Dashboard.")
        return

    # Core KPI comparison table
    keys = [
        "total_cost",
        "cost_per_ton",
        "avg_inventory",
        "avg_inventory_buffer",
        "inventory_turnover",
        "service_level_percent",
    ]

    rows = []
    for k in keys:
        a = float(kpi_a.get(k, 0.0) or 0.0)
        b = float(kpi_b.get(k, 0.0) or 0.0)
        rows.append({"kpi": k, "run_a": a, "run_b": b, "delta_b_minus_a": b - a})

    comp_df = pd.DataFrame(rows)
    st.subheader("KPI differences")
    st.dataframe(comp_df, use_container_width=True)

    fig = px.bar(comp_df, x="kpi", y="delta_b_minus_a", title="Delta (Run B - Run A)")
    st.plotly_chart(fig, use_container_width=True)

    # Cost breakdown comparison
    st.subheader("Cost breakdown comparison")
    cost_a = {
        "Production": float(kpi_a.get("cost_production", 0.0) or 0.0),
        "Transport": float(kpi_a.get("cost_transport", 0.0) or 0.0),
        "Holding": float(kpi_a.get("cost_holding", 0.0) or 0.0),
    }
    cost_b = {
        "Production": float(kpi_b.get("cost_production", 0.0) or 0.0),
        "Transport": float(kpi_b.get("cost_transport", 0.0) or 0.0),
        "Holding": float(kpi_b.get("cost_holding", 0.0) or 0.0),
    }

    cost_rows = []
    for k in cost_a.keys():
        cost_rows.append({"type": k, "run": "A", "cost": cost_a[k]})
        cost_rows.append({"type": k, "run": "B", "cost": cost_b[k]})

    cost_df = pd.DataFrame(cost_rows)
    fig2 = px.bar(cost_df, x="type", y="cost", color="run", barmode="group", title="Cost split")
    st.plotly_chart(fig2, use_container_width=True)
