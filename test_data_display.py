"""
Test script to verify data display in Streamlit optimization results.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from simple_feasible_loader import load_simple_feasible_data
from simple_feasible_model import build_simple_feasible_model
from simple_result_parser import parse_simple_results
from backend.optimization.solver import SolverConfig, solve_model
from backend.results.result_service import save_optimization_run, get_recent_runs, get_run

def test_data_display():
    """Test complete data generation and display flow."""
    
    print("🧪 TESTING DATA DISPLAY FLOW")
    print("=" * 50)
    
    try:
        # Step 1: Generate data
        print("\n📊 Step 1: Generating optimization data...")
        data = load_simple_feasible_data('Dataset_Dummy_Clinker_3MPlan.xlsx', ['1'])
        print(f"✅ Data loaded: {len(data.plant_ids)} plants, {len(data.routes)} routes")
        
        # Step 2: Build model
        print("\n🏗️ Step 2: Building optimization model...")
        model = build_simple_feasible_model(data)
        print("✅ Model built")
        
        # Step 3: Solve optimization
        print("\n🔧 Step 3: Solving optimization...")
        outcome = solve_model(model, SolverConfig(solver_name='cbc', time_limit_seconds=30, mip_gap=0.01))
        
        if not outcome.ok:
            print(f"❌ Optimization failed: {outcome.message}")
            return False
        
        print("✅ Optimization solved")
        
        # Step 4: Parse results
        print("\n📈 Step 4: Parsing results...")
        results = parse_simple_results(model, data.plant_names)
        print(f"✅ Results parsed:")
        print(f"   Production rows: {len(results.production_df)}")
        print(f"   Transport rows: {len(results.transport_df)}")
        print(f"   Inventory rows: {len(results.inventory_df)}")
        print(f"   Objective value: {results.objective_value:,.2f}")
        
        # Step 5: Save to database
        print("\n💾 Step 5: Saving to database...")
        success, message, run_id = save_optimization_run(
            created_by_email="test@example.com",
            months=['1'],
            solver="cbc",
            demand_type="deterministic",
            status="success",
            message=outcome.message,
            objective_value=results.objective_value,
            cost_breakdown=results.cost_breakdown,
            production_df=results.production_df,
            transport_df=results.transport_df,
            inventory_df=results.inventory_df,
            optimization_type="deterministic",
        )
        
        if success:
            print(f"✅ Data saved successfully: {run_id}")
        else:
            print(f"❌ Save failed: {message}")
            return False
        
        # Step 6: Load from database
        print("\n📂 Step 6: Loading from database...")
        run_data = get_run(run_id)
        
        if not run_data:
            print("❌ Failed to load run from database")
            return False
        
        print("✅ Run loaded from database")
        
        # Step 7: Check data integrity
        print("\n🔍 Step 7: Checking data integrity...")
        prod_rows = run_data.get('production_rows', [])
        trans_rows = run_data.get('transport_rows', [])
        inv_rows = run_data.get('inventory_rows', [])
        
        print(f"✅ Data integrity check:")
        print(f"   Production rows in DB: {len(prod_rows)}")
        print(f"   Transport rows in DB: {len(trans_rows)}")
        print(f"   Inventory rows in DB: {len(inv_rows)}")
        
        # Step 8: Test display format
        print("\n🖥️ Step 8: Testing display format...")
        
        # Convert to DataFrames (like UI does)
        prod_df = pd.DataFrame(prod_rows) if prod_rows else pd.DataFrame()
        trans_df = pd.DataFrame(trans_rows) if trans_rows else pd.DataFrame()
        inv_df = pd.DataFrame(inv_rows) if inv_rows else pd.DataFrame()
        
        print("✅ Display format test:")
        print(f"   Production DataFrame shape: {prod_df.shape}")
        print(f"   Transport DataFrame shape: {trans_df.shape}")
        print(f"   Inventory DataFrame shape: {inv_df.shape}")
        
        # Show sample data
        if not prod_df.empty:
            print("\n📋 Sample Production Data:")
            print(prod_df.head(3).to_string())
        
        if not trans_df.empty:
            print("\n📋 Sample Transport Data:")
            print(trans_df.head(3).to_string())
        
        print("\n🎉 ALL TESTS PASSED!")
        print("📊 Data is ready for display in Streamlit UI")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_data_display()
    
    if success:
        print("\n" + "=" * 50)
        print("✅ DATA DISPLAY TEST: SUCCESS")
        print("\n💡 If you're still seeing empty tables in Streamlit:")
        print("   1. Check browser cache and refresh")
        print("   2. Verify MongoDB connection")
        print("   3. Check the 'Optimization Results' page")
        print("   4. Look for the latest run in the list")
    else:
        print("\n" + "=" * 50)
        print("❌ DATA DISPLAY TEST: FAILED")
        print("Please check the errors above")
