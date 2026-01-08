"""Analytics package (Phase 5).

This package adds an explainable analytics layer on top of stored optimization runs.

Important:
- We do NOT change optimization logic.
- Analytics reads stored run outputs (tables) + master data (plants, routes, inventory policies, demands).
- Analytics results are stored back into the optimization run document for fast dashboards.
"""
