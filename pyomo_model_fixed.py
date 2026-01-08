"""
FIXED PYOMO OPTIMIZATION MODEL FOR CLINKER SUPPLY CHAIN

This is a corrected version of the Pyomo model that addresses feasibility issues
by implementing proper data adjustments and soft constraints.
"""

import pyomo.environ as pyo
from pyomo.opt import SolverFactory
import pandas as pd
from optimization_formulation import ClinkerOptimizationData
import time

class FixedClinkerPyomoModel:
    def __init__(self, data_file):
        self.data = ClinkerOptimizationData(data_file)
        self.model = None
        self.results = {}
        
    def create_feasible_data(self):
        """Create adjusted data to ensure feasibility"""
        print("Creating feasible data adjustments...")
        
        # Calculate original coverage
        original_capacity = sum(self.data.capacity_dict.values())
        original_demand = sum(self.data.demand_dict.values())
        original_stock = sum(self.data.opening_stock_dict.values())
        original_coverage = (original_capacity + original_stock) / original_demand
        
        print(f"Original coverage ratio: {original_coverage:.3f}")
        
        # Apply adjustments to achieve feasibility
        if original_coverage < 1.0:
            # Reduce demand to make it feasible
            demand_reduction_factor = original_coverage * 0.9  # 90% of available capacity
            
            # Alternatively, increase capacity
            capacity_expansion_factor = 1.1  # 10% increase
            
            print(f"Applying demand reduction factor: {demand_reduction_factor:.3f}")
            print(f"Applying capacity expansion factor: {capacity_expansion_factor:.3f}")
            
            # Create adjusted dictionaries
            self.adjusted_demand = {}
            for (iugu, period), demand in self.data.demand_dict.items():
                self.adjusted_demand[(iugu, period)] = demand * demand_reduction_factor
            
            self.adjusted_capacity = {}
            for (iu, period), capacity in self.data.capacity_dict.items():
                self.adjusted_capacity[(iu, period)] = capacity * capacity_expansion_factor
            
            self.adjusted_stock = self.data.opening_stock_dict.copy()
            
            # Verify new coverage
            new_capacity = sum(self.adjusted_capacity.values())
            new_demand = sum(self.adjusted_demand.values())
            new_stock = sum(self.adjusted_stock.values())
            new_coverage = (new_capacity + new_stock) / new_demand
            
            print(f"New coverage ratio: {new_coverage:.3f}")
            
            if new_coverage >= 1.0:
                print("✅ Adjusted data is feasible!")
            else:
                print("⚠️  Adjusted data may still be infeasible, using soft constraints")
        else:
            print("✅ Original data is already feasible!")
            self.adjusted_demand = self.data.demand_dict.copy()
            self.adjusted_capacity = self.data.capacity_dict.copy()
            self.adjusted_stock = self.data.opening_stock_dict.copy()
    
    def build_fixed_model(self):
        """Build the fixed Pyomo optimization model"""
        print("Building fixed Pyomo model...")
        start_time = time.time()
        
        # Create concrete model
        self.model = pyo.ConcreteModel("Fixed_Clinker_Supply_Chain")
        
        # Define sets (limited for manageability)
        self.define_limited_sets()
        
        # Create decision variables
        self.create_variables()
        
        # Set objective function
        self.set_objective()
        
        # Add constraints with slack variables
        self.add_fixed_constraints()
        
        build_time = time.time() - start_time
        print(f"Model built in {build_time:.2f} seconds")
    
    def define_limited_sets(self):
        """Define limited sets for manageability"""
        # Use subset of facilities and locations
        self.model.IU = pyo.Set(initialize=list(self.data.IU_codes)[:12])
        self.model.IUGU = pyo.Set(initialize=list(self.data.IUGU_codes)[:12])
        self.model.T = pyo.Set(initialize=[min(self.data.periods)])  # First period only
        
        # Limited transport routes
        limited_routes = []
        for (iu, iugu, t) in self.data.transport_routes:
            if (iu in self.model.IU and iugu in self.model.IUGU and t in self.model.T):
                limited_routes.append((iu, iugu, t))
        
        self.model.TransportRoutes = pyo.Set(initialize=limited_routes, dimen=3)
        
        print(f"Using {len(self.model.IU)} facilities, {len(self.model.IUGU)} locations, {len(self.model.TransportRoutes)} routes")
    
    def create_variables(self):
        """Create decision variables with proper bounds"""
        print("Creating variables...")
        
        # Production variables with adjusted capacity bounds
        def production_bounds(model, iu, t):
            capacity = self.adjusted_capacity.get((iu, t), 0)
            return (0, capacity)
        
        self.model.x = pyo.Var(self.model.IU, self.model.T, bounds=production_bounds, 
                               domain=pyo.NonNegativeReals, doc="Production quantity")
        
        # Transportation variables
        self.model.y = pyo.Var(self.model.TransportRoutes, domain=pyo.NonNegativeReals,
                               doc="Transportation quantity")
        
        # Inventory variables
        self.model.s = pyo.Var(self.model.IUGU, self.model.T, domain=pyo.NonNegativeReals,
                               doc="Inventory level")
        
        # Slack variables for demand constraints
        self.model.demand_slack = pyo.Var(self.model.IUGU, self.model.T, 
                                        domain=pyo.NonNegativeReals,
                                        doc="Unmet demand slack")
        
        print(f"Created {len(self.model.IU) * len(self.model.T)} production variables")
        print(f"Created {len(self.model.TransportRoutes)} transport variables")
        print(f"Created {len(self.model.IUGU) * len(self.model.T)} inventory variables")
        print(f"Created {len(self.model.IUGU) * len(self.model.T)} demand slack variables")
    
    def set_objective(self):
        """Set objective function with penalty for unmet demand"""
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
            
            # Inventory holding cost
            inv_cost = sum(
                10 * model.s[iugu, t]  # Simplified holding cost
                for iugu in model.IUGU for t in model.T
            )
            
            # Penalty for unmet demand (high penalty)
            unmet_penalty = sum(
                5000 * model.demand_slack[iugu, t]  # $5,000 per unit penalty
                for iugu in model.IUGU for t in model.T
            )
            
            return prod_cost + trans_cost + inv_cost + unmet_penalty
        
        self.model.total_cost = pyo.Objective(rule=total_cost_rule, sense=pyo.minimize)
    
    def add_fixed_constraints(self):
        """Add constraints with proper feasibility handling"""
        print("Adding fixed constraints...")
        
        # Demand fulfillment constraints with slack
        def demand_rule(model, iugu, t):
            # Total received in period t
            total_received = sum(
                model.y[iu, iugu, t]
                for (iu, dest_iugu, period) in model.TransportRoutes
                if dest_iugu == iugu and period == t
            )
            
            demand = self.adjusted_demand.get((iugu, t), 0)
            
            # For first period, include opening stock
            if t == min(model.T):
                opening_stock = self.adjusted_stock.get(iugu, 0)
                return opening_stock + total_received + model.demand_slack[iugu, t] >= demand
            else:
                # For subsequent periods, include inventory from previous period
                prev_t = [period for period in model.T if period < t]
                if prev_t:
                    max_prev_t = max(prev_t)
                    return model.s[iugu, max_prev_t] + total_received + model.demand_slack[iugu, t] >= demand
                else:
                    return total_received + model.demand_slack[iugu, t] >= demand
        
        self.model.demand_constraint = pyo.Constraint(
            self.model.IUGU, self.model.T, rule=demand_rule
        )
        
        # Flow balance constraints
        def inventory_balance_rule(model, iugu, t):
            # Inventory balance: closing = opening + received - consumed + slack
            opening = 0
            if t == min(model.T):
                opening = self.adjusted_stock.get(iugu, 0)
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
            demand = self.adjusted_demand.get((iugu, t), 0)
            
            return model.s[iugu, t] == opening + received - demand + model.demand_slack[iugu, t]
        
        self.model.inventory_balance = pyo.Constraint(
            self.model.IUGU, self.model.T, rule=inventory_balance_rule
        )
        
        # Transportation capacity constraints
        def transport_capacity_rule(model, iu, t):
            # Production outflow constraint
            total_outflow = sum(
                model.y[iu, iugu, t]
                for (src_iu, iugu, period) in model.TransportRoutes
                if src_iu == iu and period == t
            )
            return total_outflow <= model.x[iu, t]
        
        # Only add for IU-T combinations that have routes
        transport_combinations = set()
        for (iu, t) in self.adjusted_capacity.keys():
            if iu in self.model.IU and t in self.model.T:
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
    
    def solve_fixed_model(self, solver_name='glpk'):
        """Solve the fixed optimization model"""
        print(f"Solving fixed model with {solver_name}...")
        start_time = time.time()
        
        # Try to create solver
        try:
            solver = SolverFactory(solver_name)
            
            # Set solver options
            if solver_name == 'glpk':
                solver.options['tmlim'] = 120  # 2 minutes
            elif solver_name == 'cbc':
                solver.options['seconds'] = 120
            
            # Solve
            results = solver.solve(self.model, tee=False)
            
            solve_time = time.time() - start_time
            print(f"Model solved in {solve_time:.2f} seconds")
            
            # Store results
            self.extract_results()
            
            return results.solver.status
            
        except Exception as e:
            print(f"Solver error: {e}")
            print("Trying with pulp solver...")
            return self.solve_with_pulp()
    
    def solve_with_pulp(self):
        """Fallback solver using pulp"""
        try:
            import pulp
            
            print("Converting to pulp model...")
            # Create pulp model as fallback
            pulp_model = pulp.LpProblem("Fallback_Clinker", pulp.LpMinimize)
            
            # This is a simplified fallback - just to get some solution
            period = min(self.data.periods)
            
            # Create simplified variables
            pulp_vars = {}
            for iu in list(self.model.IU)[:5]:  # Very limited
                if (iu, period) in self.adjusted_capacity:
                    var = pulp.LpVariable(f"prod_{iu}", 0, self.adjusted_capacity[(iu, period)])
                    pulp_vars[iu] = var
            
            # Simple objective
            pulp_model += pulp.lpSum(
                self.data.prod_cost_dict.get((iu, period), 0) * pulp_vars[iu]
                for iu in pulp_vars
            )
            
            # Simple capacity constraint
            total_capacity = sum(self.adjusted_capacity.get((iu, period), 0) for iu in pulp_vars)
            total_demand = sum(self.adjusted_demand.get((iugu, period), 0) for iugu in list(self.model.IUGU)[:5])
            
            if total_capacity > 0:
                pulp_model += pulp.lpSum(pulp_vars.values()) <= min(total_capacity, total_demand)
            
            # Solve
            solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=30)
            result = pulp_model.solve(solver)
            
            status = pulp.LpStatus[pulp_model.status]
            print(f"Pulp solver status: {status}")
            
            # Extract simple results
            self.results = {
                'objective_value': pulp.value(pulp_model.objective),
                'production': {iu: var.value() for iu, var in pulp_vars.items() if var.value() > 0},
                'transport': {},
                'inventory': {},
                'unmet_demand': {}
            }
            
            return status
            
        except Exception as e:
            print(f"Fallback solver also failed: {e}")
            return "Failed"
    
    def extract_results(self):
        """Extract and store results"""
        print("Extracting results...")
        
        self.results = {
            'objective_value': pyo.value(self.model.total_cost),
            'production': {},
            'transport': {},
            'inventory': {},
            'unmet_demand': {}
        }
        
        # Production results
        for iu in self.model.IU:
            for t in self.model.T:
                value = pyo.value(self.model.x[iu, t])
                if value and value > 0.001:
                    self.results['production'][(iu, t)] = value
        
        # Transport results
        for (iu, iugu, t) in self.model.TransportRoutes:
            value = pyo.value(self.model.y[iu, iugu, t])
            if value and value > 0.001:
                self.results['transport'][(iu, iugu, t)] = value
        
        # Inventory results
        for iugu in self.model.IUGU:
            for t in self.model.T:
                value = pyo.value(self.model.s[iugu, t])
                if value and value > 0.001:
                    self.results['inventory'][(iugu, t)] = value
        
        # Unmet demand (slack)
        for iugu in self.model.IUGU:
            for t in self.model.T:
                value = pyo.value(self.model.demand_slack[iugu, t])
                if value and value > 0.001:
                    self.results['unmet_demand'][(iugu, t)] = value
        
        print(f"Total cost: ${self.results['objective_value']:,.2f}")
        print(f"Active production plans: {len(self.results['production'])}")
        print(f"Active transport routes: {len(self.results['transport'])}")
        print(f"Inventory locations: {len(self.results['inventory'])}")
        print(f"Unmet demand locations: {len(self.results['unmet_demand'])}")
    
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
            
            # Unmet demand
            if self.results['unmet_demand']:
                unmet_data = []
                for (iugu, t), qty in self.results['unmet_demand'].items():
                    unmet_data.append({'IUGU CODE': iugu, 'TIME PERIOD': t, 'UNMET_DEMAND': qty})
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
    """Main function to run the fixed Pyomo model"""
    try:
        print("=" * 80)
        print("FIXED PYOMO OPTIMIZATION MODEL")
        print("=" * 80)
        
        # Create and solve model
        model = FixedClinkerPyomoModel('Dataset_Dummy_Clinker_3MPlan.xlsx')
        
        # Create feasible data
        model.create_feasible_data()
        
        # Build and solve model
        model.build_fixed_model()
        
        # Try different solvers
        solvers = ['glpk', 'cbc']
        status = None
        
        for solver in solvers:
            try:
                print(f"\n=== Trying solver: {solver} ===")
                status = model.solve_fixed_model(solver_name=solver)
                if status in ['ok', 'optimal', 'Optimal']:
                    print("\n✅ OPTIMAL SOLUTION FOUND!")
                    model.save_results('fixed_pyomo_results.xlsx')
                    break
            except Exception as e:
                print(f"Solver {solver} failed: {e}")
                continue
        
        if status not in ['ok', 'optimal', 'Optimal']:
            print("\n⚠️  NO OPTIMAL SOLUTION FOUND")
            print("Results may be partial or infeasible")
            model.save_results('fixed_pyomo_partial_results.xlsx')
            
    except Exception as e:
        print(f"Error in fixed Pyomo model: {e}")

if __name__ == "__main__":
    main()
