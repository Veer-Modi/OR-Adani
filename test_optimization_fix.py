"""
Test script to verify optimization fixes are working.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_simple_optimization():
    """Test the simple feasible optimization."""
    print("🧪 Testing Simple Feasible Optimization...")
    
    try:
        from simple_feasible_loader import load_simple_feasible_data
        from simple_feasible_model import build_simple_feasible_model
        from backend.optimization.solver import SolverConfig, solve_model
        
        # Load data
        data = load_simple_feasible_data('Dataset_Dummy_Clinker_3MPlan.xlsx', ['1'])
        print(f"✅ Data loaded: {len(data.plant_ids)} plants, {len(data.routes)} routes")
        
        # Build model
        model = build_simple_feasible_model(data)
        print("✅ Model built successfully")
        
        # Solve model
        outcome = solve_model(model, SolverConfig(solver_name='cbc', time_limit_seconds=30, mip_gap=0.01))
        
        if outcome.ok:
            print(f"✅ Optimization SUCCESS: {outcome.termination_condition}")
            print(f"   Objective value: {getattr(outcome, 'objective_value', 'N/A')}")
            return True
        else:
            print(f"❌ Optimization FAILED: {outcome.message}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_streamlit_imports():
    """Test Streamlit app imports."""
    print("\n🧪 Testing Streamlit App Imports...")
    
    try:
        import streamlit as st
        print("✅ Streamlit imported")
        
        from ui.optimization_run import render_optimization_run
        print("✅ Optimization run module imported")
        
        from simple_feasible_loader import load_simple_feasible_data
        from simple_feasible_model import build_simple_feasible_model
        print("✅ Simple feasible modules imported")
        
        return True
        
    except Exception as e:
        print(f"❌ Import ERROR: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 TESTING OPTIMIZATION FIXES")
    print("=" * 50)
    
    # Test imports
    imports_ok = test_streamlit_imports()
    
    # Test optimization
    optimization_ok = test_simple_optimization()
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    print(f"   Imports: {'✅ PASS' if imports_ok else '❌ FAIL'}")
    print(f"   Optimization: {'✅ PASS' if optimization_ok else '❌ FAIL'}")
    
    if imports_ok and optimization_ok:
        print("\n🎉 ALL TESTS PASSED! Optimization is ready!")
        print("\n📋 NEXT STEPS:")
        print("   1. Run: streamlit run app.py")
        print("   2. Navigate to 'Run Optimization' page")
        print("   3. Select months and click 'Run Optimization'")
        print("   4. View successful results!")
    else:
        print("\n❌ Some tests failed. Check the errors above.")
    
    return imports_ok and optimization_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
