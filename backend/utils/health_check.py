"""Health checks for deployment readiness.

This module performs startup checks:
- MongoDB connectivity
- Solver availability (gurobi/cbc)

It returns simple status dictionaries suitable for showing in Streamlit.
"""

from __future__ import annotations

import os
from typing import Any, Dict

import pyomo.environ as pyo

# Ensure CBC solver is in PATH before checking
_cbc_path = r"C:\solvers\cbc\bin"
if os.path.exists(_cbc_path):
    current_path = os.environ.get("PATH", "")
    if _cbc_path not in current_path:
        os.environ["PATH"] = _cbc_path + os.pathsep + current_path


def check_mongo() -> Dict[str, Any]:
    try:
        from backend.database.mongo import get_client

        client = get_client()
        client.admin.command("ping")
        return {"ok": True, "message": "MongoDB reachable."}
    except Exception as exc:
        return {"ok": False, "message": f"MongoDB not reachable: {exc}"}


def check_solvers() -> Dict[str, Any]:
    def _available(name: str) -> bool:
        try:
            s = pyo.SolverFactory(name)
            return s is not None and s.available(exception_flag=False)
        except Exception:
            return False

    gurobi_ok = _available("gurobi")
    cbc_ok = _available("cbc")
    highs_ok = _available("highs") or _available("appsi_highs")
    scip_ok = _available("scip")

    return {
        "ok": bool(gurobi_ok or cbc_ok or highs_ok or scip_ok),
        "gurobi": gurobi_ok,
        "cbc": cbc_ok,
        "highs": highs_ok,
        "scip": scip_ok,
        "message": f"Solver availability: gurobi={gurobi_ok}, cbc={cbc_ok}, highs={highs_ok}, scip={scip_ok}",
    }


def run_startup_checks() -> Dict[str, Any]:
    mongo = check_mongo()
    solvers = check_solvers()
    return {"mongo": mongo, "solvers": solvers}
