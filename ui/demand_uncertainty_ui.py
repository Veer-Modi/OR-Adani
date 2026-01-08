"""
Demand Uncertainty Analysis UI for Streamlit

This module provides an interactive interface for analyzing demand uncertainty
impact on optimization performance.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, Any

from backend.middleware.role_guard import require_authentication, require_role
from demand_uncertainty_analysis import DemandUncertaintyAnalyzer, run_complete_analysis


def render_demand_uncertainty_analysis():
    """Render the demand uncertainty analysis page."""
    
    if not require_authentication():
        return
    
    if not require_role(["Admin", "Planner"]):
        return
    
    st.title("🎲 Demand Uncertainty Analysis")
    st.markdown("""
    Compare how cost and customer service performance change when demand is unpredictable 
    versus when demand is known in advance.
    """)
    
    # Initialize session state
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = None
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    
    # Sidebar configuration
    st.sidebar.header("⚙️ Analysis Configuration")
    
    # Scenario settings
    st.sidebar.subheader("🎲 Demand Scenarios")
    num_scenarios = st.sidebar.slider("Number of Scenarios", 3, 10, 5)
    volatility = st.sidebar.slider("Demand Volatility", 0.1, 0.5, 0.3, 0.05)
    
    # Analysis options
    st.sidebar.subheader("📊 Analysis Options")
    run_deterministic = st.sidebar.checkbox("Run Deterministic Analysis", True)
    run_stochastic = st.sidebar.checkbox("Run Stochastic Analysis", True)
    generate_plots = st.sidebar.checkbox("Generate Visualizations", True)
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📋 Analysis Overview")
        st.markdown("""
        This analysis helps you understand:
        
        - **Cost Impact**: How uncertainty affects total costs
        - **Service Level**: Customer service performance under uncertainty
        - **Risk Management**: Benefits of stochastic optimization
        - **Strategic Decisions**: When to use which approach
        """)
    
    with col2:
        st.subheader("🎯 Key Metrics")
        if st.session_state.analysis_results:
            comparison = st.session_state.analysis_results['comparison']
            diffs = comparison['differences']
            
            st.metric("Cost Impact", f"{diffs['total_cost_pct']:+.2f}%")
            st.metric("Service Level Change", f"{diffs['service_level_diff']:+.2%}")
            st.metric("Penalty Change", f"{diffs['penalty_cost_diff']:,.0f}")
        else:
            st.info("Run analysis to see metrics")
    
    # Run analysis button
    if st.button("🚀 Run Demand Uncertainty Analysis", type="primary"):
        # Use settings from uncertainty settings page if available
        if 'uncertainty_settings' in st.session_state:
            settings = st.session_state.uncertainty_settings
            if settings.get('is_enabled', True):
                num_scenarios = settings.get('num_scenarios', num_scenarios)
                volatility = settings.get('volatility', volatility)
                st.info(f"Using settings from Demand Uncertainty Settings: {num_scenarios} scenarios, {volatility:.1%} volatility")
        
        run_analysis(num_scenarios, volatility, run_deterministic, run_stochastic, generate_plots)
    
    # Display results if available
    if st.session_state.analysis_results:
        display_analysis_results()
    
    # Scenario configuration section
    st.divider()
    st.subheader("🎲 Scenario Configuration")
    display_scenario_configuration(volatility)


def run_analysis(num_scenarios: int, volatility: float, run_det: bool, run_stoch: bool, generate_plots: bool):
    """Run the demand uncertainty analysis."""
    
    with st.spinner("🔄 Running demand uncertainty analysis..."):
        try:
            # Load base data
            from simple_feasible_loader import load_simple_feasible_data
            base_data = load_simple_feasible_data("Dataset_Dummy_Clinker_3MPlan.xlsx", ['1'])
            
            # Initialize analyzer
            analyzer = DemandUncertaintyAnalyzer(base_data)
            
            # Generate scenarios
            scenarios = analyzer.generate_demand_scenarios(num_scenarios, volatility)
            st.info(f"✅ Generated {len(scenarios)} scenarios with {volatility:.1%} volatility")
            
            # Run optimizations
            if run_det:
                with st.spinner("🔧 Running deterministic optimization..."):
                    det_metrics = analyzer.run_deterministic_optimization()
                    st.success(f"✅ Deterministic: ${det_metrics.total_cost:,.0f}, Service: {det_metrics.service_level:.1%}")
            
            if run_stoch:
                with st.spinner("🎲 Running stochastic optimization..."):
                    stoch_metrics = analyzer.run_stochastic_optimization()
                    st.success(f"✅ Stochastic: ${stoch_metrics.total_cost:,.0f}, Service: {stoch_metrics.service_level:.1%}")
            
            # Get comparison
            comparison = analyzer.compare_performance()
            
            # Generate plots (with error handling)
            plots = {}
            if generate_plots:
                try:
                    plots = analyzer.create_comparison_plots()
                    st.success("✅ Plots generated successfully")
                except Exception as plot_error:
                    st.warning(f"⚠️ Plot generation failed: {str(plot_error)}")
                    st.info("Analysis completed successfully, but plots could not be generated.")
            
            # Generate report
            try:
                report = analyzer.generate_report()
            except Exception as report_error:
                st.warning(f"⚠️ Report generation failed: {str(report_error)}")
                report = "Report generation failed"
            
            # Store in session state
            st.session_state.analyzer = analyzer
            st.session_state.analysis_results = {
                'analyzer': analyzer,
                'comparison': comparison,
                'plots': plots,
                'report': report,
                'scenarios': scenarios
            }
            
            st.success("🎉 Analysis completed successfully!")
            
        except Exception as e:
            st.error(f"❌ Analysis failed: {str(e)}")
            st.exception(e)
            return False
    
    return True


def display_analysis_results():
    """Display the analysis results."""
    
    results = st.session_state.analysis_results
    comparison = results['comparison']
    plots = results['plots']
    scenarios = results['scenarios']
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Summary", "💰 Cost Analysis", "🎯 Performance", "📈 Visualizations"])
    
    with tab1:
        display_summary_view(comparison, scenarios)
    
    with tab2:
        display_cost_analysis(comparison, plots)
    
    with tab3:
        display_performance_analysis(comparison, plots)
    
    with tab4:
        display_visualizations(plots)


def display_summary_view(comparison: Dict, scenarios: list):
    """Display summary view of the analysis."""
    
    st.subheader("📊 Executive Summary")
    
    det = comparison['deterministic']
    stoch = comparison['stochastic']
    diffs = comparison['differences']
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Cost Impact",
            f"{diffs['total_cost_pct']:+.2f}%",
            f"${diffs['total_cost_diff']:,.0f}"
        )
    
    with col2:
        st.metric(
            "Service Level",
            f"{stoch.service_level:.2%}",
            f"{diffs['service_level_diff']:+.2%}"
        )
    
    with col3:
        st.metric(
            "Demand Penalty",
            f"${stoch.demand_penalty:,.0f}",
            f"{diffs['penalty_cost_diff']:+.0f}"
        )
    
    with col4:
        st.metric(
            "Facility Utilization",
            f"{stoch.facility_utilization:.2%}",
            f"{diffs['utilization_diff']:+.2%}"
        )
    
    # Comparison table
    st.subheader("📋 Detailed Comparison")
    
    comparison_data = {
        'Metric': ['Total Cost', 'Production Cost', 'Transport Cost', 'Holding Cost', 
                  'Demand Penalty', 'Service Level', 'Unmet Demand', 'Facility Utilization'],
        'Deterministic': [
            f"${det.total_cost:,.0f}",
            f"${det.production_cost:,.0f}",
            f"${det.transport_cost:,.0f}",
            f"${det.holding_cost:,.0f}",
            f"${det.demand_penalty:,.0f}",
            f"{det.service_level:.2%}",
            f"{det.unmet_demand:,.0f}",
            f"{det.facility_utilization:.2%}"
        ],
        'Stochastic': [
            f"${stoch.total_cost:,.0f}",
            f"${stoch.production_cost:,.0f}",
            f"${stoch.transport_cost:,.0f}",
            f"${stoch.holding_cost:,.0f}",
            f"${stoch.demand_penalty:,.0f}",
            f"{stoch.service_level:.2%}",
            f"{stoch.unmet_demand:,.0f}",
            f"{stoch.facility_utilization:.2%}"
        ],
        'Difference': [
            f"{diffs['total_cost_pct']:+.2f}%",
            f"${diffs['production_cost_diff']:+,.0f}",
            f"${diffs['transport_cost_diff']:+,.0f}",
            f"${diffs['holding_cost_diff']:+,.0f}",
            f"${diffs['penalty_cost_diff']:+,.0f}",
            f"{diffs['service_level_diff']:+.2%}",
            f"{diffs['unmet_demand_diff']:+,.0f}",
            f"{diffs['utilization_diff']:+.2%}"
        ]
    }
    
    df_comparison = pd.DataFrame(comparison_data)
    st.dataframe(df_comparison, use_container_width=True, hide_index=True)
    
    # Scenarios table
    st.subheader("🎲 Demand Scenarios")
    
    scenario_data = {
        'Scenario': [s.name for s in scenarios],
        'Probability': [f"{s.probability:.2%}" for s in scenarios],
        'Demand Multiplier': [f"{s.demand_multiplier:.2f}x" for s in scenarios],
        'Description': [s.description for s in scenarios]
    }
    
    df_scenarios = pd.DataFrame(scenario_data)
    st.dataframe(df_scenarios, use_container_width=True, hide_index=True)
    
    # Insights
    st.subheader("💡 Key Insights")
    
    insights = []
    
    if diffs['total_cost_pct'] > 0:
        insights.append("💰 **Higher Cost**: Stochastic optimization costs more but provides better service")
    else:
        insights.append("💰 **Lower Cost**: Stochastic optimization is more cost-effective")
    
    if diffs['service_level_diff'] > 0:
        insights.append("🎯 **Better Service**: Stochastic approach improves customer service level")
    else:
        insights.append("⚠️ **Service Impact**: Service level changes under uncertainty")
    
    if diffs['penalty_cost_diff'] < 0:
        insights.append("📉 **Lower Penalties**: Reduced stockout costs with stochastic planning")
    else:
        insights.append("📈 **Higher Penalties**: Increased uncertainty costs")
    
    if abs(diffs['utilization_diff']) > 0.05:
        insights.append("🏭 **Utilization Change**: Facility utilization significantly affected")
    
    for insight in insights:
        st.markdown(f"- {insight}")


def display_cost_analysis(comparison: Dict, plots: Dict):
    """Display detailed cost analysis."""
    
    st.subheader("💰 Cost Analysis")
    
    det = comparison['deterministic']
    stoch = comparison['stochastic']
    diffs = comparison['differences']
    
    # Cost breakdown chart
    if 'cost_comparison' in plots:
        st.plotly_chart(plots['cost_comparison'], use_container_width=True)
    
    # Cost analysis metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Cost Components")
        
        cost_data = {
            'Component': ['Production', 'Transport', 'Holding', 'Demand Penalty'],
            'Deterministic': [det.production_cost, det.transport_cost, det.holding_cost, det.demand_penalty],
            'Stochastic': [stoch.production_cost, stoch.transport_cost, stoch.holding_cost, stoch.demand_penalty],
            'Difference': [diffs['production_cost_diff'], diffs['transport_cost_diff'], 
                          diffs['holding_cost_diff'], diffs['penalty_cost_diff']]
        }
        
        df_cost = pd.DataFrame(cost_data)
        st.dataframe(df_cost, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("📈 Cost Impact Analysis")
        
        # Calculate cost percentages
        total_det = det.total_cost
        total_stoch = stoch.total_cost
        
        cost_impact = {
            'Metric': ['Total Cost', 'Cost per Unit Demand', 'Cost per Unit Production', 
                      'Penalty as % of Total Cost'],
            'Deterministic': [
                f"${total_det:,.0f}",
                f"${total_det/det.total_demand:,.2f}" if det.total_demand > 0 else "N/A",
                f"${total_det/det.total_production:,.2f}" if det.total_production > 0 else "N/A",
                f"{(det.demand_penalty/total_det)*100:.2f}%"
            ],
            'Stochastic': [
                f"${total_stoch:,.0f}",
                f"${total_stoch/stoch.total_demand:,.2f}" if stoch.total_demand > 0 else "N/A",
                f"${total_stoch/stoch.total_production:,.2f}" if stoch.total_production > 0 else "N/A",
                f"{(stoch.demand_penalty/total_stoch)*100:.2f}%"
            ]
        }
        
        df_impact = pd.DataFrame(cost_impact)
        st.dataframe(df_impact, use_container_width=True, hide_index=True)
    
    # Cost recommendations
    st.subheader("💡 Cost Optimization Recommendations")
    
    recommendations = []
    
    if diffs['penalty_cost_diff'] < 0:
        recommendations.append("✅ **Lower Stockout Costs**: Stochastic planning reduces demand penalties")
    
    if diffs['holding_cost_diff'] > 0:
        recommendations.append("📦 **Higher Inventory**: Consider safety stock optimization")
    
    if diffs['transport_cost_diff'] > 0:
        recommendations.append("🚚 **Transport Efficiency**: Explore route optimization")
    
    if diffs['production_cost_diff'] > 0:
        recommendations.append("🏭 **Production Planning**: Consider capacity adjustments")
    
    for rec in recommendations:
        st.markdown(f"- {rec}")


def display_performance_analysis(comparison: Dict, plots: Dict):
    """Display performance analysis."""
    
    st.subheader("🎯 Performance Analysis")
    
    det = comparison['deterministic']
    stoch = comparison['stochastic']
    diffs = comparison['differences']
    
    # Performance charts
    if 'performance_comparison' in plots:
        st.plotly_chart(plots['performance_comparison'], use_container_width=True)
    
    # Performance metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Service Metrics")
        
        service_data = {
            'Metric': ['Service Level', 'Unmet Demand', 'Total Demand Satisfied', 
                      'Demand Fulfillment Rate'],
            'Deterministic': [
                f"{det.service_level:.2%}",
                f"{det.unmet_demand:,.0f}",
                f"{det.total_demand - det.unmet_demand:,.0f}",
                f"{((det.total_demand - det.unmet_demand)/det.total_demand)*100:.2f}%" if det.total_demand > 0 else "N/A"
            ],
            'Stochastic': [
                f"{stoch.service_level:.2%}",
                f"{stoch.unmet_demand:,.0f}",
                f"{stoch.total_demand - stoch.unmet_demand:,.0f}",
                f"{((stoch.total_demand - stoch.unmet_demand)/stoch.total_demand)*100:.2f}%" if stoch.total_demand > 0 else "N/A"
            ],
            'Improvement': [
                f"{diffs['service_level_diff']:+.2%}",
                f"{diffs['unmet_demand_diff']:+,.0f}",
                f"{(stoch.total_demand - stoch.unmet_demand) - (det.total_demand - det.unmet_demand):+,.0f}",
                f"{diffs['service_level_diff']:+.2%}"
            ]
        }
        
        df_service = pd.DataFrame(service_data)
        st.dataframe(df_service, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("🏭 Operational Metrics")
        
        operational_data = {
            'Metric': ['Facility Utilization', 'Total Production', 'Total Shipment', 
                      'Production Efficiency'],
            'Deterministic': [
                f"{det.facility_utilization:.2%}",
                f"{det.total_production:,.0f}",
                f"{det.total_shipment:,.0f}",
                f"{(det.total_shipment/det.total_production)*100:.2f}%" if det.total_production > 0 else "N/A"
            ],
            'Stochastic': [
                f"{stoch.facility_utilization:.2%}",
                f"{stoch.total_production:,.0f}",
                f"{stoch.total_shipment:,.0f}",
                f"{(stoch.total_shipment/stoch.total_production)*100:.2f}%" if stoch.total_production > 0 else "N/A"
            ],
            'Change': [
                f"{diffs['utilization_diff']:+.2%}",
                f"{stoch.total_production - det.total_production:+,.0f}",
                f"{stoch.total_shipment - det.total_shipment:+,.0f}",
                f"{((stoch.total_shipment/stoch.total_production) - (det.total_shipment/det.total_production))*100:+.2f}%" if det.total_production > 0 and stoch.total_production > 0 else "N/A"
            ]
        }
        
        df_operational = pd.DataFrame(operational_data)
        st.dataframe(df_operational, use_container_width=True, hide_index=True)
    
    # Performance recommendations
    st.subheader("💡 Performance Improvement Recommendations")
    
    perf_recommendations = []
    
    if diffs['service_level_diff'] > 0.01:
        perf_recommendations.append("🎯 **Service Improvement**: Stochastic planning significantly improves customer service")
    
    if diffs['utilization_diff'] > 0.05:
        perf_recommendations.append("🏭 **Capacity Planning**: Consider facility expansion or better utilization")
    
    if diffs['unmet_demand_diff'] < 0:
        perf_recommendations.append("📦 **Demand Fulfillment**: Better demand satisfaction with uncertainty planning")
    
    if abs(diffs['utilization_diff']) < 0.02:
        perf_recommendations.append("⚖️ **Balanced Approach**: Similar utilization with better service")
    
    for rec in perf_recommendations:
        st.markdown(f"- {rec}")


def display_visualizations(plots: Dict):
    """Display visualization plots."""
    
    st.subheader("📈 Analysis Visualizations")
    
    if not plots:
        st.info("No plots available. Run analysis with 'Generate Visualizations' enabled.")
        return
    
    # Display each plot
    for plot_name, fig in plots.items():
        st.subheader(f"📊 {plot_name.replace('_', ' ').title()}")
        st.plotly_chart(fig, use_container_width=True)
        
        # Add interpretation
        if plot_name == 'cost_comparison':
            st.markdown("""
            **Interpretation**: This chart shows how costs differ between deterministic and stochastic approaches.
            The stochastic approach typically has higher costs but provides better service under uncertainty.
            """)
        elif plot_name == 'performance_comparison':
            st.markdown("""
            **Interpretation**: This chart compares key performance metrics between approaches.
            Look for improvements in service level and reductions in unmet demand.
            """)
        elif plot_name == 'scenario_analysis':
            st.markdown("""
            **Interpretation**: This shows the demand scenarios used in the stochastic analysis.
            Higher probability scenarios have more influence on the expected results.
            """)


def display_scenario_configuration(volatility: float):
    """Display scenario configuration interface."""
    
    st.markdown(f"""
    **Current Volatility Setting**: {volatility:.1%}
    
    This setting controls how much demand can vary across scenarios:
    - **Low Volatility (10-20%)**: Relatively predictable demand
    - **Medium Volatility (20-30%)**: Moderate uncertainty
    - **High Volatility (30-50%)**: Highly unpredictable demand
    """)
    
    # Scenario preview
    if st.checkbox("🔍 Preview Scenarios"):
        with st.spinner("Generating scenario preview..."):
            from simple_feasible_loader import load_simple_feasible_data
            base_data = load_simple_feasible_data("Dataset_Dummy_Clinker_3MPlan.xlsx", ['1'])
            analyzer = DemandUncertaintyAnalyzer(base_data)
            scenarios = analyzer.generate_demand_scenarios(5, volatility)
            
            st.write("**Preview of scenarios with current settings:**")
            
            scenario_df = pd.DataFrame([
                {
                    'Scenario': s.name,
                    'Probability': f"{s.probability:.2%}",
                    'Demand Multiplier': f"{s.demand_multiplier:.2f}x",
                    'Expected Demand': f"{sum(base_data.demand.values()) * s.demand_multiplier:,.0f}"
                }
                for s in scenarios
            ])
            
            st.dataframe(scenario_df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    render_demand_uncertainty_analysis()
