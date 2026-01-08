# ⚠️ OPTIMIZATION SOLVER NOT INSTALLED

Your application is running but **optimization features won't work** because no solver (Gurobi, CBC, or HiGHS) is installed.

## 🚀 EASIEST SOLUTIONS (Pick One)

### Solution 1: Install via Conda (RECOMMENDED - Takes 2 minutes)

If you have Anaconda or Miniconda installed:

```powershell
# In your terminal:
conda install -c conda-forge coincbc
```

That's it! Conda handles everything automatically.

### Solution 2: Download CBC Manually (5 minutes)

1. **Download CBC**:
   - Go to: https://github.com/coin-or/Cbc/releases
   - Download the latest Windows binary (look for `cbc-win64.zip` or similar)
   
2. **Extract and Setup**:
   ```powershell
   # Extract to C:\solvers\cbc\
   # Then add to PATH:
   $env:PATH += ";C:\solvers\cbc"
   # Make it permanent:
   [Environment]::SetEnvironmentVariable("Path", $env:PATH, "User")
   ```

3. **Verify**:
   ```powershell
   cbc -?
   ```

### Solution 3: Install Gurobi (If you have academic/commercial license)

1. Download from: https://www.gurobi.com/downloads/
2. Get free academic license: https://www.gurobi.com/academia/
3. Follow Gurobi's installation wizard
4. Activate your license

### Solution 4: Use WinLibs (Alternative)

Install CBC using Windows binaries from:
https://sourceforge.net/projects/winglpk/

## After Installing:

1. **Close all terminals and reopen**
2. **Restart your Streamlit app:**
   ```powershell
   cd hack-clink\auth-system
   .\.venv\Scripts\Activate.ps1
   streamlit run app.py
   ```

3. The app will automatically detect the solver!

## Quick Test

To verify the solver is working, open Python:

```python
import pyomo.environ as pyo
solver = pyo.SolverFactory('cbc')
print(f"CBC available: {solver.available()}")
```

Should print: `CBC available: True`

## Still Having Issues?

**Contact your system administrator** or use conda (Solution 1) which handles all dependencies automatically.

---

**Current Status**: App is running at http://localhost:8501 but optimization won't work until a solver is installed.
