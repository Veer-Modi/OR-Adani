# Optimization Solver Setup Guide

Your application requires an optimization solver (Gurobi, CBC, or HiGHS) to run the optimization features.

## Quick Solution: Download CBC Solver (Recommended for Free Use)

### Option 1: CBC Solver (Free, Open Source)

**For Windows:**

1. Download CBC solver from:
   - Official releases: https://github.com/coin-or/Cbc/releases
   - Pre-built binaries: https://ampl.com/products/solvers/open-source/#cbc
   
2. **Easy installation with conda** (if you have conda installed):
   ```bash
   conda install -c conda-forge coin-or-cbc
   ```

3. **Manual installation:**
   - Download the Windows binary (cbc.exe)
   - Place it in a folder, e.g., `C:\solvers\cbc\`
   - Add that folder to your system PATH:
     - Press Win+X, select "System"
     - Click "Advanced system settings"
     - Click "Environment Variables"
     - Under "System variables", find "Path"
     - Click "Edit" and add `C:\solvers\cbc\` (or wherever you placed cbc.exe)

4. **Verify installation:**
   ```powershell
   cbc -?
   ```

### Option 2: GLPK Solver (Free, Open Source)

**Using conda:**
```bash
conda install -c conda-forge glpk
```

**Using Chocolatey (Windows package manager):**
```powershell
choco install glpk-utils
```

### Option 3: HiGHS Solver (Free, Open Source)

HiGHS is modern and fast, but requires C++ build tools on Windows.

**Using conda (recommended):**
```bash
conda install -c conda-forge highspy
```

### Option 4: Gurobi (Commercial, Free Academic License)

Gurobi is the fastest but requires a license.

1. Download from: https://www.gurobi.com/downloads/
2. Get a free academic license: https://www.gurobi.com/academia/academic-program-and-licenses/
3. Install and activate the license following Gurobi's instructions

## After Installing a Solver

1. **Restart your terminal** to ensure PATH changes are loaded
2. **Restart the Streamlit app:**
   ```powershell
   cd hack-clink\auth-system
   .\.venv\Scripts\Activate.ps1
   streamlit run app.py
   ```

## Troubleshooting

### Check if solver is available:
```python
import pyomo.environ as pyo

# Check CBC
solver = pyo.SolverFactory('cbc')
print(f"CBC available: {solver.available()}")

# Check GLPK  
solver = pyo.SolverFactory('glpk')
print(f"GLPK available: {solver.available()}")

# Check HiGHS
solver = pyo.SolverFactory('highs')
print(f"HiGHS available: {solver.available()}")
```

### Common Issues:

1. **"Solver not found"**
   - Make sure the solver executable is in your system PATH
   - Restart your terminal/IDE after adding to PATH

2. **"Permission denied"**
   - Run terminal as Administrator
   - Check file permissions on the solver executable

3. **Still not working?**
   - Use conda to install: `conda install -c conda-forge coincbc` (for CBC)
   - This handles all dependencies automatically

## Quick Test

Once installed, the app will automatically detect available solvers. You'll see a warning on startup only if **no** solvers are available.
