"""Optimization Results page (Streamlit UI).

What this page does:
- Shows recent optimization runs (history)
- Displays tables and charts for a selected run
- Allows Excel export

Role access:
- Admin & Planner: full access
- Viewer: read-only access

Data flow:
UI -> results.result_service -> MongoDB
"""

from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import streamlit as st

from backend.middleware.role_guard import require_authentication, require_role
from backend.results.result_service import get_recent_runs, get_run


def _rows_to_df(rows: List[Dict[str, Any]]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def _excel_bytes(
    production_df: pd.DataFrame,
    transport_df: pd.DataFrame,
    inventory_df: pd.DataFrame,
) -> bytes:
    """Create an in-memory Excel file."""

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        production_df.to_excel(writer, index=False, sheet_name="Production")
        transport_df.to_excel(writer, index=False, sheet_name="Transport")
        sheet_name = "Inventory"
        if inventory_df is not None and not inventory_df.empty and "scenario" in inventory_df.columns:
            sheet_name = "Inventory (Scenarios)"
        inventory_df.to_excel(writer, index=False, sheet_name=sheet_name)

    return output.getvalue()


def render_optimization_results(role: str) -> None:
    if not require_authentication():
        return

    st.header("Optimization Results")
    st.caption("View optimization runs, tables, charts, and export to Excel.")

    # Viewer is allowed, but read-only (this page is read-only anyway).
    if not require_role(["Admin", "Planner", "Viewer"]):
        return

    runs = get_recent_runs(limit=30)

    if not runs:
        st.info("No optimization runs found yet. Run optimization first.")
        return

    # Create a readable label.
    run_labels = []
    label_to_id: Dict[str, str] = {}

    for r in runs:
        run_id = str(r.get("_id"))
        created_at = r.get("created_at")
        status = r.get("status")
        months = r.get("months", [])
        solver = r.get("solver")

        label = f"{run_id[:8]} | {status} | {solver} | {months} | {created_at}"
        run_labels.append(label)
        label_to_id[label] = run_id

    default_id = st.session_state.get("last_optimization_run_id")

    default_label = run_labels[0]
    if default_id:
        for label in run_labels:
            if label_to_id.get(label) == default_id:
                default_label = label
                break

    selected_label = st.selectbox("Select run", run_labels, index=run_labels.index(default_label))
    selected_id = label_to_id[selected_label]

    run = get_run(selected_id)
    if run is None:
        st.error("Run not found.")
        return

    st.subheader("Run summary")
    col1, col2, col3 = st.columns(3)
    col1.write(f"**Status:** {run.get('status')}")
    col2.write(f"**Solver:** {run.get('solver')}")
    col3.write(f"**Months:** {run.get('months')}")

    opt_type = run.get("optimization_type", "deterministic")
    st.write(f"**Optimization type:** {opt_type}")

    scenarios = run.get("scenarios", []) or []
    scen_probs = run.get("scenario_probabilities", {}) or {}
    if scenarios:
        st.subheader("Demand scenarios")
        st.dataframe(pd.DataFrame(scenarios), use_container_width=True)
    if scen_probs:
        st.write("**Scenario probabilities:**")
        st.dataframe(pd.DataFrame([{"scenario": k, "probability": v} for k, v in scen_probs.items()]), use_container_width=True)

    st.write(f"**Message:** {run.get('message')}")

    obj = float(run.get("objective_value", 0.0) or 0.0)
    st.metric("Objective value (total cost)", round(obj, 2))

    cost = run.get("cost_breakdown", {}) or {}
    st.subheader("Cost breakdown")
    cost_df = pd.DataFrame(
        [
            {"type": "production", "cost": float(cost.get("production", 0.0))},
            {"type": "transport", "cost": float(cost.get("transport", 0.0))},
            {"type": "holding", "cost": float(cost.get("holding", 0.0))},
        ]
    )
    st.dataframe(cost_df, use_container_width=True)

    if not cost_df.empty:
        fig_cost = px.pie(cost_df, names="type", values="cost", title="Cost breakdown")
        st.plotly_chart(fig_cost, use_container_width=True)

    production_df = _rows_to_df(run.get("production_rows", []))
    transport_df = _rows_to_df(run.get("transport_rows", []))
    inventory_df = _rows_to_df(run.get("inventory_rows", []))

    st.divider()
    st.subheader("Production plan")
    st.dataframe(production_df, use_container_width=True)

    if not production_df.empty:
        st.markdown("#### Production mix insights")
        prod_view = st.selectbox(
            "View production by",
            ["Plant", "Month"],
            key="production_view_selector",
            help="Toggle between total production by plant or how plants contribute over the selected months.",
        )

        prod_df = production_df.copy()
        month_order = sorted(prod_df["month"].unique()) if "month" in prod_df.columns else []
        if month_order:
            prod_df["month"] = pd.Categorical(prod_df["month"], categories=month_order, ordered=True)

        if prod_view == "Plant":
            prod_agg = prod_df.groupby("plant", as_index=False)["production"].sum().sort_values("production", ascending=False)
            fig_prod = px.bar(
                prod_agg,
                x="plant",
                y="production",
                color="plant",
                title="Total clinker production by plant",
                labels={"production": "Production (tons)", "plant": "Plant"},
            )
            fig_prod.update_layout(showlegend=False)
            st.plotly_chart(fig_prod, use_container_width=True)
        else:
            fig_prod_trend = px.line(
                prod_df.sort_values(["month", "plant"]),
                x="month",
                y="production",
                color="plant",
                markers=True,
                title="Monthly production trend by plant",
                labels={"production": "Production (tons)", "month": "Month", "plant": "Plant"},
            )
            st.plotly_chart(fig_prod_trend, use_container_width=True)

        st.caption("Use this chart to spot which sites are carrying the load and how production evolves across the planning horizon.")

    st.subheader("Transport plan")
    st.dataframe(transport_df, use_container_width=True)

    if not transport_df.empty:
        st.markdown("#### Transport flow explorer")
        month_options = ["All months"] + sorted({str(m) for m in transport_df.get("month", pd.Series(dtype=str)).dropna().unique().tolist()})
        selected_month = st.selectbox(
            "Filter by month",
            options=month_options,
            key="transport_month_selector",
            help="Focus on a single month or review the combined network load.",
        )

        if selected_month == "All months":
            transport_view_df = transport_df.copy()
        else:
            transport_view_df = transport_df[transport_df["month"].astype(str) == selected_month].copy()

        if transport_view_df.empty:
            st.info("No transport activity recorded for the selected month.")
        else:
            route_agg = (
                transport_view_df
                .groupby(["from", "to", "mode"], as_index=False)
                .agg(shipment=("shipment", "sum"), trips=("trips", "sum"))
            )
            route_agg["route"] = route_agg.apply(lambda r: f"{r['from']} → {r['to']}", axis=1)
            route_agg = route_agg.sort_values("shipment", ascending=False)

            fig_route = px.bar(
                route_agg,
                x="route",
                y="shipment",
                color="mode",
                text="trips",
                title="Shipments by route",
                labels={"route": "Route", "shipment": "Shipment (tons)", "trips": "Trips", "mode": "Mode"},
            )
            fig_route.update_traces(textposition="outside")
            st.plotly_chart(fig_route, use_container_width=True)

            mode_agg = (
                transport_view_df
                .groupby("mode", as_index=False)
                .agg(total_shipment=("shipment", "sum"), total_trips=("trips", "sum"))
            )
            fig_mode = px.bar(
                mode_agg,
                x="mode",
                y=["total_shipment", "total_trips"],
                barmode="group",
                title="Mode utilization (tons vs trips)",
                labels={"value": "Value", "mode": "Mode", "variable": "Metric"},
            )
            st.plotly_chart(fig_mode, use_container_width=True)

        st.caption("Hover over bars to see trips and identify which corridors and modes are the busiest.")

    st.subheader("Inventory levels")
    st.dataframe(inventory_df, use_container_width=True)

    if not inventory_df.empty:
        st.subheader("Inventory trends")
        inv_plot_df = inventory_df

        # Phase 4: scenario-specific inventory.
        if "scenario" in inventory_df.columns:
            scen_list = sorted({str(s) for s in inventory_df["scenario"].dropna().unique().tolist()})
            selected_scen = st.selectbox("Select scenario for inventory chart", options=scen_list, index=0)
            inv_plot_df = inventory_df[inventory_df["scenario"].astype(str) == str(selected_scen)].copy()
            title = f"Inventory by plant over time (Scenario: {selected_scen})"
        else:
            title = "Inventory by plant over time"

        if not inv_plot_df.empty:
            fig_inv = px.line(
                inv_plot_df,
                x="month",
                y="inventory",
                color="plant",
                title=title,
            )
            st.plotly_chart(fig_inv, use_container_width=True)

            heatmap_df = inv_plot_df.pivot_table(index="plant", columns="month", values="inventory", aggfunc="mean")
            if not heatmap_df.empty:
                heatmap_df = heatmap_df.reindex(sorted(heatmap_df.index))
                heatmap_df = heatmap_df[sorted(heatmap_df.columns, key=lambda x: str(x))]
                fig_heat = px.imshow(
                    heatmap_df,
                    color_continuous_scale="YlGnBu",
                    aspect="auto",
                    title="Inventory heatmap (average tons)",
                    labels={"color": "Inventory (tons)"},
                )
                st.plotly_chart(fig_heat, use_container_width=True)

            cushion_df = (
                inv_plot_df
                .groupby("plant", as_index=False)
                .agg(min_inventory=("inventory", "min"), avg_inventory=("inventory", "mean"))
                .sort_values("min_inventory")
            )
            if not cushion_df.empty:
                fig_cushion = px.bar(
                    cushion_df,
                    x="plant",
                    y=["min_inventory", "avg_inventory"],
                    barmode="group",
                    title="Inventory cushion by plant",
                    labels={"value": "Inventory (tons)", "plant": "Plant", "variable": "Metric"},
                )
                st.plotly_chart(fig_cushion, use_container_width=True)

            st.caption("Use the heatmap and cushion chart to spot plants that are drifting close to zero inventory.")

    st.divider()
    st.subheader("Export")

    if production_df is None:
        production_df = pd.DataFrame()
    if transport_df is None:
        transport_df = pd.DataFrame()
    if inventory_df is None:
        inventory_df = pd.DataFrame()

    excel_data = _excel_bytes(production_df, transport_df, inventory_df)

    st.download_button(
        label="Download Excel",
        data=excel_data,
        file_name=f"optimization_run_{selected_id}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
