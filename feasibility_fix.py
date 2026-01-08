"""
FEASIBILITY ANALYSIS AND FIXES FOR CLINKER OPTIMIZATION

This script identifies and fixes infeasibility issues in the optimization models.
"""

import pandas as pd
import numpy as np
from optimization_formulation import ClinkerOptimizationData

class FeasibilityAnalyzer:
    def __init__(self, data_file):
        self.data = ClinkerOptimizationData(data_file)
        
    def analyze_feasibility_issues(self):
        """Analyze what's causing infeasibility"""
        print("=" * 80)
        print("FEASIBILITY ANALYSIS FOR CLINKER OPTIMIZATION")
        print("=" * 80)
        
        # Calculate totals
        total_capacity = sum(self.data.capacity_dict.values())
        total_demand = sum(self.data.demand_dict.values())
        total_stock = sum(self.data.opening_stock_dict.values())
        
        print(f"\n📊 SUPPLY-DEMAND BALANCE")
        print("-" * 50)
        print(f"Total Production Capacity: {total_capacity:,}")
        print(f"Total Opening Stock: {total_stock:,}")
        print(f"Total Available Supply: {total_capacity + total_stock:,}")
        print(f"Total Demand: {total_demand:,}")
        print(f"Supply-Demand Gap: {(total_capacity + total_stock) - total_demand:,}")
        print(f"Coverage Ratio: {((total_capacity + total_stock) / total_demand * 100):.1f}%")
        
        # Period-by-period analysis
        print(f"\n📅 PERIOD-BY-PERIOD ANALYSIS")
        print("-" * 50)
        
        for period in sorted(self.data.periods):
            period_capacity = sum(
                capacity for (iu, t), capacity in self.data.capacity_dict.items() 
                if t == period
            )
            period_demand = sum(
                demand for (iugu, t), demand in self.data.demand_dict.items() 
                if t == period
            )
            
            # Calculate opening stock for this period
            if period == min(self.data.periods):
                available_stock = total_stock
            else:
                # Simplified: assume stock carries over
                available_stock = total_stock / len(self.data.periods)
            
            period_supply = period_capacity + available_stock
            coverage = (period_supply / period_demand * 100) if period_demand > 0 else 0
            
            print(f"Period {period}:")
            print(f"  Capacity: {period_capacity:,}")
            print(f"  Demand: {period_demand:,}")
            print(f"  Available Stock: {available_stock:,.0f}")
            print(f"  Total Supply: {period_supply:,}")
            print(f"  Coverage: {coverage:.1f}%")
            
            if coverage < 100:
                shortage = period_demand - period_supply
                print(f"  ⚠️  SHORTAGE: {shortage:,} units")
        
        # Facility-specific analysis
        print(f"\n🏭 FACILITY-SPECIFIC ISSUES")
        print("-" * 50)
        
        # Check for facilities with no capacity data
        facilities_with_capacity = set(iu for (iu, t) in self.data.capacity_dict.keys())
        all_facilities = set(self.data.IU_codes)
        missing_capacity = all_facilities - facilities_with_capacity
        
        if missing_capacity:
            print(f"Facilities with NO capacity data: {len(missing_capacity)}")
            for facility in sorted(missing_capacity):
                print(f"  - {facility}")
        
        # Check for demand points with no opening stock
        locations_with_stock = set(self.data.opening_stock_dict.keys())
        all_locations = set(self.data.IUGU_codes)
        missing_stock = all_locations - locations_with_stock
        
        if missing_stock:
            print(f"\nLocations with NO opening stock: {len(missing_stock)}")
            for location in sorted(missing_stock)[:10]:  # Show first 10
                print(f"  - {location}")
        
        # Transportation network analysis
        print(f"\n🚚 TRANSPORTATION NETWORK ISSUES")
        print("-" * 50)
        
        # Check for disconnected locations
        connected_origins = set(iu for (iu, iugu, t) in self.data.transport_routes)
        connected_destinations = set(iugu for (iu, iugu, t) in self.data.transport_routes)
        
        disconnected_origins = all_facilities - connected_origins
        disconnected_destinations = all_locations - connected_destinations
        
        if disconnected_origins:
            print(f"Facilities with NO outbound routes: {len(disconnected_origins)}")
            for facility in sorted(disconnected_origins):
                print(f"  - {facility}")
        
        if disconnected_destinations:
            print(f"Locations with NO inbound routes: {len(disconnected_destinations)}")
            for location in sorted(disconnected_destinations)[:10]:
                print(f"  - {location}")
        
        return {
            'total_shortage': total_demand - (total_capacity + total_stock),
            'coverage_ratio': (total_capacity + total_stock) / total_demand,
            'missing_capacity_facilities': missing_capacity,
            'missing_stock_locations': missing_stock,
            'disconnected_origins': disconnected_origins,
            'disconnected_destinations': disconnected_destinations
        }
    
    def generate_feasible_scenarios(self):
        """Generate scenarios to make the problem feasible"""
        print(f"\n🔧 FEASIBILITY SCENARIOS")
        print("-" * 50)
        
        total_capacity = sum(self.data.capacity_dict.values())
        total_demand = sum(self.data.demand_dict.values())
        total_stock = sum(self.data.opening_stock_dict.values())
        
        scenarios = []
        
        # Scenario 1: Demand Reduction
        print("SCENARIO 1: DEMAND REDUCTION")
        demand_reduction_needed = 1 - ((total_capacity + total_stock) / total_demand)
        feasible_demand = total_demand * (1 - demand_reduction_needed)
        print(f"  Required reduction: {demand_reduction_needed*100:.1f}%")
        print(f"  Feasible demand: {feasible_demand:,}")
        scenarios.append(('Demand Reduction', demand_reduction_needed, feasible_demand))
        
        # Scenario 2: Capacity Expansion
        print("\nSCENARIO 2: CAPACITY EXPANSION")
        capacity_expansion_needed = (total_demand / total_stock) - 1
        feasible_capacity = total_capacity * (1 + capacity_expansion_needed)
        print(f"  Required expansion: {capacity_expansion_needed*100:.1f}%")
        print(f"  Feasible capacity: {feasible_capacity:,}")
        scenarios.append(('Capacity Expansion', capacity_expansion_needed, feasible_capacity))
        
        # Scenario 3: Combined Approach
        print("\nSCENARIO 3: COMBINED APPROACH")
        # 50% demand reduction + 50% capacity expansion
        demand_red = 0.25  # 25% reduction
        cap_exp = 0.5   # 50% expansion
        
        adjusted_demand = total_demand * (1 - demand_red)
        adjusted_capacity = total_capacity * (1 + cap_exp)
        total_supply = adjusted_capacity + total_stock
        
        coverage = total_supply / adjusted_demand
        print(f"  Demand reduction: {demand_red*100:.0f}%")
        print(f"  Capacity expansion: {cap_exp*100:.0f}%")
        print(f"  Coverage ratio: {coverage*100:.1f}%")
        scenarios.append(('Combined', (demand_red, cap_exp), coverage))
        
        return scenarios
    
    def create_feasible_data_adjustments(self):
        """Create adjusted data to make problem feasible"""
        print(f"\n📝 CREATING FEASIBLE DATA ADJUSTMENTS")
        print("-" * 50)
        
        # Strategy: Reduce demand by 30% to make it feasible
        demand_reduction_factor = 0.7
        
        # Create adjusted demand dictionary
        adjusted_demand = {}
        for (iugu, period), demand in self.data.demand_dict.items():
            adjusted_demand[(iugu, period)] = demand * demand_reduction_factor
        
        # Strategy: Increase capacity by 20%
        capacity_expansion_factor = 1.2
        
        # Create adjusted capacity dictionary
        adjusted_capacity = {}
        for (iu, period), capacity in self.data.capacity_dict.items():
            adjusted_capacity[(iu, period)] = capacity * capacity_expansion_factor
        
        # Strategy: Increase opening stock by 50%
        stock_expansion_factor = 1.5
        
        # Create adjusted opening stock dictionary
        adjusted_stock = {}
        for iugu, stock in self.data.opening_stock_dict.items():
            adjusted_stock[iugu] = stock * stock_expansion_factor
        
        # Verify feasibility
        new_total_capacity = sum(adjusted_capacity.values())
        new_total_demand = sum(adjusted_demand.values())
        new_total_stock = sum(adjusted_stock.values())
        
        coverage = (new_total_capacity + new_total_stock) / new_total_demand
        
        original_capacity = sum(self.data.capacity_dict.values())
        original_demand = sum(self.data.demand_dict.values())
        original_stock = sum(self.data.opening_stock_dict.values())
        
        print(f"Original Coverage: {((original_capacity + original_stock) / original_demand * 100):.1f}%")
        print(f"Adjusted Coverage: {coverage * 100:.1f}%")
        
        if coverage >= 1.0:
            print("✅ ADJUSTED PROBLEM IS FEASIBLE!")
        else:
            print("❌ ADJUSTED PROBLEM STILL INFEASIBLE")
        
        return {
            'adjusted_demand': adjusted_demand,
            'adjusted_capacity': adjusted_capacity,
            'adjusted_stock': adjusted_stock,
            'coverage_ratio': coverage
        }

def main():
    """Main function to run feasibility analysis"""
    try:
        analyzer = FeasibilityAnalyzer('Dataset_Dummy_Clinker_3MPlan.xlsx')
        
        # Analyze feasibility issues
        issues = analyzer.analyze_feasibility_issues()
        
        # Generate feasible scenarios
        scenarios = analyzer.generate_feasible_scenarios()
        
        # Create feasible adjustments
        adjustments = analyzer.create_feasible_data_adjustments()
        
        print(f"\n" + "=" * 80)
        print("FEASIBILITY ANALYSIS COMPLETE")
        print("=" * 80)
        print(f"\nRECOMMENDED ACTIONS:")
        print(f"1. Use adjusted data for initial testing")
        print(f"2. Implement demand prioritization in production")
        print(f"3. Consider capacity expansion for long-term")
        print(f"4. Add slack variables for soft constraints")
        
    except Exception as e:
        print(f"Error in feasibility analysis: {e}")

if __name__ == "__main__":
    main()
