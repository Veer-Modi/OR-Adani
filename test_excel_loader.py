"""Test script to verify Excel loader works correctly."""

import sys
import os

# Add CBC to PATH
_cbc_path = r"C:\solvers\cbc\bin"
if os.path.exists(_cbc_path):
    current_path = os.environ.get("PATH", "")
    if _cbc_path not in current_path:
        os.environ["PATH"] = _cbc_path + os.pathsep + current_path

try:
    import pyomo.environ as pyo
    from backend.optimization.excel_loader import load_excel_data
    from backend.optimization.model import build_model
    from backend.optimization.solver import SolverConfig, solve_model
    
    print("=" * 80)
    print("TESTING EXCEL DATA LOADER")
    print("=" * 80)
    
    excel_file = "Dataset_Dummy_Clinker_3MPlan.xlsx"
    
    if not os.path.exists(excel_file):
        print(f"ERROR: Excel file not found: {excel_file}")
        sys.exit(1)
    
    print(f"\nLoading data from: {excel_file}")
    print("Time periods: [1, 2, 3]")
    
    # Load data
    data = load_excel_data(excel_file, selected_months=['1', '2', '3'])
    
    print("\n[SUCCESS] Data loaded successfully!")
    print(f"  - Plants: {len(data.plant_ids)}")
    print(f"  - Clinker plants: {len(data.clinker_plants)}")
    print(f"  - Routes: {len(data.routes)}")
    print(f"  - Time periods: {len(data.months)}")
    print(f"  - Demand entries: {len(data.demand)}")
    
    if hasattr(data, 'min_fulfillment'):
        print(f"  - Min fulfillment constraints: {len(data.min_fulfillment)}")
    if hasattr(data, 'min_closing_stock'):
        print(f"  - Min closing stock constraints: {len(data.min_closing_stock)}")
    if hasattr(data, 'transport_code_limits'):
        print(f"  - Transport code limits: {len(data.transport_code_limits)}")
    if hasattr(data, 'transport_bounds'):
        print(f"  - Transport bounds: {len(data.transport_bounds)}")
    
    print("\nBuilding optimization model...")
    model = build_model(data)
    
    print("[SUCCESS] Model built successfully!")
    var_count = sum(1 for _ in model.component_objects(pyo.Var))
    con_count = sum(1 for _ in model.component_objects(pyo.Constraint))
    param_count = sum(1 for _ in model.component_objects(pyo.Param))
    print(f"  - Variables: {var_count}")
    print(f"  - Constraints: {con_count}")
    print(f"  - Parameters: {param_count}")
    
    print("\nSolving optimization...")
    outcome = solve_model(model, SolverConfig(solver_name="cbc", time_limit_seconds=60))
    
    if outcome.ok:
        print("[SUCCESS] Optimization solved!")
        print(f"  - Status: {outcome.termination_condition}")
        print(f"  - Solver used: {outcome.solver_used}")
        print(f"  - Runtime: {outcome.runtime_seconds:.2f} seconds")
    else:
        print("[ERROR] Optimization failed!")
        print(f"  - Message: {outcome.message}")
        print(f"  - Status: {outcome.termination_condition}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    
except ImportError as e:
    print(f"ERROR: Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
