"""Optimization package.

This package contains the deterministic optimization engine:
- data_loader: reads MongoDB and validates data
- model: builds a Pyomo model
- constraints/objective: define the math
- solver: runs Gurobi (or fallback)
- result_parser: converts Pyomo solution into tables/charts friendly data
"""
