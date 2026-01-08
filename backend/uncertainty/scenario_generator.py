"""Scenario generator.

Business idea (simple):
- Planners keep a single "base" demand (usually the existing Fixed demand).
- Uncertainty is represented as a few scenarios that scale the base demand:
  - Low / Normal / High

Why scaling?
- It is easy to explain.
- It avoids duplicating demand entry for every plant-month-scenario.

The output of this module is a clean structure the optimization model can use:
- scenario_names: ["Low", "Normal", "High"]
- probabilities: {"Low": 0.2, ...}
- demand_by_scenario[(scenario, plant_id, month)] = demand_qty
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from backend.optimization.data_loader import OptimizationData


@dataclass
class DemandScenario:
    name: str
    probability: float
    demand_multiplier: float


@dataclass
class ScenarioDemandData:
    scenario_names: List[str]
    probability: Dict[str, float]
    demand: Dict[Tuple[str, str, str], float]


def generate_demand_scenarios(
    base_data: OptimizationData,
    scenarios: List[DemandScenario],
) -> ScenarioDemandData:
    """Generate scenario-specific demands from base demand.

    Args:
        base_data: OptimizationData created by assemble_optimization_data (usually with demand_type_filter="Fixed").
        scenarios: list of scenario definitions.

    Returns:
        ScenarioDemandData with demand[(scenario, plant_id, month)]

    Raises:
        ValueError if probabilities are invalid.
    """

    if not scenarios:
        raise ValueError("No scenarios configured.")

    names = [s.name.strip() for s in scenarios if (s.name or "").strip()]
    if len(names) != len(set(names)):
        raise ValueError("Scenario names must be unique.")

    prob: Dict[str, float] = {}
    for s in scenarios:
        try:
            p = float(s.probability)
        except Exception:
            raise ValueError("Scenario probability must be a number.")
        if p < 0:
            raise ValueError("Scenario probability cannot be negative.")
        prob[s.name] = p

    total_p = sum(prob.values())
    if abs(total_p - 1.0) > 1e-6:
        raise ValueError("Scenario probabilities must sum to 1.")

    demand: Dict[Tuple[str, str, str], float] = {}
    for s in scenarios:
        try:
            mult = float(s.demand_multiplier)
        except Exception:
            raise ValueError("Demand multiplier must be a number.")
        if mult < 0:
            raise ValueError("Demand multiplier cannot be negative.")

        for p in base_data.plant_ids:
            for t in base_data.months:
                base = float(base_data.demand.get((p, t), 0.0) or 0.0)
                demand[(s.name, p, t)] = base * mult

    return ScenarioDemandData(
        scenario_names=names,
        probability=prob,
        demand=demand,
    )
