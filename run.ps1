# Helper script to run the Multi-Agent system with the correct Python environment
# Usage: .\run.ps1 [args]
# Examples:
#   .\run.ps1 --interactive
#   .\run.ps1 -c "List configuration files"
#   .\run.ps1 --examples

$venvPython = ".\venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Error "Virtual environment not found. Please run 'python -m venv venv' first."
    exit 1
}

# Pass all arguments to the Python script
& $venvPython src\main.py $args
