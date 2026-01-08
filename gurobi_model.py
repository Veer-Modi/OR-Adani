"""
GUROBI OPTIMIZATION MODEL FOR CLINKER SUPPLY CHAIN

This model solves the multi-period clinker production and distribution problem
using Gurobi optimizer to minimize total costs while satisfying all constraints.
"""

import gurobipy as gp
from gurobipy import GRB
import pandas as pd
from optimization_formulation import ClinkerOptimizationData
import time

class ClinkerGurobiModel:
    def __init__(self, data_file):
        self.data = ClinkerOptimizationData(data_file)
        self.model = None
        self.variables = {}
        self.results = {}
        
    def build_model(self):
        """Build the Gurobi optimization model"""
        print("Building Gurobi model...")
        start_time = time.time()
        
        # Create model
        self.model = gp.Model("Clinker_Supply_Chain")
        
        # Create decision variables
        self.create_variables()
        
        # Set objective function
        self.set_objective()
        
        # Add constraints
        self.add_constraints()
        
        build_time = time.time() - start_time
        print(f"Model built in {build_time:.2f} seconds")
        
    def create_variables(self):
        """Create decision variables"""
        print("Creating variables...")
        
        # Production variables: x[i,t] - production at IU i in period t
        self.variables['production'] = {}
        for iu in self.data.IU_codes:
            for t in self.data.periods:
                self.variables['production'][(iu, t)] = self.model.addVar(
                    lb=0, name=f"prod_{iu}_{t}"
                )
        
        # Transportation variables: y[i,j,t] - shipment from IU i to IUGU j in period t
        self.variables['transport'] = {}
        for (iu, iugu, t) in self.data.transport_routes:
            self.variables['transport'][(iu, iugu, t)] = self.model.addVar(
                lb=0, name=f"trans_{iu}_{iugu}_{t}"
            )
        
        # Inventory variables: s[j,t] - inventory at IUGU j at end of period t
        self.variables['inventory'] = {}
        for iugu in self.data.IUGU_codes:
            for t in self.data.periods:
                self.variables['inventory'][(iugu, t)] = self.model.addVar(
                    lb=0, name=f"inv_{iugu}_{t}"
                )
        
        # Update model
        self.model.update()
        
        print(f"Created {len(self.variables['production'])} production variables")
        print(f"Created {len(self.variables['transport'])} transport variables")
        print(f"Created {len(self.variables['inventory'])} inventory variables")
        
    def set_objective(self):
        """Set the objective function to minimize total cost"""
        print("Setting objective function...")
        
        # Production cost
        prod_cost = 0
        for (iu, t), var in self.variables['production'].items():
            if (iu, t) in self.data.prod_cost_dict:
                cost = self.data.prod_cost_dict[(iu, t)]
                prod_cost += cost * var
        
        # Transportation cost
        trans_cost = 0
        for (iu, iugu, t), var in self.variables['transport'].items():
            if (iu, iugu, t) in self.data.transport_cost_dict:
                cost = self.data.transport_cost_dict[(iu, iugu, t)]
                trans_cost += cost * var
        
        # Inventory holding cost (assuming 1% of value per period as holding cost)
        inv_cost = 0
        for (iugu, t), var in self.variables['inventory'].items():
            inv_cost += 10 * var  # Simplified holding cost
        
        # Set objective
        self.model.setObjective(prod_cost + trans_cost + inv_cost, GRB.MINIMIZE)
        
    def add_constraints(self):
        """Add all constraints to the model"""
        print("Adding constraints...")
        
        # 1. Production capacity constraints
        self.add_production_capacity_constraints()
        
        # 2. Demand fulfillment constraints
        self.add_demand_constraints()
        
        # 3. Flow balance constraints
        self.add_flow_balance_constraints()
        
        # 4. Inventory constraints
        self.add_inventory_constraints()
        
        # 5. Transportation capacity constraints
        self.add_transport_constraints()
        
    def add_production_capacity_constraints(self):
        """Add production capacity constraints"""
        for (iu, t), capacity in self.data.capacity_dict.items():
            if (iu, t) in self.variables['production']:
                self.model.addConstr(
                    self.variables['production'][(iu, t)] <= capacity,
                    name=f"cap_{iu}_{t}"
                )
        
    def add_demand_constraints(self):
        """Add demand fulfillment constraints"""
        for (iugu, t), demand in self.data.demand_dict.items():
            # Total received = demand (assuming no backlogging)
            total_received = 0
            for (iu, dest_iugu, period), var in self.variables['transport'].items():
                if dest_iugu == iugu and period == t:
                    total_received += var
            
            # For first period, include opening stock
            if t == min(self.data.periods):
                opening_stock = self.data.opening_stock_dict.get(iugu, 0)
                self.model.addConstr(
                    opening_stock + total_received >= demand,
                    name=f"demand_{iugu}_{t}"
                )
            else:
                # For subsequent periods, include inventory from previous period
                prev_t = t - 1
                if (iugu, prev_t) in self.variables['inventory']:
                    self.model.addConstr(
                        self.variables['inventory'][(iugu, prev_t)] + total_received >= demand,
                        name=f"demand_{iugu}_{t}"
                    )
    
    def add_flow_balance_constraints(self):
        """Add flow balance constraints for inventory"""
        for iugu in self.data.IUGU_codes:
            for t in self.data.periods:
                # Inventory balance: closing = opening + received - consumed
                opening = 0
                if t == min(self.data.periods):
                    opening = self.data.opening_stock_dict.get(iugu, 0)
                else:
                    prev_t = t - 1
                    if (iugu, prev_t) in self.variables['inventory']:
                        opening = self.variables['inventory'][(iugu, prev_t)]
                
                # Total received in period t
                received = 0
                for (iu, dest_iugu, period), var in self.variables['transport'].items():
                    if dest_iugu == iugu and period == t:
                        received += var
                
                # Demand in period t
                demand = self.data.demand_dict.get((iugu, t), 0)
                
                # Inventory balance constraint
                if (iugu, t) in self.variables['inventory']:
                    self.model.addConstr(
                        self.variables['inventory'][(iugu, t)] == opening + received - demand,
                        name=f"balance_{iugu}_{t}"
                    )
    
    def add_inventory_constraints(self):
        """Add inventory level constraints"""
        for (iugu, t, bound_type), value in self.data.closing_stock_dict.items():
            if (iugu, t) in self.variables['inventory']:
                if bound_type == 'min':
                    self.model.addConstr(
                        self.variables['inventory'][(iugu, t)] >= value,
                        name=f"min_inv_{iugu}_{t}"
                    )
                elif bound_type == 'max':
                    self.model.addConstr(
                        self.variables['inventory'][(iugu, t)] <= value,
                        name=f"max_inv_{iugu}_{t}"
                    )
    
    def add_transport_constraints(self):
        """Add transportation constraints"""
        # Production outflow constraint
        for iu in self.data.IU_codes:
            for t in self.data.periods:
                if (iu, t) in self.variables['production']:
                    total_outflow = 0
                    for (src_iu, iugu, period), var in self.variables['transport'].items():
                        if src_iu == iu and period == t:
                            total_outflow += var
                    
                    self.model.addConstr(
                        total_outflow <= self.variables['production'][(iu, t)],
                        name=f"outflow_{iu}_{t}"
                    )
    
    def solve(self):
        """Solve the optimization model"""
        print("Solving model...")
        start_time = time.time()
        
        # Set solver parameters
        self.model.setParam('TimeLimit', 300)  # 5 minutes
        self.model.setParam('OutputFlag', 1)
        
        # Solve
        self.model.optimize()
        
        solve_time = time.time() - start_time
        print(f"Model solved in {solve_time:.2f} seconds")
        
        # Store results
        self.extract_results()
        
        return self.model.status
    
    def extract_results(self):
        """Extract and store results"""
        print("Extracting results...")
        
        self.results = {
            'objective_value': self.model.objVal,
            'production': {},
            'transport': {},
            'inventory': {}
        }
        
        # Production results
        for (iu, t), var in self.variables['production'].items():
            if var.X > 0.001:  # Only store non-zero values
                self.results['production'][(iu, t)] = var.X
        
        # Transport results
        for (iu, iugu, t), var in self.variables['transport'].items():
            if var.X > 0.001:  # Only store non-zero values
                self.results['transport'][(iu, iugu, t)] = var.X
        
        # Inventory results
        for (iugu, t), var in self.variables['inventory'].items():
            if var.X > 0.001:  # Only store non-zero values
                self.results['inventory'][(iugu, t)] = var.X
        
        print(f"Total cost: ${self.results['objective_value']:,.2f}")
        print(f"Active production plans: {len(self.results['production'])}")
        print(f"Active transport routes: {len(self.results['transport'])}")
        print(f"Inventory locations: {len(self.results['inventory'])}")
    
    def save_results(self, filename):
        """Save results to Excel file"""
        print(f"Saving results to {filename}...")
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Production results
            if self.results['production']:
                prod_data = []
                for (iu, t), qty in self.results['production'].items():
                    prod_data.append({'IU CODE': iu, 'TIME PERIOD': t, 'PRODUCTION': qty})
                prod_df = pd.DataFrame(prod_data)
                prod_df.to_excel(writer, sheet_name='Production', index=False)
            
            # Transport results
            if self.results['transport']:
                trans_data = []
                for (iu, iugu, t), qty in self.results['transport'].items():
                    trans_data.append({
                        'FROM IU': iu, 'TO IUGU': iugu, 'TIME PERIOD': t, 'QUANTITY': qty
                    })
                trans_df = pd.DataFrame(trans_data)
                trans_df.to_excel(writer, sheet_name='Transport', index=False)
            
            # Inventory results
            if self.results['inventory']:
                inv_data = []
                for (iugu, t), qty in self.results['inventory'].items():
                    inv_data.append({'IUGU CODE': iugu, 'TIME PERIOD': t, 'INVENTORY': qty})
                inv_df = pd.DataFrame(inv_data)
                inv_df.to_excel(writer, sheet_name='Inventory', index=False)
            
            # Summary
            summary_data = [{
                'Metric': 'Total Cost',
                'Value': self.results['objective_value']
            }]
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        print("Results saved successfully!")

def main():
    """Main function to run the Gurobi model"""
    try:
        # Create and solve model
        model = ClinkerGurobiModel('Dataset_Dummy_Clinker_3MPlan.xlsx')
        model.build_model()
        
        status = model.solve()
        
        if status == GRB.OPTIMAL:
            print("\n=== OPTIMAL SOLUTION FOUND ===")
            model.save_results('gurobi_results.xlsx')
        elif status == GRB.TIME_LIMIT:
            print("\n=== TIME LIMIT REACHED ===")
            model.save_results('gurobi_results_time_limit.xlsx')
        else:
            print(f"\n=== SOLUTION STATUS: {status} ===")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
