"""Solver integration.

This module runs the optimization using a chosen solver:
- Primary: Gurobi
- Fallback: CBC

Beginner tip:
- Pyomo builds a math model
- A solver (like Gurobi) finds the best solution
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from datetime import datetime
import os
import time

import pyomo.environ as pyo

from backend.core.config_manager import get_config
from backend.core.logger import get_logger

# Ensure CBC solver is in PATH before using it
_cbc_path = r"C:\solvers\cbc\bin"
if os.path.exists(_cbc_path):
    current_path = os.environ.get("PATH", "")
    if _cbc_path not in current_path:
        os.environ["PATH"] = _cbc_path + os.pathsep + current_path


@dataclass
class SolverConfig:
    solver_name: str  # "gurobi", "cbc", or "highs"
    time_limit_seconds: int = 60
    mip_gap: float = 0.01


@dataclass
class SolveOutcome:
    ok: bool
    message: str
    termination_condition: str
    solver_status: str
    solver_used: str | None = None
    runtime_seconds: float | None = None
    solver_log_path: str | None = None


def solve_model(model: pyo.ConcreteModel, config: SolverConfig) -> SolveOutcome:
    """Solve a Pyomo model and return a friendly status."""

    logger = get_logger()
    cfg = get_config()

    requested_solver = (config.solver_name or "").strip().lower()

    if requested_solver not in {"gurobi", "cbc", "highs", "scip"}:
        return SolveOutcome(
            ok=False,
            message="Invalid solver selected.",
            termination_condition="invalid",
            solver_status="invalid",
            solver_used=None,
        )

    # Phase 6: automatic fallback.
    # Preference order:
    # - user requested solver
    # - if gurobi requested: try cbc, then highs, then scip
    # - if cbc requested: try highs, then scip
    # - if highs requested: try scip
    # - if scip requested: no further fallback
    solver_name = requested_solver
    fallback_chain: list[str]
    if requested_solver == "gurobi":
        fallback_chain = ["cbc", "highs", "scip"]
    elif requested_solver == "cbc":
        fallback_chain = ["highs", "scip"]
    elif requested_solver == "highs":
        fallback_chain = ["scip"]
    else:
        fallback_chain = []

    solver = pyo.SolverFactory(solver_name)
    if solver is None or not solver.available(exception_flag=False):
        for alt in fallback_chain:
            logger.warning(f"Solver '{solver_name}' not available; falling back to {alt}.")
            solver_name = alt
            solver = pyo.SolverFactory(solver_name)
            if solver is not None and solver.available(exception_flag=False):
                break

        if solver is None or not solver.available(exception_flag=False):
            return SolveOutcome(
                ok=False,
                message=(
                    "No solver is available on this machine. "
                    "Install an open-source solver: SCIP via 'pip install pyscipopt', "
                    "HiGHS via 'pip install highspy', or configure Gurobi/CBC and try again."
                ),
                termination_condition="not_available",
                solver_status="not_available",
                solver_used=None,
            )

    # Configure common options.
    try:
        if solver_name == "gurobi":
            solver.options["TimeLimit"] = int(config.time_limit_seconds)
            solver.options["MIPGap"] = float(config.mip_gap)
        elif solver_name == "cbc":
            # CBC uses different option names.
            solver.options["seconds"] = int(config.time_limit_seconds)
            # CBC mip gap option may differ by build; keep it optional.
        elif solver_name == "highs":
            # HiGHS option names may vary; keep it minimal and avoid hard failures.
            pass
        elif solver_name == "scip":
            # SCIP solver options
            solver.options["limits/time"] = int(config.time_limit_seconds)
            solver.options["limits/gap"] = float(config.mip_gap)
    except Exception:
        # If options fail, still try solving.
        pass

    try:
        tee = bool(cfg.solver_logs_enabled)
        log_path: str | None = None

        # Optional: write solver output to a file.
        if tee:
            os.makedirs(cfg.log_dir, exist_ok=True)
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            log_path = os.path.join(cfg.log_dir, f"solver_{solver_name}_{ts}.log")
            solver.options["logfile"] = log_path

        start = time.time()
        results = solver.solve(model, tee=tee)
        runtime = time.time() - start
    except Exception as exc:
        return SolveOutcome(
            ok=False,
            message="Solver failed to run. Please try again or change solver settings.",
            termination_condition="error",
            solver_status="error",
            solver_used=solver_name,
        )

    status = str(getattr(results.solver, "status", "unknown"))
    term = str(getattr(results.solver, "termination_condition", "unknown"))

    # Common termination conditions:
    # - optimal
    # - infeasible
    # - maxTimeLimit
    # - feasible
    ok = term.lower() in {"optimal", "feasible"}

    if term.lower() == "infeasible":
        return SolveOutcome(
            ok=False,
            message="Model is infeasible (no plan satisfies all constraints). Check inputs and constraints.",
            termination_condition=term,
            solver_status=status,
            solver_used=solver_name,
            runtime_seconds=float(runtime) if "runtime" in locals() else None,
            solver_log_path=log_path if "log_path" in locals() else None,
        )

    if not ok:
        return SolveOutcome(
            ok=False,
            message=f"Solver finished with status={status}, termination={term}.",
            termination_condition=term,
            solver_status=status,
            solver_used=solver_name,
            runtime_seconds=float(runtime) if "runtime" in locals() else None,
            solver_log_path=log_path if "log_path" in locals() else None,
        )

    return SolveOutcome(
        ok=True,
        message="Optimization solved successfully.",
        termination_condition=term,
        solver_status=status,
        solver_used=solver_name,
        runtime_seconds=float(runtime) if "runtime" in locals() else None,
        solver_log_path=log_path if "log_path" in locals() else None,
    )
