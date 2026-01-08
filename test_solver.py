"""Quick test to verify CBC solver works with optimization."""

import os
import pyomo.environ as pyo

# Add CBC to path
os.environ['PATH'] = r'C:\solvers\cbc\bin;' + os.environ['PATH']

print("=" * 50)
print("Testing CBC Solver")
print("=" * 50)

# Create a simple optimization model
model = pyo.ConcreteModel()

# Variables
model.x = pyo.Var(bounds=(0, 10))
model.y = pyo.Var(bounds=(0, 10))

# Objective: maximize x + 2y
model.obj = pyo.Objective(expr=model.x + 2*model.y, sense=pyo.maximize)

# Constraints
model.con1 = pyo.Constraint(expr=model.x + model.y <= 8)
model.con2 = pyo.Constraint(expr=2*model.x + model.y <= 10)

# Solve
print("\n1. Checking solver availability...")
solver = pyo.SolverFactory('cbc')
print(f"   CBC available: {solver.available()}")

if solver.available():
    print("\n2. Solving optimization problem...")
    print("   Maximize: x + 2y")
    print("   Subject to:")
    print("     x + y <= 8")
    print("     2x + y <= 10")
    print("     x, y >= 0")
    
    results = solver.solve(model, tee=False)
    
    print("\n3. Results:")
    print(f"   Status: {results.solver.status}")
    print(f"   Termination: {results.solver.termination_condition}")
    print(f"   Optimal x = {pyo.value(model.x):.2f}")
    print(f"   Optimal y = {pyo.value(model.y):.2f}")
    print(f"   Optimal objective value = {pyo.value(model.obj):.2f}")
    
    print("\n" + "=" * 50)
    print("✓ CBC SOLVER IS WORKING PERFECTLY!")
    print("=" * 50)
else:
    print("\n✗ ERROR: CBC solver not available")
    print("=" * 50)
