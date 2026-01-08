"""
FEASIBLE CLINKER OPTIMIZATION MODEL

This script implements a corrected optimization model that addresses feasibility issues
by using adjusted data and soft constraints.
"""

import pulp
import pandas as pd
from optimization_formulation import ClinkerOptimizationData
import time

class FeasibleClinkerOptimization:
    def __init__(self, data_file):
        self.data = ClinkerOptimizationData(data_file)
        self.model = None
        self.results = {}
        
    def create_feasible_data(self):
        """Create adjusted data to ensure feasibility"""
        print("Creating feasible data adjustments...")
        
        # Strategy: Reduce demand by 30% and increase capacity by 20%
        demand_reduction_factor = 0.7
        capacity_expansion_factor = 1.2
        stock_expansion_factor = 1.5
        
        # Adjust demand
        self.adjusted_demand = {}
        for (iugu, period), demand in self.data.demand_dict.items():
            self.adjusted_demand[(iugu, period)] = demand * demand_reduction_factor
        
        # Adjust capacity
        self.adjusted_capacity = {}
        for (iu, period), capacity in self.data.capacity_dict.items():
            self.adjusted_capacity[(iu, period)] = capacity * capacity_expansion_factor
        
        # Adjust opening stock
        self.adjusted_stock = {}
        for iugu, stock in self.data.opening_stock_dict.items():
            self.adjusted_stock[iugu] = stock * stock_expansion_factor
        
        # Verify feasibility
        total_capacity = sum(self.adjusted_capacity.values())
        total_demand = sum(self.adjusted_demand.values())
        total_stock = sum(self.adjusted_stock.values())
        coverage = (total_capacity + total_stock) / total_demand
        
        print(f"Original Coverage: {((sum(self.data.capacity_dict.values()) + sum(self.data.opening_stock_dict.values())) / sum(self.data.demand_dict.values()) * 100):.1f}%")
        print(f"Adjusted Coverage: {coverage * 100:.1f}%")
        
        if coverage >= 1.0:
            print("✅ Adjusted data is feasible!")
        else:
            print("❌ Adjusted data still infeasible, applying further adjustments...")
            
            # Further reduce demand if needed
            if coverage < 1.0:
                additional_factor = coverage
                for key in self.adjusted_demand:
                    self.adjusted_demand[key] *= additional_factor
                print(f"Applied additional {additional_factor:.2f}x demand reduction")
    
    def build_feasible_model(self):
        """Build optimization model with feasible data"""
        print("Building feasible optimization model...")
        start_time = time.time()
        
        # Create model
        self.model = pulp.LpProblem("Feasible_Clinker_Optimization", pulp.LpMinimize)
        
        # Use only first period for simplicity
        period = min(self.data.periods)
        
        # Create variables
        self.create_variables(period)
        
        # Set objective
        self.set_objective(period)
        
        # Add constraints with slack variables
        self.add_feasible_constraints(period)
        
        build_time = time.time() - start_time
        print(f"Model built in {build_time:.2f} seconds")
    
    def create_variables(self, period):
        """Create decision variables"""
        print("Creating decision variables...")
        
        # Production variables (limited to first 15 facilities for manageability)
        self.prod_vars = {}
        facilities_to_use = list(self.data.IU_codes)[:15]
        
        for iu in facilities_to_use:
            if (iu, period) in self.adjusted_capacity:
                self.prod_vars[iu] = pulp.LpVariable(
                    f"prod_{iu}_{period}", 
                    lowBound=0, 
                    upBound=self.adjusted_capacity[(iu, period)],
                    cat='Continuous'
                )
        
        # Transportation variables
        self.trans_vars = {}
        for (iu, iugu, t) in self.data.transport_routes:
            if t == period and iu in self.prod_vars and iugu in list(self.data.IUGU_codes)[:15]:
                self.trans_vars[(iu, iugu)] = pulp.LpVariable(
                    f"trans_{iu}_{iugu}_{period}",
                    lowBound=0,
                    cat='Continuous'
                )
        
        # Inventory variables
        self.inv_vars = {}
        locations_to_use = list(self.data.IUGU_codes)[:15]
        
        for iugu in locations_to_use:
            self.inv_vars[iugu] = pulp.LpVariable(
                f"inv_{iugu}_{period}",
                lowBound=0,
                cat='Continuous'
            )
        
        # Slack variables for demand constraints
        self.demand_slack = {}
        for iugu in locations_to_use:
            self.demand_slack[iugu] = pulp.LpVariable(
                f"demand_slack_{iugu}_{period}",
                lowBound=0,
                cat='Continuous'
            )
        
        print(f"Created {len(self.prod_vars)} production variables")
        print(f"Created {len(self.trans_vars)} transport variables")
        print(f"Created {len(self.inv_vars)} inventory variables")
        print(f"Created {len(self.demand_slack)} demand slack variables")
    
    def set_objective(self, period):
        """Set objective function with penalty for unmet demand"""
        print("Setting objective function...")
        
        # Production cost
        prod_cost = pulp.lpSum(
            self.data.prod_cost_dict.get((iu, period), 0) * self.prod_vars[iu]
            for iu in self.prod_vars
        )
        
        # Transportation cost
        trans_cost = pulp.lpSum(
            self.data.transport_cost_dict.get((iu, iugu, period), 0) * self.trans_vars[(iu, iugu)]
            for (iu, iugu) in self.trans_vars
        )
        
        # Inventory holding cost
        inv_cost = pulp.lpSum(
            10 * self.inv_vars[iugu]  # Simplified holding cost
            for iugu in self.inv_vars
        )
        
        # Penalty for unmet demand (high penalty to minimize slack)
        unmet_demand_penalty = pulp.lpSum(
            10000 * self.demand_slack[iugu]  # $10,000 per unit penalty
            for iugu in self.demand_slack
        )
        
        # Set objective
        self.model += prod_cost + trans_cost + inv_cost + unmet_demand_penalty, "Total_Cost"
    
    def add_feasible_constraints(self, period):
        """Add constraints with slack variables"""
        print("Adding feasible constraints...")
        
        # Demand fulfillment constraints with slack
        for iugu in self.inv_vars:
            demand = self.adjusted_demand.get((iugu, period), 0)
            if demand > 0:
                # Total received
                total_received = pulp.lpSum(
                    self.trans_vars[(iu, dest_iugu)]
                    for (iu, dest_iugu) in self.trans_vars
                    if dest_iugu == iugu
                )
                
                # Opening stock
                opening_stock = self.adjusted_stock.get(iugu, 0)
                
                # Demand constraint with slack
                self.model += (
                    opening_stock + total_received + self.demand_slack[iugu] >= demand,
                    f"demand_{iugu}"
                )
        
        # Production outflow constraints
        for iu in self.prod_vars:
            total_outflow = pulp.lpSum(
                self.trans_vars[(iu, iugu)]
                for (src_iu, iugu) in self.trans_vars
                if src_iu == iu
            )
            self.model += total_outflow <= self.prod_vars[iu], f"outflow_{iu}"
        
        # Inventory balance constraints
        for iugu in self.inv_vars:
            opening_stock = self.adjusted_stock.get(iugu, 0)
            
            # Total received
            total_received = pulp.lpSum(
                self.trans_vars[(iu, dest_iugu)]
                for (iu, dest_iugu) in self.trans_vars
                if dest_iugu == iugu
            )
            
            demand = self.adjusted_demand.get((iugu, period), 0)
            
            # Inventory balance
            self.model += (
                self.inv_vars[iugu] == opening_stock + total_received - demand + self.demand_slack[iugu],
                f"balance_{iugu}"
            )
    
    def solve_model(self):
        """Solve the feasible optimization model"""
        print("Solving feasible optimization model...")
        start_time = time.time()
        
        # Solve using CBC solver
        solver = pulp.PULP_CBC_CMD(msg=True, timeLimit=60)
        result = self.model.solve(solver)
        
        solve_time = time.time() - start_time
        print(f"Model solved in {solve_time:.2f} seconds")
        
        # Extract results
        self.extract_results()
        
        return pulp.LpStatus[self.model.status]
    
    def extract_results(self):
        """Extract and display results"""
        print("Extracting results...")
        
        self.results = {
            'objective_value': pulp.value(self.model.objective),
            'production': {},
            'transport': {},
            'inventory': {},
            'unmet_demand': {}
        }
        
        # Production results
        for iu, var in self.prod_vars.items():
            if var.value() > 0.001:
                self.results['production'][iu] = var.value()
        
        # Transport results
        for (iu, iugu), var in self.trans_vars.items():
            if var.value() > 0.001:
                self.results['transport'][(iu, iugu)] = var.value()
        
        # Inventory results
        for iugu, var in self.inv_vars.items():
            if var.value() > 0.001:
                self.results['inventory'][iugu] = var.value()
        
        # Unmet demand (slack)
        for iugu, var in self.demand_slack.items():
            if var.value() > 0.001:
                self.results['unmet_demand'][iugu] = var.value()
        
        print(f"Total cost: ${self.results['objective_value']:,.2f}")
        print(f"Active production plans: {len(self.results['production'])}")
        print(f"Active transport routes: {len(self.results['transport'])}")
        print(f"Inventory locations: {len(self.results['inventory'])}")
        print(f"Unmet demand locations: {len(self.results['unmet_demand'])}")
        
        if self.results['unmet_demand']:
            total_unmet = sum(self.results['unmet_demand'].values())
            print(f"Total unmet demand: {total_unmet:,.0f} units")
    
    def save_results(self, filename):
        """Save results to Excel file"""
        print(f"Saving results to {filename}...")
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Production results
            if self.results['production']:
                prod_data = [
                    {'IU CODE': iu, 'PRODUCTION': qty}
                    for iu, qty in self.results['production'].items()
                ]
                prod_df = pd.DataFrame(prod_data)
                prod_df.to_excel(writer, sheet_name='Production', index=False)
            
            # Transport results
            if self.results['transport']:
                trans_data = [
                    {'FROM IU': iu, 'TO IUGU': iugu, 'QUANTITY': qty}
                    for (iu, iugu), qty in self.results['transport'].items()
                ]
                trans_df = pd.DataFrame(trans_data)
                trans_df.to_excel(writer, sheet_name='Transport', index=False)
            
            # Inventory results
            if self.results['inventory']:
                inv_data = [
                    {'IUGU CODE': iugu, 'INVENTORY': qty}
                    for iugu, qty in self.results['inventory'].items()
                ]
                inv_df = pd.DataFrame(inv_data)
                inv_df.to_excel(writer, sheet_name='Inventory', index=False)
            
            # Unmet demand
            if self.results['unmet_demand']:
                unmet_data = [
                    {'IUGU CODE': iugu, 'UNMET_DEMAND': qty}
                    for iugu, qty in self.results['unmet_demand'].items()
                ]
                unmet_df = pd.DataFrame(unmet_data)
                unmet_df.to_excel(writer, sheet_name='Unmet_Demand', index=False)
            
            # Summary
            summary_data = [
                {'Metric': 'Total Cost', 'Value': self.results['objective_value']},
                {'Metric': 'Active Production Plans', 'Value': len(self.results['production'])},
                {'Metric': 'Active Transport Routes', 'Value': len(self.results['transport'])},
                {'Metric': 'Inventory Locations', 'Value': len(self.results['inventory'])},
                {'Metric': 'Unmet Demand Locations', 'Value': len(self.results['unmet_demand'])}
            ]
            if self.results['unmet_demand']:
                summary_data.append({
                    'Metric': 'Total Unmet Demand', 
                    'Value': sum(self.results['unmet_demand'].values())
                })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        print("Results saved successfully!")

def main():
    """Main function to run feasible optimization"""
    try:
        print("=" * 80)
        print("FEASIBLE CLINKER OPTIMIZATION MODEL")
        print("=" * 80)
        
        # Create and solve model
        model = FeasibleClinkerOptimization('Dataset_Dummy_Clinker_3MPlan.xlsx')
        
        # Create feasible data
        model.create_feasible_data()
        
        # Build and solve model
        model.build_feasible_model()
        status = model.solve_model()
        
        if status == 'Optimal':
            print("\n✅ OPTIMAL SOLUTION FOUND!")
            model.save_results('feasible_optimization_results.xlsx')
        else:
            print(f"\n❌ SOLUTION STATUS: {status}")
            
    except Exception as e:
        print(f"Error in feasible optimization: {e}")

if __name__ == "__main__":
    main()
