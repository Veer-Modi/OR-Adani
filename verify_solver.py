"""Verify CBC solver is properly detected."""

import os
import sys

# Add CBC to PATH
_cbc_path = r"C:\solvers\cbc\bin"
if os.path.exists(_cbc_path):
    current_path = os.environ.get("PATH", "")
    if _cbc_path not in current_path:
        os.environ["PATH"] = _cbc_path + os.pathsep + current_path
        print(f"[OK] Added CBC to PATH: {_cbc_path}")
    else:
        print(f"[OK] CBC already in PATH: {_cbc_path}")
else:
    print(f"[ERROR] CBC not found at {_cbc_path}")
    sys.exit(1)

# Test CBC detection
try:
    import pyomo.environ as pyo
    solver = pyo.SolverFactory('cbc')
    available = solver.available()
    
    print(f"\n{'='*50}")
    print("CBC Solver Verification")
    print(f"{'='*50}")
    print(f"CBC available: {available}")
    
    if available:
        print("\n[SUCCESS] CBC solver is properly configured!")
        print("The app should now detect CBC and optimization will work.")
    else:
        print("\n[ERROR] CBC solver is not available")
        print("Please check:")
        print(f"  1. CBC exists at: {_cbc_path}")
        print(f"  2. cbc.exe exists at: {os.path.join(_cbc_path, 'cbc.exe')}")
        sys.exit(1)
        
except Exception as e:
    print(f"\n[ERROR] testing CBC: {e}")
    sys.exit(1)
