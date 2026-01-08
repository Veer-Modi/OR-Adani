"""
PULP SIMPLIFIED OPTIMIZATION MODEL FOR CLINKER SUPPLY CHAIN

This is a simplified version using PuLP for demonstration purposes.
It solves a reduced version of the clinker production and distribution problem.
"""

import pulp
import pandas as pd
from optimization_formulation import ClinkerOptimizationData
import time

class ClinkerPulpModel:
    def __init__(self, data_file):
        self.data = ClinkerOptimizationData(data_file)
        self.model = None
        self.results = {}
        
    def build_simplified_model(self):
        """Build a simplified version for demonstration"""
        print("Building simplified PuLP model...")
        start_time = time.time()
        
        # Create model
        self.model = pulp.LpProblem("Clinker_Supply_Chain_Simplified", pulp.LpMinimize)
        
        # Use only first period for simplification
        period = min(self.data.periods)
        
        # Create simplified decision variables
        self.create_simplified_variables(period)
        
        # Set objective
        self.set_simplified_objective(period)
        
        # Add simplified constraints
        self.add_simplified_constraints(period)
        
        build_time = time.time() - start_time
        print(f"Simplified model built in {build_time:.2f} seconds")
        
    def create_simplified_variables(self, period):
        """Create simplified decision variables for first period only"""
        print("Creating simplified variables...")
        
        # Production variables for first period only
        self.prod_vars = {}
        for iu in self.data.IU_codes[:10]:  # Limit to first 10 IUs for simplicity
            if (iu, period) in self.data.capacity_dict:
                self.prod_vars[iu] = pulp.LpVariable(
                    f"prod_{iu}_{period}", 
                    lowBound=0, 
                    upBound=self.data.capacity_dict[(iu, period)],
                    cat='Continuous'
                )
        
        # Transport variables for first period only
        self.trans_vars = {}
        for (iu, iugu, t) in self.data.transport_routes:
            if t == period and iu in self.prod_vars:
                self.trans_vars[(iu, iugu)] = pulp.LpVariable(
                    f"trans_{iu}_{iugu}_{period}",
                    lowBound=0,
                    cat='Continuous'
                )
        
        print(f"Created {len(self.prod_vars)} production variables")
        print(f"Created {len(self.trans_vars)} transport variables")
        
    def set_simplified_objective(self, period):
        """Set simplified objective function"""
        print("Setting simplified objective...")
        
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
        
        # Set objective
        self.model += prod_cost + trans_cost, "Total_Cost"
        
    def add_simplified_constraints(self, period):
        """Add simplified constraints"""
        print("Adding simplified constraints...")
        
        # Demand fulfillment for first 10 IUGUs
        for iugu in self.data.IUGU_codes[:10]:
            demand = self.data.demand_dict.get((iugu, period), 0)
            if demand > 0:
                # Total received
                total_received = pulp.lpSum(
                    self.trans_vars[(iu, iugu)]
                    for (iu, dest_iugu) in self.trans_vars
                    if dest_iugu == iugu
                )
                
                # Opening stock
                opening_stock = self.data.opening_stock_dict.get(iugu, 0)
                
                # Demand constraint
                self.model += opening_stock + total_received >= demand, f"demand_{iugu}"
        
        # Production outflow constraints
        for iu in self.prod_vars:
            total_outflow = pulp.lpSum(
                self.trans_vars[(iu, iugu)]
                for (src_iu, iugu) in self.trans_vars
                if src_iu == iu
            )
            self.model += total_outflow <= self.prod_vars[iu], f"outflow_{iu}"
    
    def solve(self):
        """Solve the simplified model"""
        print("Solving simplified model...")
        start_time = time.time()
        
        # Solve using default CBC solver
        self.model.solve(pulp.PULP_CBC_CMD(msg=True))
        
        solve_time = time.time() - start_time
        print(f"Model solved in {solve_time:.2f} seconds")
        
        # Extract results
        self.extract_simplified_results()
        
        return pulp.LpStatus[self.model.status]
    
    def extract_simplified_results(self):
        """Extract simplified results"""
        print("Extracting results...")
        
        self.results = {
            'objective_value': pulp.value(self.model.objective),
            'production': {},
            'transport': {}
        }
        
        # Production results
        for iu, var in self.prod_vars.items():
            if var.value() > 0.001:
                self.results['production'][iu] = var.value()
        
        # Transport results
        for (iu, iugu), var in self.trans_vars.items():
            if var.value() > 0.001:
                self.results['transport'][(iu, iugu)] = var.value()
        
        print(f"Total cost: ${self.results['objective_value']:,.2f}")
        print(f"Active production plans: {len(self.results['production'])}")
        print(f"Active transport routes: {len(self.results['transport'])}")
    
    def save_results(self, filename):
        """Save simplified results to Excel"""
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
            
            # Summary
            summary_data = [
                {'Metric': 'Total Cost', 'Value': self.results['objective_value']},
                {'Metric': 'Active Production Plans', 'Value': len(self.results['production'])},
                {'Metric': 'Active Transport Routes', 'Value': len(self.results['transport'])}
            ]
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        print("Results saved successfully!")

def main():
    """Main function to run the simplified PuLP model"""
    try:
        # Create and solve simplified model
        model = ClinkerPulpModel('Dataset_Dummy_Clinker_3MPlan.xlsx')
        model.build_simplified_model()
        
        status = model.solve()
        
        if status == 'Optimal':
            print("\n=== OPTIMAL SOLUTION FOUND ===")
            model.save_results('pulp_simplified_results.xlsx')
        else:
            print(f"\n=== SOLUTION STATUS: {status} ===")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
