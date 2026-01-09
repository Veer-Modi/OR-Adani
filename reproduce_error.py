
import pandas as pd
from backend.optimization.feasible_excel_loader import load_feasible_excel_data
from backend.optimization.feasible_model import build_feasible_model
from backend.optimization.result_parser import parse_results
from backend.optimization.solver import solve_model, SolverConfig

def reproduce():
    print("Loading data (FULL MODEL)...")
    data = load_feasible_excel_data(
        file_path="Dataset_Dummy_Clinker_3MPlan.xlsx",
        selected_months=['1']
    )
    
    print("Building model (FULL MODEL)...")
    model = build_feasible_model(data)
    
    print("Solving model...")
    outcome = solve_model(
        model,
        SolverConfig(solver_name='cbc', time_limit_seconds=10)
    )
    
    if not outcome.ok:
        print(f"Solve failed: {outcome.message}")
        return

    print("Parsing results (FULL MODEL)...")
    results = parse_results(model, plant_names=data.plant_names)
    
    print("Cost breakdown keys:", results.cost_breakdown.keys())
    print("Cost breakdown values:", results.cost_breakdown)
    
    print("Attempting to create cost DataFrame...")
    cost = results.cost_breakdown
    try:
        cost_df = pd.DataFrame([
            {"type": "production", "cost": float(cost.get("production", 0.0))},
            {"type": "transport", "cost": float(cost.get("transport", 0.0))},
            {"type": "holding", "cost": float(cost.get("holding", 0.0))},
            {"type": "demand_penalty", "cost": float(cost.get("demand_penalty", 0.0))},
        ])
        print("DataFrame created successfully:")
        print(cost_df)
    except Exception as e:
        print(f"CRASHED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    reproduce()
