import pyomo.environ as pyo
import highspy

print("Checking Highs via appsi...")
try:
    s = pyo.SolverFactory('appsi_highs')
    print(f"appsi_highs available: {s.available()}")
except Exception as e:
    print(f"appsi_highs error: {e}")

print("Checking Highs via highs...")
try:
    s = pyo.SolverFactory('highs')
    print(f"highs available: {s.available()}")
except Exception as e:
    print(f"highs error: {e}")
