# Quick Start Guide

## Setup

1. **Ensure you're in the project directory:**
   ```powershell
   cd c:\sai\dev\ai\agent\mulagent
   ```

2. **Virtual environment is already created at `.\venv\`**

3. **Dependencies are already installed**

## Running the Application

### Option 1: Using the Helper Script (Recommended)

```powershell
# Show example commands
.\run.ps1 --examples

# Interactive mode
.\run.ps1 --interactive

# Single command
.\run.ps1 -c "List configuration files"

# Verbose mode
.\run.ps1 -c "Show me VMs" -v
```

### Option 2: Activate Virtual Environment Manually

```powershell
# Activate the venv (note: the leading dot and space are important!)
. .\venv\Scripts\Activate.ps1

# Now run the application
python src\main.py --interactive

# When done, deactivate
deactivate
```

### Option 3: Direct Execution

```powershell
.\venv\Scripts\python.exe src\main.py --interactive
```

## Common Issues

### Issue: "ModuleNotFoundError: No module named 'autogen'"

**Problem:** You're using the global Python instead of the venv Python.

**Solution:** Use one of the methods above (preferably `.\run.ps1`)

### Issue: venv shows in prompt but wrong Python is used

**Problem:** The venv isn't properly activated.

**Solution:** 
1. Deactivate any active environment: `deactivate`
2. Use the activation helper: `. .\activate-venv.ps1`
3. Or use the run script: `.\run.ps1`

## Verify Setup

Check that you're using the correct Python:

```powershell
# Should show path containing 'venv'
(Get-Command python).Source

# Or use the venv Python directly
.\venv\Scripts\python.exe --version
```

## Example Commands

Once running in interactive mode, try:

- `List configuration files`
- `Show me VMs that would be deleted in cleanup`
- `Get build metrics for last week`
- `List all blob retention policies`

Type `exit` or `quit` to stop.
