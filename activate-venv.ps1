# Activation script for the virtual environment
# Usage: . .\activate-venv.ps1  (note the leading dot and space)

$venvActivate = ".\venv\Scripts\Activate.ps1"

if (-not (Test-Path $venvActivate)) {
    Write-Error "Virtual environment not found at .\venv\"
    Write-Host "To create it, run: python -m venv venv"
    exit 1
}

Write-Host "Activating virtual environment..." -ForegroundColor Green
& $venvActivate

# Verify activation
$pythonPath = (Get-Command python).Source
if ($pythonPath -like "*venv*") {
    Write-Host "✓ Virtual environment activated successfully" -ForegroundColor Green
    Write-Host "Python: $pythonPath" -ForegroundColor Cyan
} else {
    Write-Warning "Virtual environment may not be activated correctly"
    Write-Host "Python: $pythonPath" -ForegroundColor Yellow
}
