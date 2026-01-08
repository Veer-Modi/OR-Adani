"""Management Insights Dashboard.

This page is meant for non-technical decision makers.
It summarizes the most important KPIs and flags bottlenecks.

Role access:
- Admin: can recompute analytics
- Planner/Viewer: view only

Data source:
- Stored optimization runs in MongoDB
- Stored analytics inside each run document
"""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from backend.analytics.analytics_service import compute_and_store_analytics
from backend.middleware.role_guard import require_authentication, require_role
from backend.results.result_service import get_recent_runs, get_run


def _pick_run_label(r: Dict[str, Any]) -> str:
    run_id = str(r.get("_id"))
    created_at = r.get("created_at")
    status = r.get("status")
    solver = r.get("solver")
    opt_type = r.get("optimization_type", "deterministic")
    months = r.get("months", [])
    return f"{run_id[:8]} | {status} | {opt_type} | {solver} | {months} | {created_at}"


def render_management_dashboard(role: str) -> None:
    if not require_authentication():
        return

    st.header("Management Insights Dashboard")
    st.caption("Enterprise KPI view of optimization outcomes, utilization, bottlenecks, and cost drivers.")

    if not require_role(["Admin", "Planner", "Viewer"]):
        return

    runs = get_recent_runs(limit=50)
    runs = [r for r in runs if str(r.get("status") or "") == "success"]
    if not runs:
        st.info("No successful runs found.")
        return

    labels = [_pick_run_label(r) for r in runs]
    label_to_id = {labels[i]: str(runs[i].get("_id")) for i in range(len(runs))}

    selected_label = st.selectbox("Select run", labels, index=0)
    run_id = label_to_id[selected_label]

    run = get_run(run_id)
    if run is None:
        st.error("Run not found.")
        return

    can_edit = role == "Admin"

    if can_edit:
        if st.button("Compute / Refresh analytics for this run"):
            ok, msg = compute_and_store_analytics(run_id)
            if ok:
                st.success(msg)
                run = get_run(run_id) or run
            else:
                st.error(msg)

    analytics = run.get("analytics") or {}
    kpis = analytics.get("kpis") or {}
    resilience = analytics.get("resilience") or {}

    if not kpis:
        st.warning("Analytics not computed for this run yet. Admin can compute it using the button above.")
        return

    st.subheader("KPI Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total cost", round(float(kpis.get("total_cost", 0.0)), 2))
    c2.metric("Cost / ton", round(float(kpis.get("cost_per_ton", 0.0)), 2))
    c3.metric("Service level (%)", round(float(kpis.get("service_level_percent", 0.0)), 2))
    c4.metric("Inventory turnover", round(float(kpis.get("inventory_turnover", 0.0)), 2))

    st.subheader("Supply chain resilience")
    res_score = float(resilience.get("score", 0.0) or 0.0)
    res_class = resilience.get("classification", "Not computed")

    c_res_left, c_res_right = st.columns([2, 1])

    gauge = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=res_score,
            delta={"reference": 60, "increasing": {"color": "#2E7D32"}},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#1E88E5"},
                "steps": [
                    {"range": [0, 60], "color": "#ef5350"},
                    {"range": [60, 80], "color": "#ffb300"},
                    {"range": [80, 100], "color": "#43a047"},
                ],
            },
            title={"text": f"Resilience score · {res_class}"},
        )
    )
    gauge.update_layout(height=260, margin=dict(l=30, r=30, t=60, b=20))
    c_res_left.plotly_chart(gauge, use_container_width=True)

    components = resilience.get("components", {})
    with c_res_right:
        st.markdown("#### Component health")
        st.metric("Service level", f"{components.get('service_level', 0.0):.1f}%")
        st.metric("Production headroom", f"{components.get('production_headroom', 0.0):.1f}%")
        st.metric("Storage headroom", f"{components.get('storage_headroom', 0.0):.1f}%")
        st.metric("Transport headroom", f"{components.get('transport_headroom', 0.0):.1f}%")

    col_alerts, col_recos = st.columns(2)
    alerts = resilience.get("alerts", [])
    recommendations = resilience.get("recommendations", [])

    with col_alerts:
        st.markdown("#### Risk alerts")
        if alerts:
            for alert in alerts:
                st.error(alert)
        else:
            st.success("No critical alerts. Network is operating within buffers.")

    with col_recos:
        st.markdown("#### Recommended actions")
        for reco in recommendations:
            st.info(reco)

    st.subheader("Cost breakdown")
    cost_df = pd.DataFrame(
        [
            {"type": "Production", "cost": float(kpis.get("cost_production", 0.0))},
            {"type": "Transport", "cost": float(kpis.get("cost_transport", 0.0))},
            {"type": "Holding", "cost": float(kpis.get("cost_holding", 0.0))},
        ]
    )
    st.dataframe(cost_df, use_container_width=True)
    fig = px.pie(cost_df, names="type", values="cost", title="Cost split")
    st.plotly_chart(fig, use_container_width=True)

    util = analytics.get("utilization") or {}

    st.subheader("Capacity utilization")
    prod_util_df = pd.DataFrame(util.get("production", []) or [])
    if not prod_util_df.empty:
        prod_view = prod_util_df.copy()
        prod_view["headroom_percent"] = (100.0 - prod_view["utilization_percent"]).clip(lower=0)
        fig_prod = px.bar(
            prod_view.melt(id_vars=["plant"], value_vars=["utilization_percent", "headroom_percent"], var_name="Metric", value_name="Percent"),
            x="plant",
            y="Percent",
            color="Metric",
            barmode="stack",
            title="Production load vs headroom",
            labels={"Percent": "Percent (%)", "plant": "Plant"},
        )
        fig_prod.update_layout(legend_title_text="", yaxis=dict(range=[0, 100]))
        st.plotly_chart(fig_prod, use_container_width=True)
        st.caption("Blue shows how much of each plant's clinker capacity is booked. Grey shows spare headroom.")

    storage_util_df = pd.DataFrame(util.get("storage", []) or [])
    if not storage_util_df.empty:
        storage_sorted = storage_util_df.sort_values("utilization_percent", ascending=False)
        fig_st = px.bar(
            storage_sorted,
            x="utilization_percent",
            y="plant",
            orientation="h",
            title="Storage utilization by site",
            labels={"utilization_percent": "Average fill (%)", "plant": "Plant"},
            color="utilization_percent",
            color_continuous_scale="Blues",
        )
        st.plotly_chart(fig_st, use_container_width=True)
        st.caption("Look for bars near 100% – those silos leave little room for demand spikes.")

    transport_util_df = pd.DataFrame(util.get("transport", []) or [])
    if not transport_util_df.empty:
        st.markdown("### Transport network load")
        month_options = sorted(transport_util_df["month"].astype(str).unique().tolist()) if "month" in transport_util_df.columns else []
        month_filter = st.selectbox(
            "Show utilization for month",
            options=["All months"] + month_options,
            key="management_transport_month",
            help="Switch to a specific month to zoom into seasonal peaks.",
        )

        if month_filter != "All months":
            trans_view = transport_util_df[transport_util_df["month"].astype(str) == month_filter].copy()
        else:
            trans_view = transport_util_df.copy()

        if trans_view.empty:
            st.info("No transport records for the selected month.")
        else:
            route_heat = (
                trans_view
                .groupby(["from", "to"], as_index=False)["utilization_percent"]
                .mean()
            )
            route_heat["route"] = route_heat.apply(lambda r: f"{r['from']} → {r['to']}", axis=1)
            route_heat = route_heat.sort_values("utilization_percent", ascending=False)
            fig_route = px.bar(
                route_heat,
                x="route",
                y="utilization_percent",
                title="Average route utilization",
                labels={"route": "Route", "utilization_percent": "Average utilization (%)"},
                color="utilization_percent",
                color_continuous_scale="Viridis",
            )
            fig_route.update_layout(xaxis_tickangle=-30)
            st.plotly_chart(fig_route, use_container_width=True)

            if "month" in trans_view.columns:
                timeline = (
                    transport_util_df
                    .groupby("month", as_index=False)["utilization_percent"]
                    .mean()
                    .sort_values("month")
                )
                fig_timeline = px.line(
                    timeline,
                    x="month",
                    y="utilization_percent",
                    markers=True,
                    title="Network utilization trend",
                    labels={"month": "Month", "utilization_percent": "Avg utilization (%)"},
                )
                st.plotly_chart(fig_timeline, use_container_width=True)
        st.caption("Use these visuals to find lanes consistently running hot and months where the network nears saturation.")

    st.subheader("Bottlenecks")
    bn = analytics.get("bottlenecks") or {}

    plant_bn = pd.DataFrame(bn.get("plants", []) or [])
    route_bn = pd.DataFrame(bn.get("routes", []) or [])
    inv_bn = pd.DataFrame(bn.get("inventory", []) or [])

    if plant_bn.empty and route_bn.empty and inv_bn.empty:
        st.success("No bottlenecks flagged by current thresholds.")
    else:
        if not plant_bn.empty:
            st.warning("Plants near max capacity")
            st.dataframe(plant_bn, use_container_width=True)
        if not route_bn.empty:
            st.warning("Routes near full capacity")
            st.dataframe(route_bn, use_container_width=True)
        if not inv_bn.empty:
            st.warning("Inventory hitting safety stock")
            st.dataframe(inv_bn, use_container_width=True)

    st.subheader("Cost drivers")
    cd = analytics.get("cost_drivers") or {}

    top_plants = pd.DataFrame(cd.get("top_plants", []) or [])
    top_routes = pd.DataFrame(cd.get("top_routes", []) or [])
    mode_cost = pd.DataFrame(cd.get("mode_cost", []) or [])

    colA, colB = st.columns(2)
    colA.write("Top cost-driving plants")
    colA.dataframe(top_plants, use_container_width=True)

    colB.write("Top expensive routes")
    colB.dataframe(top_routes, use_container_width=True)

    if not mode_cost.empty:
        fig_mode = px.bar(mode_cost, x="mode", y="cost", title="Transport cost by mode")
        st.plotly_chart(fig_mode, use_container_width=True)
