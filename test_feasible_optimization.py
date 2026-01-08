"""
Simple test for feasible optimization without full backend dependencies.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from feasible_optimization import FeasibleClinkerOptimization
    
    print("Testing feasible optimization...")
    
    # Create and test the feasible optimization
    model = FeasibleClinkerOptimization('Dataset_Dummy_Clinker_3MPlan.xlsx')
    
    # Create feasible data
    model.create_feasible_data()
    
    # Build and solve model
    model.build_feasible_model()
    status = model.solve_model()
    
    if status == 'Optimal':
        print("✅ Feasible optimization test PASSED!")
        print(f"Total cost: ${model.results['objective_value']:,.2f}")
        print(f"Active production plans: {len(model.results['production'])}")
        print(f"Unmet demand: {sum(model.results['unmet_demand'].values()):,.0f} units")
    else:
        print(f"❌ Feasible optimization test FAILED: {status}")
        
except Exception as e:
    print(f"❌ Error in feasible optimization test: {e}")
    import traceback
    traceback.print_exc()
