# PowerShell script to download and install CBC solver for Windows

Write-Host "=== CBC Solver Installation Script ===" -ForegroundColor Green
Write-Host ""

# Create solvers directory
$solverDir = "C:\solvers\cbc"
Write-Host "Creating solver directory at: $solverDir" -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $solverDir | Out-Null

# Download CBC from AMPL
$cbcUrl = "https://ampl.com/dl/open/cbc/cbc-win64.zip"
$zipPath = "$env:TEMP\cbc-win64.zip"

Write-Host "Downloading CBC solver..." -ForegroundColor Yellow
try {
    Invoke-WebRequest -Uri $cbcUrl -OutFile $zipPath -UseBasicParsing
    Write-Host "Download complete!" -ForegroundColor Green
} catch {
    Write-Host "Error downloading CBC. Please download manually from:" -ForegroundColor Red
    Write-Host "https://ampl.com/products/solvers/open-source/#cbc" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Alternative: Use conda to install CBC:" -ForegroundColor Cyan
    Write-Host "  conda install -c conda-forge coincbc" -ForegroundColor White
    exit 1
}

# Extract the archive
Write-Host "Extracting CBC..." -ForegroundColor Yellow
try {
    Expand-Archive -Path $zipPath -DestinationPath $solverDir -Force
    Write-Host "Extraction complete!" -ForegroundColor Green
} catch {
    Write-Host "Error extracting archive: $_" -ForegroundColor Red
    exit 1
}

# Add to PATH
Write-Host "Adding CBC to system PATH..." -ForegroundColor Yellow
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($currentPath -notlike "*$solverDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$currentPath;$solverDir", "User")
    Write-Host "CBC added to PATH!" -ForegroundColor Green
    Write-Host "Please restart your terminal for changes to take effect." -ForegroundColor Yellow
} else {
    Write-Host "CBC is already in PATH." -ForegroundColor Green
}

# Verify installation
Write-Host ""
Write-Host "=== Installation Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "CBC solver has been installed to: $solverDir" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Close and reopen your terminal/PowerShell" -ForegroundColor White
Write-Host "2. Verify installation by running: cbc -?" -ForegroundColor White
Write-Host "3. Restart your Streamlit app" -ForegroundColor White
Write-Host ""
Write-Host "If you have issues, check the SOLVER_SETUP.md file for alternative installation methods." -ForegroundColor Cyan
