# Startup script for the Streamlit application with CBC solver

Write-Host "=== Starting Application with CBC Solver ===" -ForegroundColor Green
Write-Host ""

# Ensure CBC is in PATH
$cbcPath = "C:\solvers\cbc\bin"
$env:Path = "$cbcPath;" + $env:Path
Write-Host "CBC solver added to PATH" -ForegroundColor Green

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
& .\.venv\Scripts\Activate.ps1

# Verify CBC is available
Write-Host ""
Write-Host "Checking solver availability..." -ForegroundColor Cyan
python -c "import pyomo.environ as pyo; solver = pyo.SolverFactory('cbc'); print('CBC available: ' + str(solver.available()))"

Write-Host ""
Write-Host "=== Freeing Port 8501 ===" -ForegroundColor Cyan

# Free port 8501 if it's in use
$connections = Get-NetTCPConnection -LocalPort 8501 -ErrorAction SilentlyContinue
if ($connections) {
    Write-Host "Port 8501 is in use. Freeing it..." -ForegroundColor Yellow
    $connections | ForEach-Object { 
        Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue 
    }
    Start-Sleep -Seconds 2
    Write-Host "Port 8501 is now free!" -ForegroundColor Green
} else {
    Write-Host "Port 8501 is available" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Starting Streamlit App ===" -ForegroundColor Green
Write-Host ""

# Start Streamlit
streamlit run app.py
