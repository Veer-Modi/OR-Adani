"""
Test script for demand uncertainty analysis
"""

from simple_feasible_loader import load_simple_feasible_data
from demand_uncertainty_analysis import DemandUncertaintyAnalyzer

def test_demand_uncertainty():
    """Test the demand uncertainty analysis system."""
    
    print("🚀 TESTING DEMAND UNCERTAINTY ANALYSIS")
    print("=" * 50)
    
    try:
        # Load data
        print("📊 Loading base data...")
        base_data = load_simple_feasible_data('Dataset_Dummy_Clinker_3MPlan.xlsx', ['1'])
        print(f"✅ Data loaded: {len(base_data.plant_ids)} plants")
        
        # Initialize analyzer
        analyzer = DemandUncertaintyAnalyzer(base_data)
        
        # Generate scenarios
        print("🎲 Generating scenarios...")
        scenarios = analyzer.generate_demand_scenarios(num_scenarios=3, volatility=0.2)
        print(f"✅ Generated {len(scenarios)} scenarios")
        
        for s in scenarios:
            print(f"   {s.name}: {s.probability:.2%} prob, {s.demand_multiplier:.2f}x demand")
        
        # Run deterministic optimization
        print("\n🔧 Running deterministic optimization...")
        det_metrics = analyzer.run_deterministic_optimization()
        print(f"✅ Deterministic: ${det_metrics.total_cost:,.2f}, Service: {det_metrics.service_level:.2%}")
        
        # Run stochastic optimization
        print("\n🎲 Running stochastic optimization...")
        stoch_metrics = analyzer.run_stochastic_optimization()
        print(f"✅ Stochastic: ${stoch_metrics.total_cost:,.2f}, Service: {stoch_metrics.service_level:.2%}")
        
        # Compare
        comparison = analyzer.compare_performance()
        diffs = comparison['differences']
        
        print("\n📊 COMPARISON RESULTS:")
        print(f"Cost Change: {diffs['total_cost_pct']:+.2f}%")
        print(f"Service Level Change: {diffs['service_level_diff']:+.2%}")
        print(f"Penalty Change: {diffs['penalty_cost_diff']:+,.2f}")
        
        print("\n🎉 DEMAND UNCERTAINTY ANALYSIS WORKING!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_demand_uncertainty()
    
    if success:
        print("\n" + "=" * 50)
        print("✅ ALL TESTS PASSED!")
        print("\n💡 Ready to use in Streamlit:")
        print("   1. Run: streamlit run app.py")
        print("   2. Navigate to 'Demand Uncertainty Analysis'")
        print("   3. Configure scenarios and run analysis")
    else:
        print("\n" + "=" * 50)
        print("❌ TESTS FAILED")
        print("Please check the errors above")
