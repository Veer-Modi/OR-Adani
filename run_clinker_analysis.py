"""
Run demand uncertainty analysis for the clinker project and interpret results
"""

from simple_feasible_loader import load_simple_feasible_data
from demand_uncertainty_analysis import DemandUncertaintyAnalyzer

def run_clinker_analysis():
    """Run and interpret demand uncertainty analysis for clinker project."""
    
    print('🚀 DEMAND UNCERTAINTY ANALYSIS - CLINKER PROJECT')
    print('=' * 60)
    
    # Load data
    base_data = load_simple_feasible_data('Dataset_Dummy_Clinker_3MPlan.xlsx', ['1'])
    print(f'✅ Data loaded: {len(base_data.plant_ids)} plants, {len(base_data.routes)} routes')
    
    # Initialize analyzer
    analyzer = DemandUncertaintyAnalyzer(base_data)
    
    # Generate scenarios
    scenarios = analyzer.generate_demand_scenarios(num_scenarios=5, volatility=0.3)
    print(f'✅ Generated {len(scenarios)} scenarios')
    for s in scenarios:
        print(f'   {s.name}: {s.probability:.2%} prob, {s.demand_multiplier:.2f}x demand')
    
    # Run deterministic optimization
    print('\n🔧 Running deterministic optimization...')
    det_metrics = analyzer.run_deterministic_optimization()
    print(f'✅ Deterministic: ${det_metrics.total_cost:,.2f}, Service: {det_metrics.service_level:.2%}')
    
    # Run stochastic optimization
    print('\n🎲 Running stochastic optimization...')
    stoch_metrics = analyzer.run_stochastic_optimization()
    print(f'✅ Stochastic: ${stoch_metrics.total_cost:,.2f}, Service: {stoch_metrics.service_level:.2%}')
    
    # Get comparison
    comparison = analyzer.compare_performance()
    diffs = comparison['differences']
    
    print('\n📊 KEY RESULTS FOR YOUR CLINKER PROJECT:')
    print('=' * 50)
    print(f'💰 Cost Impact: {diffs["total_cost_pct"]:+.2f}% (${diffs["total_cost_diff"]:,.0f})')
    print(f'🎯 Service Level: {det_metrics.service_level:.2%} → {stoch_metrics.service_level:.2%} ({diffs["service_level_diff"]:+.2%})')
    print(f'⚠️  Unmet Demand: {det_metrics.unmet_demand:,.0f} → {stoch_metrics.unmet_demand:,.0f} units')
    print(f'🏭 Facility Utilization: {det_metrics.facility_utilization:.2%} → {stoch_metrics.facility_utilization:.2%}')
    print(f'💸 Demand Penalty: ${det_metrics.demand_penalty:,.0f} → ${stoch_metrics.demand_penalty:,.0f}')
    
    print('\n🎯 BUSINESS INSIGHTS:')
    print('=' * 30)
    if diffs['total_cost_pct'] > 0:
        print(f'💰 Uncertainty planning costs {diffs["total_cost_pct"]:.2f}% more')
        print('   This is the "insurance premium" for better risk management')
    else:
        print(f'💰 Uncertainty planning saves {abs(diffs["total_cost_pct"]):.2f}%')
    
    if diffs['service_level_diff'] > 0:
        print(f'🎯 Service level improves by {diffs["service_level_diff"]:.2%}')
        print('   Better customer satisfaction with uncertainty planning')
    else:
        print(f'⚠️  Service level changes by {diffs["service_level_diff"]:.2%}')
        print('   Service impact is minimal')
    
    if diffs['penalty_cost_diff'] < 0:
        print(f'💸 Stockout costs reduced by ${abs(diffs["penalty_cost_diff"]):,.0f}')
        print('   Better preparation reduces emergency costs')
    else:
        print(f'💸 Stockout costs increase by ${diffs["penalty_cost_diff"]:,.0f}')
        print('   Higher cost for uncertainty protection')
    
    print('\n🚀 RECOMMENDATIONS:')
    print('=' * 25)
    if diffs['total_cost_pct'] < 2.0:
        print('✅ Low cost increase for uncertainty protection - RECOMMENDED')
    else:
        print('⚠️  Higher cost increase - evaluate risk tolerance')
    
    if abs(diffs['service_level_diff']) < 0.05:
        print('🎯 Service level impact minimal - good for risk management')
    else:
        print('🎯 Significant service impact - consider uncertainty planning')
    
    if diffs['penalty_cost_diff'] < 0:
        print('💸 Reduced stockout costs - strong business case')
    else:
        print('💸 Higher preparation costs - weigh against stockout risks')
    
    # Capacity insights
    print('\n🏭 CAPACITY INVESTMENT INSIGHTS:')
    print('=' * 35)
    if stoch_metrics.facility_utilization > 0.9:
        print('⚠️  High facility utilization - consider capacity expansion')
        print('   Current utilization: {:.1%}'.format(stoch_metrics.facility_utilization))
    elif stoch_metrics.facility_utilization > 0.8:
        print('👀 Moderate utilization - monitor for expansion needs')
        print('   Current utilization: {:.1%}'.format(stoch_metrics.facility_utilization))
    else:
        print('✅ Adequate capacity - no immediate expansion needed')
        print('   Current utilization: {:.1%}'.format(stoch_metrics.facility_utilization))
    
    # Inventory insights
    print('\n📦 INVENTORY STRATEGY INSIGHTS:')
    print('=' * 35)
    if diffs['penalty_cost_diff'] > 0:
        print('💰 Higher safety stock costs for uncertainty protection')
        print('   Consider: buffer inventory at critical locations')
    else:
        print('💸 Lower stockout costs with uncertainty planning')
        print('   Current strategy appears effective')
    
    # Transport insights
    print('\n🚚 TRANSPORT PLANNING INSIGHTS:')
    print('=' * 35)
    transport_ratio = stoch_metrics.total_shipment / stoch_metrics.total_production if stoch_metrics.total_production > 0 else 0
    print(f'📊 Transport efficiency: {transport_ratio:.1%} of production shipped')
    if transport_ratio < 0.9:
        print('⚠️  Some production not shipped - check inventory buildup')
    else:
        print('✅ Good transport flow - most production reaching customers')
    
    print('\n🎉 ANALYSIS COMPLETE!')
    print('\n💡 Next Steps:')
    print('1. Review these insights with your team')
    print('2. Use Streamlit UI for deeper analysis')
    print('3. Consider scenario-based planning for critical decisions')
    
    return comparison

if __name__ == "__main__":
    run_clinker_analysis()
