"""Scenario comparison dashboard.

This page compares optimization run types:
- Deterministic (Phase 3)
- Stochastic (expected-cost)
- Robust (worst-case)

The dashboard is intentionally simple:
- Cost comparison
- Inventory buffer comparison
- Scenario unmet demand (should be 0 if model is feasible)

Note:
- In Phase 4, unmet demand is not allowed (hard constraint), so it should be 0.
  If the model is infeasible, the run will be marked as failed.
"""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd
import plotly.express as px
import streamlit as st

from backend.middleware.role_guard import require_authentication, require_role
from backend.results.result_service import get_recent_runs


def render_scenario_comparison(role: str) -> None:
    if not require_authentication():
        return

    st.header("Scenario Comparison")
    st.caption("Compare deterministic vs stochastic vs robust runs.")

    if not require_role(["Admin", "Planner", "Viewer"]):
        return

    runs = get_recent_runs(limit=60)
    if not runs:
        st.info("No runs found yet.")
        return

    # Only compare successful runs.
    runs = [r for r in runs if (r.get("status") or "") == "success"]
    if not runs:
        st.info("No successful runs available to compare.")
        return

    df = pd.DataFrame(
        [
            {
                "run_id": str(r.get("_id")),
                "created_at": r.get("created_at"),
                "optimization_type": r.get("optimization_type", "deterministic"),
                "objective_value": float(r.get("objective_value", 0.0) or 0.0),
                "avg_inventory": float((r.get("summary_metrics", {}) or {}).get("avg_inventory", 0.0) or 0.0),
                "avg_buffer": float((r.get("summary_metrics", {}) or {}).get("avg_buffer", 0.0) or 0.0),
            }
            for r in runs
        ]
    )

    if df.empty:
        st.info("No comparable run data.")
        return

    # Limit to most recent per type to keep UI clean.
    df = df.sort_values("created_at", ascending=False)

    # Handle case where there are fewer runs than minimum slider value
    max_slider_value = max(5, min(50, len(df)))
    
    sample_size = st.slider(
        "Number of recent runs to display",
        min_value=5,
        max_value=max_slider_value,
        value=min(15, len(df)),
        step=5,
        help="Adjust how many of the most recent runs are included in the charts below.",
    )

    df_sample = df.head(sample_size)

    st.subheader("Total cost comparison")
    fig_cost = px.bar(
        df_sample,
        x="run_id",
        y="objective_value",
        color="optimization_type",
        title="Objective value by run",
    )
    fig_cost.update_layout(xaxis_title="Run", yaxis_title="Total cost", xaxis_tickangle=-35)
    st.plotly_chart(fig_cost, use_container_width=True)

    st.subheader("Inventory buffer comparison")
    fig_buf = px.bar(
        df_sample,
        x="run_id",
        y="avg_buffer",
        color="optimization_type",
        title="Average inventory buffer (inventory - safety_stock)",
    )
    fig_buf.update_layout(xaxis_title="Run", yaxis_title="Avg buffer (tons)", xaxis_tickangle=-35)
    st.plotly_chart(fig_buf, use_container_width=True)

    st.subheader("Cost vs buffer trade-off")
    fig_tradeoff = px.scatter(
        df_sample,
        x="avg_buffer",
        y="objective_value",
        color="optimization_type",
        hover_name="run_id",
        trendline="ols",
        title="Trade-off between inventory buffer and total cost",
        labels={"avg_buffer": "Avg buffer (tons)", "objective_value": "Total cost"},
    )
    st.plotly_chart(fig_tradeoff, use_container_width=True)
    st.caption("Points further left show leaner inventories. Compare colors to see which planning mode gives the best balance.")

    if "created_at" in df_sample.columns:
        timeline_df = df_sample.sort_values("created_at")
        try:
            timeline_df["created_at"] = pd.to_datetime(timeline_df["created_at"])
        except Exception:
            pass
        if timeline_df["created_at"].dtype != object:
            st.subheader("Timeline of recent runs")
            fig_time = px.line(
                timeline_df,
                x="created_at",
                y="objective_value",
                color="optimization_type",
                markers=True,
                title="Objective value trend",
                labels={"created_at": "Created at", "objective_value": "Total cost"},
            )
            st.plotly_chart(fig_time, use_container_width=True)

    st.subheader("Runs table")
    st.dataframe(df_sample, use_container_width=True)
