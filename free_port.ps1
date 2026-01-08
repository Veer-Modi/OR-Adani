# Script to free port 8501 from any process

Write-Host "=== Freeing Port 8501 ===" -ForegroundColor Cyan
Write-Host ""

# Find all processes using port 8501
$connections = Get-NetTCPConnection -LocalPort 8501 -ErrorAction SilentlyContinue

if ($connections) {
    Write-Host "Found processes using port 8501:" -ForegroundColor Yellow
    $processIds = $connections | Select-Object -Unique -ExpandProperty OwningProcess
    
    foreach ($pid in $processIds) {
        $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($process) {
            Write-Host "  - Process ID: $pid ($($process.ProcessName)) - Started: $($process.StartTime)" -ForegroundColor White
        }
    }
    
    Write-Host ""
    Write-Host "Stopping processes..." -ForegroundColor Yellow
    
    # Stop all processes using port 8501
    $connections | ForEach-Object { 
        Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue 
    }
    
    Start-Sleep -Seconds 2
    
    # Verify port is free
    $remaining = Get-NetTCPConnection -LocalPort 8501 -ErrorAction SilentlyContinue
    if (-not $remaining) {
        Write-Host "SUCCESS: Port 8501 is now FREE!" -ForegroundColor Green
    } else {
        Write-Host "WARNING: Port still in use" -ForegroundColor Red
    }
} else {
    Write-Host "Port 8501 is already FREE!" -ForegroundColor Green
}

Write-Host ""
Write-Host "You can now start your Streamlit app." -ForegroundColor Cyan
