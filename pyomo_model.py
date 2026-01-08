"""
PYOMO OPTIMIZATION MODEL FOR CLINKER SUPPLY CHAIN

This model solves the multi-period clinker production and distribution problem
using Pyomo optimization framework to minimize total costs while satisfying all constraints.
"""

import pyomo.environ as pyo
from pyomo.opt import SolverFactory
import pandas as pd
from optimization_formulation import ClinkerOptimizationData
import time

class ClinkerPyomoModel:
    def __init__(self, data_file):
        self.data = ClinkerOptimizationData(data_file)
        self.model = None
        self.results = {}
        
    def build_model(self):
        """Build the Pyomo optimization model"""
        print("Building Pyomo model...")
        start_time = time.time()
        
        # Create concrete model
        self.model = pyo.ConcreteModel("Clinker_Supply_Chain")
        
        # Define sets
        self.define_sets()
        
        # Create decision variables
        self.create_variables()
        
        # Set objective function
        self.set_objective()
        
        # Add constraints
        self.add_constraints()
        
        build_time = time.time() - start_time
        print(f"Model built in {build_time:.2f} seconds")
        
    def define_sets(self):
        """Define model sets"""
        self.model.IU = pyo.Set(initialize=self.data.IU_codes)
        self.model.IUGU = pyo.Set(initialize=self.data.IUGU_codes)
        self.model.T = pyo.Set(initialize=self.data.periods)
        
        # Transport routes set
        transport_routes = [(iu, iugu, t) for (iu, iugu, t) in self.data.transport_routes]
        self.model.TransportRoutes = pyo.Set(initialize=transport_routes, dimen=3)
        
    def create_variables(self):
        """Create decision variables"""
        print("Creating variables...")
        
        # Production variables: x[i,t] - production at IU i in period t
        def production_bounds(model, iu, t):
            capacity = self.data.capacity_dict.get((iu, t), 0)
            return (0, capacity)
        
        self.model.x = pyo.Var(self.model.IU, self.model.T, bounds=production_bounds, 
                               domain=pyo.NonNegativeReals, doc="Production quantity")
        
        # Transportation variables: y[i,j,t] - shipment from IU i to IUGU j in period t
        self.model.y = pyo.Var(self.model.TransportRoutes, domain=pyo.NonNegativeReals,
                               doc="Transportation quantity")
        
        # Inventory variables: s[j,t] - inventory at IUGU j at end of period t
        self.model.s = pyo.Var(self.model.IUGU, self.model.T, domain=pyo.NonNegativeReals,
                               doc="Inventory level")
        
        print(f"Created {len(self.model.IU) * len(self.model.T)} production variables")
        print(f"Created {len(self.model.TransportRoutes)} transport variables")
        print(f"Created {len(self.model.IUGU) * len(self.model.T)} inventory variables")
        
    def set_objective(self):
        """Set the objective function to minimize total cost"""
        print("Setting objective function...")
        
        def total_cost_rule(model):
            # Production cost
            prod_cost = sum(
                self.data.prod_cost_dict.get((iu, t), 0) * model.x[iu, t]
                for iu in model.IU for t in model.T
            )
            
            # Transportation cost
            trans_cost = sum(
                self.data.transport_cost_dict.get((iu, iugu, t), 0) * model.y[iu, iugu, t]
                for (iu, iugu, t) in model.TransportRoutes
            )
            
            # Inventory holding cost (simplified)
            inv_cost = sum(
                10 * model.s[iugu, t]  # Simplified holding cost
                for iugu in model.IUGU for t in model.T
            )
            
            return prod_cost + trans_cost + inv_cost
        
        self.model.total_cost = pyo.Objective(rule=total_cost_rule, sense=pyo.minimize)
        
    def add_constraints(self):
        """Add all constraints to the model"""
        print("Adding constraints...")
        
        # 1. Production capacity constraints (handled by variable bounds)
        
        # 2. Demand fulfillment constraints
        self.add_demand_constraints()
        
        # 3. Flow balance constraints
        self.add_flow_balance_constraints()
        
        # 4. Inventory constraints
        self.add_inventory_constraints()
        
        # 5. Transportation capacity constraints
        self.add_transport_constraints()
        
    def add_demand_constraints(self):
        """Add demand fulfillment constraints"""
        def demand_rule(model, iugu, t):
            # Total received in period t
            total_received = sum(
                model.y[iu, iugu, t]
                for (iu, dest_iugu, period) in model.TransportRoutes
                if dest_iugu == iugu and period == t
            )
            
            demand = self.data.demand_dict.get((iugu, t), 0)
            
            # For first period, include opening stock
            if t == min(model.T):
                opening_stock = self.data.opening_stock_dict.get(iugu, 0)
                return opening_stock + total_received >= demand
            else:
                # For subsequent periods, include inventory from previous period
                prev_t = [period for period in model.T if period < t]
                if prev_t:
                    max_prev_t = max(prev_t)
                    return model.s[iugu, max_prev_t] + total_received >= demand
                else:
                    return total_received >= demand
        
        self.model.demand_constraint = pyo.Constraint(
            self.model.IUGU, self.model.T, rule=demand_rule
        )
        
    def add_flow_balance_constraints(self):
        """Add flow balance constraints for inventory"""
        def inventory_balance_rule(model, iugu, t):
            # Inventory balance: closing = opening + received - consumed
            opening = 0
            if t == min(model.T):
                opening = self.data.opening_stock_dict.get(iugu, 0)
            else:
                prev_t = [period for period in model.T if period < t]
                if prev_t:
                    max_prev_t = max(prev_t)
                    opening = model.s[iugu, max_prev_t]
            
            # Total received in period t
            received = sum(
                model.y[iu, iugu, t]
                for (iu, dest_iugu, period) in model.TransportRoutes
                if dest_iugu == iugu and period == t
            )
            
            # Demand in period t
            demand = self.data.demand_dict.get((iugu, t), 0)
            
            return model.s[iugu, t] == opening + received - demand
        
        self.model.inventory_balance = pyo.Constraint(
            self.model.IUGU, self.model.T, rule=inventory_balance_rule
        )
        
    def add_inventory_constraints(self):
        """Add inventory level constraints"""
        def inventory_min_rule(model, iugu, t):
            min_stock = self.data.closing_stock_dict.get((iugu, t, 'min'), 0)
            return model.s[iugu, t] >= min_stock
        
        def inventory_max_rule(model, iugu, t):
            max_stock = self.data.closing_stock_dict.get((iugu, t, 'max'), float('inf'))
            return model.s[iugu, t] <= max_stock
        
        # Only add constraints where they exist
        min_constraints = []
        max_constraints = []
        
        for (iugu, t, bound_type) in self.data.closing_stock_dict.keys():
            if bound_type == 'min':
                min_constraints.append((iugu, t))
            elif bound_type == 'max':
                max_constraints.append((iugu, t))
        
        if min_constraints:
            self.model.inventory_min = pyo.Constraint(
                min_constraints, rule=inventory_min_rule
            )
        
        if max_constraints:
            self.model.inventory_max = pyo.Constraint(
                max_constraints, rule=inventory_max_rule
            )
        
    def add_transport_constraints(self):
        """Add transportation constraints"""
        def transport_capacity_rule(model, iu, t):
            # Production outflow constraint
            total_outflow = sum(
                model.y[iu, iugu, t]
                for (src_iu, iugu, period) in model.TransportRoutes
                if src_iu == iu and period == t
            )
            return total_outflow <= model.x[iu, t]
        
        # Only add for IU-T combinations that have production capacity
        transport_combinations = set()
        for (iu, t) in self.data.capacity_dict.keys():
            # Check if there are any transport routes from this IU in this period
            has_routes = any(
                route_iu == iu and route_t == t 
                for (route_iu, route_iugu, route_t) in self.model.TransportRoutes
            )
            if has_routes:
                transport_combinations.add((iu, t))
        
        if transport_combinations:
            self.model.transport_capacity = pyo.Constraint(
                transport_combinations, rule=transport_capacity_rule
            )
    
    def solve(self, solver_name='glpk'):
        """Solve the optimization model"""
        print(f"Solving model with {solver_name}...")
        start_time = time.time()
        
        # Create solver
        solver = SolverFactory(solver_name)
        
        # Set solver options
        if solver_name == 'glpk':
            solver.options['tmlim'] = 300  # 5 minutes time limit
        elif solver_name == 'cbc':
            solver.options['seconds'] = 300
        
        # Solve
        results = solver.solve(self.model, tee=True)
        
        solve_time = time.time() - start_time
        print(f"Model solved in {solve_time:.2f} seconds")
        
        # Store results
        self.extract_results()
        
        return results.solver.status
    
    def extract_results(self):
        """Extract and store results"""
        print("Extracting results...")
        
        self.results = {
            'objective_value': pyo.value(self.model.total_cost),
            'production': {},
            'transport': {},
            'inventory': {}
        }
        
        # Production results
        for iu in self.model.IU:
            for t in self.model.T:
                value = pyo.value(self.model.x[iu, t])
                if value and value > 0.001:  # Only store non-zero values
                    self.results['production'][(iu, t)] = value
        
        # Transport results
        for (iu, iugu, t) in self.model.TransportRoutes:
            value = pyo.value(self.model.y[iu, iugu, t])
            if value and value > 0.001:  # Only store non-zero values
                self.results['transport'][(iu, iugu, t)] = value
        
        # Inventory results
        for iugu in self.model.IUGU:
            for t in self.model.T:
                value = pyo.value(self.model.s[iugu, t])
                if value and value > 0.001:  # Only store non-zero values
                    self.results['inventory'][(iugu, t)] = value
        
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
            summary_data = [
                {'Metric': 'Total Cost', 'Value': self.results['objective_value']},
                {'Metric': 'Active Production Plans', 'Value': len(self.results['production'])},
                {'Metric': 'Active Transport Routes', 'Value': len(self.results['transport'])},
                {'Metric': 'Inventory Locations', 'Value': len(self.results['inventory'])}
            ]
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        print("Results saved successfully!")
    
    def print_model_info(self):
        """Print model information"""
        print("\n=== MODEL INFORMATION ===")
        print(f"Variables: {self.model.nvariables()}")
        print(f"Constraints: {self.model.nconstraints()}")
        print(f"Objective: {self.model.total_cost.expr}")

def main():
    """Main function to run the Pyomo model"""
    try:
        # Create and solve model
        model = ClinkerPyomoModel('Dataset_Dummy_Clinker_3MPlan.xlsx')
        model.build_model()
        model.print_model_info()
        
        # Try different solvers
        solvers = ['glpk', 'cbc']
        status = None
        
        for solver in solvers:
            try:
                print(f"\n=== Trying solver: {solver} ===")
                status = model.solve(solver_name=solver)
                if status == pyo.SolverStatus.ok:
                    print("\n=== OPTIMAL SOLUTION FOUND ===")
                    model.save_results('pyomo_results.xlsx')
                    break
            except Exception as e:
                print(f"Solver {solver} failed: {e}")
                continue
        
        if status != pyo.SolverStatus.ok:
            print("\n=== NO OPTIMAL SOLUTION FOUND ===")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
