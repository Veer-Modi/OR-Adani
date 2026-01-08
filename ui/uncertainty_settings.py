"""Demand Uncertainty Settings page.

This UI is intentionally simple and educational:
- 3 scenarios (Low/Normal/High) by default
- Each has a probability and a demand multiplier

Business interpretation:
- Demand multiplier 0.9 means "10% lower than base (Fixed) demand".
- Demand multiplier 1.1 means "10% higher than base demand".

Role access:
- Admin & Planner: can edit and save
- Viewer: view only
"""

from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st

from backend.middleware.role_guard import require_authentication, require_role
from backend.uncertainty.uncertainty_service import get_uncertainty_settings, upsert_uncertainty_settings


def render_uncertainty_settings(role: str) -> None:
    if not require_authentication():
        return

    st.header("Demand Uncertainty Settings")
    st.caption("Configure Low/Normal/High demand scenarios and probabilities.")

    if not require_role(["Admin", "Planner", "Viewer"]):
        return

    settings = get_uncertainty_settings()

    can_edit = role in {"Admin", "Planner"}

    is_enabled = st.checkbox(
        "Enable demand uncertainty",
        value=bool(settings.get("is_enabled", False)),
        disabled=not can_edit,
        help="If disabled, optimization runs are deterministic (Phase 3 behavior).",
    )

    st.subheader("Scenarios")
    st.caption("Probabilities must sum to 1. Multipliers scale the base Fixed demand.")

    scenarios: List[Dict[str, Any]] = settings.get("scenarios") or []
    if not scenarios:
        scenarios = [
            {"name": "Low", "probability": 0.2, "demand_multiplier": 0.9},
            {"name": "Normal", "probability": 0.6, "demand_multiplier": 1.0},
            {"name": "High", "probability": 0.2, "demand_multiplier": 1.1},
        ]

    edited: List[Dict[str, Any]] = []
    total_prob = 0.0

    for idx, s in enumerate(scenarios):
        col1, col2, col3 = st.columns(3)
        name = col1.text_input(
            f"Scenario name #{idx + 1}",
            value=str(s.get("name", "")),
            disabled=True,
        )
        prob = col2.number_input(
            f"Probability ({name})",
            min_value=0.0,
            max_value=1.0,
            value=float(s.get("probability", 0.0) or 0.0),
            step=0.05,
            disabled=not can_edit,
        )
        mult = col3.number_input(
            f"Demand multiplier ({name})",
            min_value=0.0,
            value=float(s.get("demand_multiplier", 1.0) or 1.0),
            step=0.05,
            disabled=not can_edit,
        )

        total_prob += float(prob)
        edited.append({"name": name, "probability": float(prob), "demand_multiplier": float(mult)})

    st.write(f"**Probability sum:** {round(total_prob, 4)}")
    if abs(total_prob - 1.0) > 1e-6:
        st.warning("Probabilities must sum to 1.")

    if can_edit:
        if st.button("Save settings"):
            ok, msg = upsert_uncertainty_settings({"is_enabled": is_enabled, "scenarios": edited})
            if ok:
                st.success(msg)
            else:
                st.error(msg)
    else:
        st.info("Viewer role: view-only.")
