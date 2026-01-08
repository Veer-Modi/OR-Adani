"""
OUTPUT CASES AND DEMONSTRATIONS FOR CLINKER OPTIMIZATION

This script generates various output cases and demonstrates the optimization models
with different scenarios and result interpretations.
"""

import pandas as pd
import numpy as np
from optimization_formulation import ClinkerOptimizationData
import matplotlib.pyplot as plt
import seaborn as sns

class OutputCaseGenerator:
    def __init__(self, data_file):
        self.data = ClinkerOptimizationData(data_file)
        
    def generate_data_summary_cases(self):
        """Generate comprehensive data summary cases"""
        print("=" * 80)
        print("CASE 1: COMPREHENSIVE DATA ANALYSIS")
        print("=" * 80)
        
        # Case 1.1: Demand Analysis by Period
        print("\n1.1 DEMAND ANALYSIS BY PERIOD")
        print("-" * 50)
        demand_by_period = {}
        for period in self.data.periods:
            period_demand = sum(
                demand for (iugu, t), demand in self.data.demand_dict.items() 
                if t == period
            )
            demand_by_period[period] = period_demand
            print(f"Period {period}: {period_demand:,} units")
        
        print(f"\nTotal Demand: {sum(demand_by_period.values()):,} units")
        print(f"Average per Period: {np.mean(list(demand_by_period.values())):,.0f} units")
        
        # Case 1.2: Capacity Analysis by IU
        print("\n1.2 CAPACITY ANALYSIS BY PRODUCTION FACILITY")
        print("-" * 50)
        capacity_by_iu = {}
        for iu in self.data.IU_codes:
            total_capacity = sum(
                capacity for (facility, t), capacity in self.data.capacity_dict.items()
                if facility == iu
            )
            capacity_by_iu[iu] = total_capacity
        
        # Sort and display top 10 facilities
        sorted_capacity = sorted(capacity_by_iu.items(), key=lambda x: x[1], reverse=True)
        print("Top 10 Production Facilities by Total Capacity:")
        for i, (iu, capacity) in enumerate(sorted_capacity[:10], 1):
            print(f"{i:2d}. {iu}: {capacity:,} units")
        
        # Case 1.3: Cost Structure Analysis
        print("\n1.3 COST STRUCTURE ANALYSIS")
        print("-" * 50)
        
        # Production costs
        prod_costs = list(self.data.prod_cost_dict.values())
        print(f"Production Cost Range: ${min(prod_costs):,.0f} - ${max(prod_costs):,.0f}")
        print(f"Average Production Cost: ${np.mean(prod_costs):,.0f}")
        
        # Transportation costs
        trans_costs = list(self.data.transport_cost_dict.values())
        non_zero_trans = [cost for cost in trans_costs if cost > 0]
        if non_zero_trans:
            print(f"Transport Cost Range: ${min(non_zero_trans):,.0f} - ${max(non_zero_trans):,.0f}")
            print(f"Average Transport Cost: ${np.mean(non_zero_trans):,.0f}")
        
        # Case 1.4: Inventory Analysis
        print("\n1.4 INVENTORY ANALYSIS")
        print("-" * 50)
        total_opening_stock = sum(self.data.opening_stock_dict.values())
        print(f"Total Opening Stock: {total_opening_stock:,} units")
        print(f"Stock Coverage: {(total_opening_stock / sum(demand_by_period.values()) * 100):.1f}% of Period 1 Demand")
        
        # Top 10 locations by opening stock
        sorted_stock = sorted(
            self.data.opening_stock_dict.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        print("\nTop 10 Locations by Opening Stock:")
        for i, (iugu, stock) in enumerate(sorted_stock[:10], 1):
            print(f"{i:2d}. {iugu}: {stock:,.0f} units")
    
    def generate_optimization_scenarios(self):
        """Generate different optimization scenarios"""
        print("\n" + "=" * 80)
        print("CASE 2: OPTIMIZATION SCENARIOS")
        print("=" * 80)
        
        # Scenario 2.1: Capacity Utilization Analysis
        print("\n2.1 CAPACITY UTILIZATION SCENARIOS")
        print("-" * 50)
        
        total_capacity = sum(self.data.capacity_dict.values())
        total_demand = sum(self.data.demand_dict.values())
        total_stock = sum(self.data.opening_stock_dict.values())
        
        print(f"Total Production Capacity: {total_capacity:,}")
        print(f"Total Demand: {total_demand:,}")
        print(f"Total Opening Stock: {total_stock:,}")
        print(f"Available Supply: {total_capacity + total_stock:,}")
        print(f"Supply-Demand Gap: {(total_capacity + total_stock) - total_demand:,}")
        print(f"Capacity Utilization Needed: {(total_demand / total_capacity * 100):.1f}%")
        
        # Scenario 2.2: Transportation Network Analysis
        print("\n2.2 TRANSPORTATION NETWORK ANALYSIS")
        print("-" * 50)
        
        # Count routes by origin
        routes_by_origin = {}
        for (iu, iugu, t) in self.data.transport_routes:
            if iu not in routes_by_origin:
                routes_by_origin[iu] = 0
            routes_by_origin[iu] += 1
        
        print("Top 10 Production Facilities by Number of Routes:")
        sorted_routes = sorted(routes_by_origin.items(), key=lambda x: x[1], reverse=True)
        for i, (iu, routes) in enumerate(sorted_routes[:10], 1):
            print(f"{i:2d}. {iu}: {routes} routes")
        
        # Scenario 2.3: Demand Distribution Analysis
        print("\n2.3 DEMAND DISTRIBUTION ANALYSIS")
        print("-" * 50)
        
        demand_by_iugu = {}
        for (iugu, t), demand in self.data.demand_dict.items():
            if iugu not in demand_by_iugu:
                demand_by_iugu[iugu] = 0
            demand_by_iugu[iugu] += demand
        
        # Statistics
        demands = list(demand_by_iugu.values())
        print(f"Number of Demand Points: {len(demand_by_iugu)}")
        print(f"Highest Demand: {max(demands):,}")
        print(f"Lowest Demand: {min(demands):,}")
        print(f"Average Demand: {np.mean(demands):,.0f}")
        print(f"Demand Standard Deviation: {np.std(demands):,.0f}")
        
        # Top 10 demand points
        sorted_demand = sorted(demand_by_iugu.items(), key=lambda x: x[1], reverse=True)
        print("\nTop 10 Demand Points:")
        for i, (iugu, demand) in enumerate(sorted_demand[:10], 1):
            print(f"{i:2d}. {iugu}: {demand:,} units")
    
    def generate_what_if_scenarios(self):
        """Generate what-if analysis scenarios"""
        print("\n" + "=" * 80)
        print("CASE 3: WHAT-IF SCENARIOS")
        print("=" * 80)
        
        # Scenario 3.1: Capacity Expansion Impact
        print("\n3.1 CAPACITY EXPANSION IMPACT")
        print("-" * 50)
        
        total_capacity = sum(self.data.capacity_dict.values())
        total_demand = sum(self.data.demand_dict.values())
        
        print("Capacity Expansion Scenarios:")
        for expansion_pct in [10, 20, 30, 50]:
            expanded_capacity = total_capacity * (1 + expansion_pct/100)
            utilization = (total_demand / expanded_capacity) * 100
            print(f"  +{expansion_pct}% Capacity: {utilization:.1f}% utilization")
        
        # Scenario 3.2: Demand Fluctuation Impact
        print("\n3.2 DEMAND FLUCTUATION IMPACT")
        print("-" * 50)
        
        print("Demand Change Scenarios:")
        for demand_change in [-20, -10, 0, 10, 20]:
            changed_demand = total_demand * (1 + demand_change/100)
            utilization = (changed_demand / total_capacity) * 100
            print(f"  {demand_change:+d}% Demand: {utilization:.1f}% utilization")
        
        # Scenario 3.3: Cost Reduction Impact
        print("\n3.3 COST REDUCTION IMPACT")
        print("-" * 50)
        
        avg_prod_cost = np.mean(list(self.data.prod_cost_dict.values()))
        avg_trans_cost = np.mean([c for c in self.data.transport_cost_dict.values() if c > 0])
        
        print("Cost Reduction Scenarios (Annual Savings):")
        for cost_reduction in [5, 10, 15, 20]:
            prod_savings = avg_prod_cost * total_capacity * (cost_reduction/100)
            trans_savings = avg_trans_cost * len(self.data.transport_routes) * 100 * (cost_reduction/100)  # Estimate
            total_savings = prod_savings + trans_savings
            print(f"  -{cost_reduction}% Costs: ${total_savings:,.0f} savings")
    
    def generate_kpi_dashboard_data(self):
        """Generate KPI dashboard data"""
        print("\n" + "=" * 80)
        print("CASE 4: KPI DASHBOARD DATA")
        print("=" * 80)
        
        # Calculate key metrics
        total_capacity = sum(self.data.capacity_dict.values())
        total_demand = sum(self.data.demand_dict.values())
        total_stock = sum(self.data.opening_stock_dict.values())
        
        print("\n4.1 OPERATIONAL KPIs")
        print("-" * 50)
        print(f"Supply Chain Efficiency: {(total_capacity / total_demand * 100):.1f}%")
        print(f"Inventory Coverage: {(total_stock / total_demand * 100):.1f}%")
        print(f"Network Complexity: {len(self.data.transport_routes)} routes")
        print(f"Facility Utilization Target: {(total_demand / total_capacity * 100):.1f}%")
        
        print("\n4.2 FINANCIAL KPIs")
        print("-" * 50)
        avg_prod_cost = np.mean(list(self.data.prod_cost_dict.values()))
        estimated_prod_cost = avg_prod_cost * total_capacity
        print(f"Estimated Production Cost: ${estimated_prod_cost:,.0f}")
        
        avg_trans_cost = np.mean([c for c in self.data.transport_cost_dict.values() if c > 0])
        estimated_trans_cost = avg_trans_cost * len(self.data.transport_routes) * 50  # Estimate
        print(f"Estimated Transport Cost: ${estimated_trans_cost:,.0f}")
        
        holding_cost_rate = 0.1  # 10% annual holding cost
        estimated_holding_cost = total_stock * avg_prod_cost * holding_cost_rate
        print(f"Estimated Holding Cost: ${estimated_holding_cost:,.0f}")
        
        total_estimated_cost = estimated_prod_cost + estimated_trans_cost + estimated_holding_cost
        print(f"Total Estimated Cost: ${total_estimated_cost:,.0f}")
        
        print("\n4.3 STRATEGIC KPIs")
        print("-" * 50)
        print(f"Number of Production Facilities: {len(self.data.IU_codes)}")
        print(f"Number of Demand Points: {len(self.data.IUGU_codes)}")
        print(f"Planning Horizon: {len(self.data.periods)} periods")
        print(f"Average Facility Size: {total_capacity / len(self.data.IU_codes):,.0f} units")
        print(f"Average Demand per Location: {total_demand / len(self.data.IUGU_codes):,.0f} units")
    
    def generate_sample_optimization_results(self):
        """Generate sample optimization results for demonstration"""
        print("\n" + "=" * 80)
        print("CASE 5: SAMPLE OPTIMIZATION RESULTS")
        print("=" * 80)
        
        print("\n5.1 SAMPLE PRODUCTION PLAN")
        print("-" * 50)
        print("Period 1 Production Allocation (Sample):")
        
        # Generate sample production plan
        sample_production = {}
        remaining_demand = sum(
            demand for (iugu, t), demand in self.data.demand_dict.items() if t == 1
        )
        
        for iu in list(self.data.IU_codes)[:8]:  # Top 8 facilities
            capacity = self.data.capacity_dict.get((iu, 1), 0)
            if capacity > 0:
                allocation = min(capacity, remaining_demand / 4)  # Allocate portion
                sample_production[iu] = allocation
                remaining_demand -= allocation
                print(f"  {iu}: {allocation:,.0f} units ({allocation/capacity*100:.1f}% capacity)")
        
        print(f"\nTotal Planned Production: {sum(sample_production.values()):,.0f} units")
        
        print("\n5.2 SAMPLE TRANSPORTATION PLAN")
        print("-" * 50)
        print("Sample Transportation Routes (Top 10):")
        
        # Generate sample transport routes
        sample_routes = []
        for (iu, iugu, t) in list(self.data.transport_routes)[:10]:
            if t == 1 and iu in sample_production:
                cost = self.data.transport_cost_dict.get((iu, iugu, t), 0)
                quantity = min(10000, sample_production.get(iu, 0) / 5)
                sample_routes.append((iu, iugu, quantity, cost))
                print(f"  {iu} -> {iugu}: {quantity:,.0f} units (Cost: ${cost:.0f}/unit)")
        
        print("\n5.3 SAMPLE INVENTORY PLAN")
        print("-" * 50)
        print("Sample Inventory Levels (Period 1 End):")
        
        # Generate sample inventory levels
        for iugu in list(self.data.IUGU_codes)[:5]:
            opening = self.data.opening_stock_dict.get(iugu, 0)
            demand = self.data.demand_dict.get((iugu, 1), 0)
            received = sum(qty for _, dest, qty, _ in sample_routes if dest == iugu)
            closing = opening + received - demand
            print(f"  {iugu}: {closing:,.0f} units (Opening: {opening:,.0f}, Demand: {demand:,.0f})")
    
    def export_summary_report(self):
        """Export comprehensive summary report"""
        print("\n" + "=" * 80)
        print("EXPORTING SUMMARY REPORT")
        print("=" * 80)
        
        # Create summary data
        summary_data = {
            'Metric': [
                'Total Production Capacity',
                'Total Demand',
                'Total Opening Stock',
                'Supply-Demand Gap',
                'Number of Facilities',
                'Number of Demand Points',
                'Transport Routes',
                'Planning Periods',
                'Average Production Cost',
                'Average Transport Cost',
                'Capacity Utilization Required',
                'Inventory Coverage Ratio'
            ],
            'Value': [
                sum(self.data.capacity_dict.values()),
                sum(self.data.demand_dict.values()),
                sum(self.data.opening_stock_dict.values()),
                (sum(self.data.capacity_dict.values()) + sum(self.data.opening_stock_dict.values())) - sum(self.data.demand_dict.values()),
                len(self.data.IU_codes),
                len(self.data.IUGU_codes),
                len(self.data.transport_routes),
                len(self.data.periods),
                np.mean(list(self.data.prod_cost_dict.values())),
                np.mean([c for c in self.data.transport_cost_dict.values() if c > 0]) if any(c > 0 for c in self.data.transport_cost_dict.values()) else 0,
                (sum(self.data.demand_dict.values()) / sum(self.data.capacity_dict.values()) * 100),
                (sum(self.data.opening_stock_dict.values()) / sum(self.data.demand_dict.values()) * 100)
            ],
            'Unit': [
                'units', 'units', 'units', 'units', 'facilities', 'locations', 
                'routes', 'periods', '$/unit', '$/unit', '%', '%'
            ]
        }
        
        summary_df = pd.DataFrame(summary_data)
        
        # Export to Excel
        with pd.ExcelWriter('clinker_optimization_summary.xlsx', engine='openpyxl') as writer:
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Export detailed data
            demand_df = pd.DataFrame([
                {'IUGU': iugu, 'Period': t, 'Demand': demand}
                for (iugu, t), demand in self.data.demand_dict.items()
            ])
            demand_df.to_excel(writer, sheet_name='Demand_Details', index=False)
            
            capacity_df = pd.DataFrame([
                {'IU': iu, 'Period': t, 'Capacity': capacity}
                for (iu, t), capacity in self.data.capacity_dict.items()
            ])
            capacity_df.to_excel(writer, sheet_name='Capacity_Details', index=False)
        
        print("Summary report exported to 'clinker_optimization_summary.xlsx'")
        print(f"Summary includes {len(summary_df)} key metrics and detailed data tables")

def main():
    """Main function to generate all output cases"""
    try:
        print("GENERATING COMPREHENSIVE OUTPUT CASES FOR CLINKER OPTIMIZATION")
        print("=" * 80)
        
        # Initialize generator
        generator = OutputCaseGenerator('Dataset_Dummy_Clinker_3MPlan.xlsx')
        
        # Generate all cases
        generator.generate_data_summary_cases()
        generator.generate_optimization_scenarios()
        generator.generate_what_if_scenarios()
        generator.generate_kpi_dashboard_data()
        generator.generate_sample_optimization_results()
        generator.export_summary_report()
        
        print("\n" + "=" * 80)
        print("ALL OUTPUT CASES GENERATED SUCCESSFULLY")
        print("=" * 80)
        print("\nFiles Created:")
        print("- clinker_optimization_summary.xlsx: Comprehensive summary report")
        print("\nNext Steps:")
        print("1. Review the summary report for key insights")
        print("2. Run optimization models with actual solvers")
        print("3. Compare results with sample scenarios")
        print("4. Perform sensitivity analysis based on what-if scenarios")
        
    except Exception as e:
        print(f"Error generating output cases: {e}")

if __name__ == "__main__":
    main()
