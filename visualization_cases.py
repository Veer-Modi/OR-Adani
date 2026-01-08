"""
VISUALIZATION AND ADVANCED OUTPUT CASES FOR CLINKER OPTIMIZATION

This script creates visualizations and advanced analysis cases for the optimization results.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from optimization_formulation import ClinkerOptimizationData
import warnings
warnings.filterwarnings('ignore')

class VisualizationCaseGenerator:
    def __init__(self, data_file):
        self.data = ClinkerOptimizationData(data_file)
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
    def create_demand_capacity_analysis(self):
        """Create demand vs capacity analysis visualizations"""
        print("GENERATING DEMAND VS CAPACITY ANALYSIS")
        print("=" * 50)
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Clinker Supply Chain: Demand vs Capacity Analysis', fontsize=16, fontweight='bold')
        
        # 1. Demand by Period
        demand_by_period = {}
        for period in self.data.periods:
            period_demand = sum(
                demand for (iugu, t), demand in self.data.demand_dict.items() 
                if t == period
            )
            demand_by_period[period] = period_demand
        
        axes[0,0].bar(demand_by_period.keys(), demand_by_period.values(), color='skyblue')
        axes[0,0].set_title('Demand by Time Period')
        axes[0,0].set_xlabel('Period')
        axes[0,0].set_ylabel('Demand (units)')
        axes[0,0].ticklabel_format(style='plain', axis='y')
        
        # Add value labels on bars
        for i, (period, demand) in enumerate(demand_by_period.items()):
            axes[0,0].text(period+1, demand + 100000, f'{demand:,}', 
                          ha='center', va='bottom', fontweight='bold')
        
        # 2. Capacity by Facility (Top 10)
        capacity_by_iu = {}
        for iu in self.data.IU_codes:
            total_capacity = sum(
                capacity for (facility, t), capacity in self.data.capacity_dict.items()
                if facility == iu
            )
            capacity_by_iu[iu] = total_capacity
        
        top_10_capacity = sorted(capacity_by_iu.items(), key=lambda x: x[1], reverse=True)[:10]
        
        axes[0,1].barh([iu for iu, _ in top_10_capacity], 
                      [capacity for _, capacity in top_10_capacity], color='lightcoral')
        axes[0,1].set_title('Top 10 Production Facilities by Capacity')
        axes[0,1].set_xlabel('Total Capacity (units)')
        axes[0,1].ticklabel_format(style='plain', axis='x')
        
        # 3. Demand Distribution
        demand_by_iugu = {}
        for (iugu, t), demand in self.data.demand_dict.items():
            if iugu not in demand_by_iugu:
                demand_by_iugu[iugu] = 0
            demand_by_iugu[iugu] += demand
        
        axes[1,0].hist(list(demand_by_iugu.values()), bins=15, color='lightgreen', alpha=0.7)
        axes[1,0].set_title('Demand Distribution Across Locations')
        axes[1,0].set_xlabel('Total Demand per Location (units)')
        axes[1,0].set_ylabel('Number of Locations')
        axes[1,0].ticklabel_format(style='plain', axis='x')
        
        # 4. Capacity vs Demand Comparison
        total_capacity = sum(self.data.capacity_dict.values())
        total_demand = sum(self.data.demand_dict.values())
        total_stock = sum(self.data.opening_stock_dict.values())
        
        categories = ['Production\nCapacity', 'Total\nDemand', 'Opening\nStock']
        values = [total_capacity, total_demand, total_stock]
        colors = ['blue', 'red', 'green']
        
        bars = axes[1,1].bar(categories, values, color=colors, alpha=0.7)
        axes[1,1].set_title('Overall Supply vs Demand')
        axes[1,1].set_ylabel('Units')
        axes[1,1].ticklabel_format(style='plain', axis='y')
        
        # Add value labels
        for bar, value in zip(bars, values):
            height = bar.get_height()
            axes[1,1].text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                          f'{value:,}', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig('demand_capacity_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # Print key insights
        print(f"Key Insights:")
        print(f"- Total Capacity: {total_capacity:,} units")
        print(f"- Total Demand: {total_demand:,} units")
        print(f"- Gap: {total_demand - total_capacity:,} units ({(total_demand/total_capacity-1)*100:.1f}% excess demand)")
        print(f"- Opening Stock Coverage: {(total_stock/total_demand)*100:.1f}% of demand")
        
    def create_cost_analysis_visualization(self):
        """Create cost structure analysis"""
        print("\nGENERATING COST STRUCTURE ANALYSIS")
        print("=" * 50)
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Clinker Supply Chain: Cost Structure Analysis', fontsize=16, fontweight='bold')
        
        # 1. Production Cost Distribution
        prod_costs = list(self.data.prod_cost_dict.values())
        axes[0,0].hist(prod_costs, bins=20, color='gold', alpha=0.7, edgecolor='black')
        axes[0,0].set_title('Production Cost Distribution')
        axes[0,0].set_xlabel('Production Cost ($/unit)')
        axes[0,0].set_ylabel('Frequency')
        axes[0,0].axvline(np.mean(prod_costs), color='red', linestyle='--', 
                         label=f'Mean: ${np.mean(prod_costs):.0f}')
        axes[0,0].legend()
        
        # 2. Transport Cost Distribution
        trans_costs = [cost for cost in self.data.transport_cost_dict.values() if cost > 0]
        if trans_costs:
            axes[0,1].hist(trans_costs, bins=20, color='lightblue', alpha=0.7, edgecolor='black')
            axes[0,1].set_title('Transport Cost Distribution (Non-zero)')
            axes[0,1].set_xlabel('Transport Cost ($/unit)')
            axes[0,1].set_ylabel('Frequency')
            axes[0,1].axvline(np.mean(trans_costs), color='red', linestyle='--',
                             label=f'Mean: ${np.mean(trans_costs):.0f}')
            axes[0,1].legend()
        
        # 3. Cost by Facility
        facility_costs = {}
        for iu in self.data.IU_codes:
            costs = [cost for (facility, t), cost in self.data.prod_cost_dict.items() if facility == iu]
            if costs:
                facility_costs[iu] = np.mean(costs)
        
        if facility_costs:
            sorted_facilities = sorted(facility_costs.items(), key=lambda x: x[1])[:15]
            axes[1,0].barh([iu for iu, _ in sorted_facilities], 
                          [cost for _, cost in sorted_facilities], color='orange')
            axes[1,0].set_title('Average Production Cost by Facility (Lowest 15)')
            axes[1,0].set_xlabel('Average Cost ($/unit)')
        
        # 4. Cost Comparison Pie Chart
        total_capacity = sum(self.data.capacity_dict.values())
        avg_prod_cost = np.mean(prod_costs)
        total_prod_cost = total_capacity * avg_prod_cost
        
        avg_trans_cost = np.mean(trans_costs) if trans_costs else 0
        estimated_trans_cost = avg_trans_cost * len(self.data.transport_routes) * 100  # Estimate
        
        holding_cost_rate = 0.1
        total_stock = sum(self.data.opening_stock_dict.values())
        estimated_holding_cost = total_stock * avg_prod_cost * holding_cost_rate
        
        costs = [total_prod_cost, estimated_trans_cost, estimated_holding_cost]
        labels = ['Production', 'Transportation', 'Inventory Holding']
        colors = ['#ff9999', '#66b3ff', '#99ff99']
        
        axes[1,1].pie(costs, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        axes[1,1].set_title('Estimated Cost Breakdown')
        
        plt.tight_layout()
        plt.savefig('cost_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"Cost Analysis Summary:")
        print(f"- Average Production Cost: ${np.mean(prod_costs):.0f}/unit")
        print(f"- Average Transport Cost: ${np.mean(trans_costs):.0f}/unit" if trans_costs else "- No transport data")
        print(f"- Estimated Annual Production Cost: ${total_prod_cost:,.0f}")
        print(f"- Estimated Annual Transport Cost: ${estimated_trans_cost:,.0f}")
        print(f"- Estimated Annual Holding Cost: ${estimated_holding_cost:,.0f}")
        
    def create_network_analysis(self):
        """Create transportation network analysis"""
        print("\nGENERATING TRANSPORTATION NETWORK ANALYSIS")
        print("=" * 50)
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Clinker Supply Chain: Network Analysis', fontsize=16, fontweight='bold')
        
        # 1. Routes by Origin Facility
        routes_by_origin = {}
        for (iu, iugu, t) in self.data.transport_routes:
            if iu not in routes_by_origin:
                routes_by_origin[iu] = 0
            routes_by_origin[iu] += 1
        
        top_origins = sorted(routes_by_origin.items(), key=lambda x: x[1], reverse=True)[:15]
        axes[0,0].barh([iu for iu, _ in top_origins], 
                      [routes for _, routes in top_origins], color='purple')
        axes[0,0].set_title('Top 15 Facilities by Number of Routes')
        axes[0,0].set_xlabel('Number of Routes')
        
        # 2. Routes by Destination
        routes_by_dest = {}
        for (iu, iugu, t) in self.data.transport_routes:
            if iugu not in routes_by_dest:
                routes_by_dest[iugu] = 0
            routes_by_dest[iugu] += 1
        
        top_dests = sorted(routes_by_dest.items(), key=lambda x: x[1], reverse=True)[:15]
        axes[0,1].barh([iugu for iugu, _ in top_dests], 
                      [routes for _, routes in top_dests], color='teal')
        axes[0,1].set_title('Top 15 Destinations by Number of Routes')
        axes[0,1].set_xlabel('Number of Routes')
        
        # 3. Transport Cost Heatmap (Sample)
        # Create a sample cost matrix for visualization
        sample_origins = list(routes_by_origin.keys())[:10]
        sample_dests = list(routes_by_dest.keys())[:10]
        
        cost_matrix = np.zeros((len(sample_origins), len(sample_dests)))
        for i, origin in enumerate(sample_origins):
            for j, dest in enumerate(sample_dests):
                for t in self.data.periods:
                    cost = self.data.transport_cost_dict.get((origin, dest, t), 0)
                    if cost > 0:
                        cost_matrix[i, j] = cost
                        break
        
        im = axes[1,0].imshow(cost_matrix, cmap='YlOrRd', aspect='auto')
        axes[1,0].set_title('Transport Cost Heatmap (Sample)')
        axes[1,0].set_xticks(range(len(sample_dests)))
        axes[1,0].set_yticks(range(len(sample_origins)))
        axes[1,0].set_xticklabels(sample_dests, rotation=45)
        axes[1,0].set_yticklabels(sample_origins)
        plt.colorbar(im, ax=axes[1,0], label='Cost ($/unit)')
        
        # 4. Network Connectivity Distribution
        connectivity = list(routes_by_origin.values())
        axes[1,1].hist(connectivity, bins=15, color='brown', alpha=0.7, edgecolor='black')
        axes[1,1].set_title('Network Connectivity Distribution')
        axes[1,1].set_xlabel('Number of Routes per Facility')
        axes[1,1].set_ylabel('Number of Facilities')
        axes[1,1].axvline(np.mean(connectivity), color='red', linestyle='--',
                         label=f'Mean: {np.mean(connectivity):.1f}')
        axes[1,1].legend()
        
        plt.tight_layout()
        plt.savefig('network_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"Network Analysis Summary:")
        print(f"- Total Routes: {len(self.data.transport_routes)}")
        print(f"- Average Routes per Facility: {np.mean(connectivity):.1f}")
        print(f"- Most Connected Facility: {max(routes_by_origin.items(), key=lambda x: x[1])}")
        print(f"- Most Served Destination: {max(routes_by_dest.items(), key=lambda x: x[1])}")
        
    def create_scenario_analysis(self):
        """Create what-if scenario analysis"""
        print("\nGENERATING SCENARIO ANALYSIS")
        print("=" * 50)
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Clinker Supply Chain: Scenario Analysis', fontsize=16, fontweight='bold')
        
        # Current baseline
        total_capacity = sum(self.data.capacity_dict.values())
        total_demand = sum(self.data.demand_dict.values())
        
        # 1. Capacity Expansion Scenarios
        expansion_scenarios = [0, 10, 20, 30, 50, 100]
        utilization_rates = []
        for exp in expansion_scenarios:
            expanded_capacity = total_capacity * (1 + exp/100)
            utilization = (total_demand / expanded_capacity) * 100
            utilization_rates.append(utilization)
        
        axes[0,0].plot(expansion_scenarios, utilization_rates, 'bo-', linewidth=2, markersize=8)
        axes[0,0].axhline(y=100, color='r', linestyle='--', label='100% Utilization')
        axes[0,0].set_title('Capacity Expansion Impact')
        axes[0,0].set_xlabel('Capacity Expansion (%)')
        axes[0,0].set_ylabel('Capacity Utilization (%)')
        axes[0,0].grid(True, alpha=0.3)
        axes[0,0].legend()
        
        # Add value labels
        for i, (exp, util) in enumerate(zip(expansion_scenarios, utilization_rates)):
            axes[0,0].annotate(f'{util:.1f}%', (exp, util), textcoords="offset points", 
                             xytext=(0,10), ha='center')
        
        # 2. Demand Fluctuation Scenarios
        demand_changes = [-30, -20, -10, 0, 10, 20, 30]
        demand_utilization = []
        for change in demand_changes:
            changed_demand = total_demand * (1 + change/100)
            utilization = (changed_demand / total_capacity) * 100
            demand_utilization.append(utilization)
        
        axes[0,1].plot(demand_changes, demand_utilization, 'ro-', linewidth=2, markersize=8)
        axes[0,1].axhline(y=100, color='g', linestyle='--', label='100% Utilization')
        axes[0,1].axhline(y=163.7, color='b', linestyle='--', label='Current Utilization')
        axes[0,1].set_title('Demand Fluctuation Impact')
        axes[0,1].set_xlabel('Demand Change (%)')
        axes[0,1].set_ylabel('Capacity Utilization (%)')
        axes[0,1].grid(True, alpha=0.3)
        axes[0,1].legend()
        
        # 3. Cost Reduction Impact
        cost_reductions = [5, 10, 15, 20, 25, 30]
        avg_prod_cost = np.mean(list(self.data.prod_cost_dict.values()))
        total_prod_cost = avg_prod_cost * total_capacity
        
        savings = [total_prod_cost * (reduction/100) for reduction in cost_reductions]
        
        axes[1,0].bar(cost_reductions, savings, color='green', alpha=0.7)
        axes[1,0].set_title('Production Cost Reduction Impact')
        axes[1,0].set_xlabel('Cost Reduction (%)')
        axes[1,0].set_ylabel('Annual Savings ($)')
        axes[1,0].ticklabel_format(style='plain', axis='y')
        
        # Add value labels
        for i, (reduction, saving) in enumerate(zip(cost_reductions, savings)):
            axes[1,0].text(reduction, saving + saving*0.01, f'${saving/1e9:.1f}B', 
                          ha='center', va='bottom', fontweight='bold')
        
        # 4. Feasibility Matrix
        capacity_expansions = [0, 20, 40, 60, 80, 100]
        demand_reductions = [0, 10, 20, 30, 40, 50]
        
        feasibility_matrix = np.zeros((len(demand_reductions), len(capacity_expansions)))
        
        for i, demand_red in enumerate(demand_reductions):
            for j, cap_exp in enumerate(capacity_expansions):
                adjusted_demand = total_demand * (1 - demand_red/100)
                adjusted_capacity = total_capacity * (1 + cap_exp/100)
                utilization = (adjusted_demand / adjusted_capacity) * 100
                feasibility_matrix[i, j] = utilization
        
        im = axes[1,1].imshow(feasibility_matrix, cmap='RdYlGn_r', aspect='auto', vmin=0, vmax=200)
        axes[1,1].set_title('Feasibility Matrix (Utilization %)')
        axes[1,1].set_xticks(range(len(capacity_expansions)))
        axes[1,1].set_yticks(range(len(demand_reductions)))
        axes[1,1].set_xticklabels([f'+{exp}%' for exp in capacity_expansions])
        axes[1,1].set_yticklabels([f'-{red}%' for red in demand_reductions])
        axes[1,1].set_xlabel('Capacity Expansion')
        axes[1,1].set_ylabel('Demand Reduction')
        
        # Add contour lines for key utilization levels
        contours = axes[1,1].contour(feasibility_matrix, levels=[100, 150], colors=['black', 'white'], 
                                    linewidths=2, linestyles='--')
        axes[1,1].clabel(contours, inline=True, fontsize=10)
        
        plt.colorbar(im, ax=axes[1,1], label='Utilization (%)')
        plt.tight_layout()
        plt.savefig('scenario_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"Scenario Analysis Summary:")
        print(f"- Current Utilization: {(total_demand/total_capacity)*100:.1f}%")
        print(f"- Capacity needed for 100% utilization: {(total_demand/total_capacity - 1)*100:.1f}% increase")
        print(f"- Demand reduction needed for 100% utilization: {(1 - total_capacity/total_demand)*100:.1f}% decrease")
        print(f"- 10% cost reduction would save: ${total_prod_cost * 0.1:,.0f} annually")

def main():
    """Main function to generate all visualizations"""
    try:
        print("GENERATING COMPREHENSIVE VISUALIZATION OUTPUT CASES")
        print("=" * 80)
        
        # Initialize generator
        generator = VisualizationCaseGenerator('Dataset_Dummy_Clinker_3MPlan.xlsx')
        
        # Generate all visualizations
        generator.create_demand_capacity_analysis()
        generator.create_cost_analysis_visualization()
        generator.create_network_analysis()
        generator.create_scenario_analysis()
        
        print("\n" + "=" * 80)
        print("ALL VISUALIZATIONS GENERATED SUCCESSFULLY")
        print("=" * 80)
        print("\nFiles Created:")
        print("- demand_capacity_analysis.png: Demand vs capacity analysis")
        print("- cost_analysis.png: Cost structure analysis")
        print("- network_analysis.png: Transportation network analysis")
        print("- scenario_analysis.png: What-if scenario analysis")
        print("\nThese visualizations provide comprehensive insights into:")
        print("1. Supply-demand balance and capacity constraints")
        print("2. Cost structure and optimization opportunities")
        print("3. Network complexity and connectivity")
        print("4. Scenario planning and feasibility analysis")
        
    except Exception as e:
        print(f"Error generating visualizations: {e}")

if __name__ == "__main__":
    main()
