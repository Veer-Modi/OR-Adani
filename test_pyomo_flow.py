
import pandas as pd
from simple_feasible_loader import load_simple_feasible_data
from simple_feasible_model import build_simple_feasible_model
from simple_result_parser import parse_simple_results
from backend.optimization.solver import solve_model, SolverConfig

def test_pyomo_flow():
    print("Loading data (Simple Feasible)...")
    try:
        data = load_simple_feasible_data(
            file_path="Dataset_Dummy_Clinker_3MPlan.xlsx",
            selected_months=['Jan-2024']
        )
        print(f"Data loaded. Plans: {len(data.plant_ids)}")
    except Exception as e:
        print(f"Data load failed: {e}")
        return

    print("Building model (Simple Feasible Pyomo)...")
    try:
        model = build_simple_feasible_model(data)
    except Exception as e:
        print(f"Model build failed: {e}")
        return
    
    print("Solving model (CBC -> Fallback)...")
    outcome = solve_model(
        model,
        SolverConfig(solver_name='cbc', time_limit_seconds=30)
    )
    
    print(f"Solve Outcome: ok={outcome.ok}, message={outcome.message}")
    print(f"Solver used: {outcome.solver_used}")
    print(f"Termination condition: {outcome.termination_condition}")

    if not outcome.ok:
        print("Optimization failed to return ok status.")
        return

    print("Parsing results...")
    results = parse_simple_results(model, plant_names=data.plant_names)
    
    print(f"Objective Value: {results.objective_value}")
    print(f"Production DF: {len(results.production_df)} rows")
    if not results.production_df.empty:
        print(results.production_df.head())
    else:
        print("PRODUCTION DF IS EMPTY!")

    print(f"Transport DF: {len(results.transport_df)} rows")
    
if __name__ == "__main__":
    test_pyomo_flow()
