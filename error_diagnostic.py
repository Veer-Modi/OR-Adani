"""
Comprehensive error diagnostic tool for optimization issues.
"""

import sys
import os
import traceback

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_all_components():
    """Test all components of the optimization system."""
    
    print("🔍 COMPREHENSIVE ERROR DIAGNOSTIC")
    print("=" * 60)
    
    tests = []
    
    # Test 1: Basic imports
    print("\n🧪 Test 1: Basic Imports")
    try:
        import streamlit as st
        print("✅ Streamlit imported")
        tests.append(("Streamlit", True, None))
    except Exception as e:
        print(f"❌ Streamlit failed: {e}")
        tests.append(("Streamlit", False, str(e)))
    
    try:
        import pandas as pd
        print("✅ Pandas imported")
        tests.append(("Pandas", True, None))
    except Exception as e:
        print(f"❌ Pandas failed: {e}")
        tests.append(("Pandas", False, str(e)))
    
    try:
        import pyomo.environ as pyo
        print("✅ Pyomo imported")
        tests.append(("Pyomo", True, None))
    except Exception as e:
        print(f"❌ Pyomo failed: {e}")
        tests.append(("Pyomo", False, str(e)))
    
    # Test 2: Data loading
    print("\n🧪 Test 2: Data Loading")
    try:
        from simple_feasible_loader import load_simple_feasible_data
        data = load_simple_feasible_data('Dataset_Dummy_Clinker_3MPlan.xlsx', ['1'])
        print(f"✅ Data loaded: {len(data.plant_ids)} plants, {len(data.routes)} routes")
        tests.append(("Data Loading", True, None))
    except Exception as e:
        print(f"❌ Data loading failed: {e}")
        traceback.print_exc()
        tests.append(("Data Loading", False, str(e)))
    
    # Test 3: Model building
    print("\n🧪 Test 3: Model Building")
    try:
        from simple_feasible_model import build_simple_feasible_model
        if 'data' in locals():
            model = build_simple_feasible_model(data)
            print("✅ Model built successfully")
            tests.append(("Model Building", True, None))
    except Exception as e:
        print(f"❌ Model building failed: {e}")
        traceback.print_exc()
        tests.append(("Model Building", False, str(e)))
    
    # Test 4: Optimization solving
    print("\n🧪 Test 4: Optimization Solving")
    try:
        from backend.optimization.solver import SolverConfig, solve_model
        if 'model' in locals():
            outcome = solve_model(model, SolverConfig(solver_name='cbc', time_limit_seconds=30, mip_gap=0.01))
            if outcome.ok:
                print("✅ Optimization solved successfully")
                tests.append(("Optimization", True, None))
            else:
                print(f"❌ Optimization failed: {outcome.message}")
                tests.append(("Optimization", False, outcome.message))
    except Exception as e:
        print(f"❌ Optimization solving failed: {e}")
        traceback.print_exc()
        tests.append(("Optimization", False, str(e)))
    
    # Test 5: Streamlit app imports
    print("\n🧪 Test 5: Streamlit App Imports")
    try:
        from ui.optimization_run import render_optimization_run
        print("✅ Optimization run module imported")
        tests.append(("Streamlit App", True, None))
    except Exception as e:
        print(f"❌ Streamlit app import failed: {e}")
        traceback.print_exc()
        tests.append(("Streamlit App", False, str(e)))
    
    # Test 6: Excel file access
    print("\n🧪 Test 6: Excel File Access")
    try:
        import pandas as pd
        xl = pd.ExcelFile('Dataset_Dummy_Clinker_3MPlan.xlsx')
        print(f"✅ Excel file accessible with sheets: {xl.sheet_names}")
        tests.append(("Excel File", True, None))
    except Exception as e:
        print(f"❌ Excel file access failed: {e}")
        tests.append(("Excel File", False, str(e)))
    
    # Test 7: Solver availability
    print("\n🧪 Test 7: Solver Availability")
    try:
        import pulp
        solver = pulp.PULP_CBC_CMD(msg=False)
        print("✅ CBC solver available")
        tests.append(("CBC Solver", True, None))
    except Exception as e:
        print(f"❌ CBC solver failed: {e}")
        tests.append(("CBC Solver", False, str(e)))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 DIAGNOSTIC SUMMARY:")
    
    passed = sum(1 for _, success, _ in tests if success)
    total = len(tests)
    
    for name, success, error in tests:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {name}: {status}")
        if not success and error:
            print(f"      Error: {error}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! System is working correctly.")
        print("\n💡 If you're still seeing errors, please:")
        print("   1. Clear your browser cache")
        print("   2. Restart the Streamlit app")
        print("   3. Check browser console for JavaScript errors")
    else:
        print(f"\n⚠️  {total - passed} tests failed. See errors above.")
    
    return passed == total

def test_specific_error():
    """Test for specific common errors."""
    
    print("\n🔍 TESTING FOR SPECIFIC ERRORS")
    print("=" * 40)
    
    # Check for missing Excel file
    if not os.path.exists('Dataset_Dummy_Clinker_3MPlan.xlsx'):
        print("❌ Excel file not found: Dataset_Dummy_Clinker_3MPlan.xlsx")
        return False
    
    # Check for permission issues
    try:
        with open('Dataset_Dummy_Clinker_3MPlan.xlsx', 'rb') as f:
            f.read(100)
        print("✅ Excel file readable")
    except Exception as e:
        print(f"❌ Excel file permission error: {e}")
        return False
    
    # Check for memory issues
    try:
        import psutil
        memory = psutil.virtual_memory()
        print(f"✅ Available memory: {memory.available / (1024**3):.1f} GB")
        if memory.available < 1024**3:  # Less than 1GB
            print("⚠️  Low memory available")
    except ImportError:
        print("⚠️  Cannot check memory (psutil not installed)")
    
    return True

if __name__ == "__main__":
    print("🚀 STARTING ERROR DIAGNOSTIC")
    
    # Run comprehensive tests
    all_ok = test_all_components()
    
    # Run specific error tests
    specific_ok = test_specific_error()
    
    print("\n" + "=" * 60)
    if all_ok and specific_ok:
        print("🎊 SYSTEM IS HEALTHY!")
        print("\n📋 NEXT STEPS:")
        print("   1. Run: streamlit run app.py")
        print("   2. Open browser to localhost:8501")
        print("   3. Navigate to 'Run Optimization'")
        print("   4. If error persists, screenshot and share")
    else:
        print("❌ ISSUES FOUND - See above for details")
    
    print("\n📞 If you need further help, please share:")
    print("   - Screenshot of the error")
    print("   - Browser console errors (F12)")
    print("   - Terminal output")
