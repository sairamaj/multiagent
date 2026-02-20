# Quick Start Guide

Get your Multi-Agent system running in 5 minutes!

---

## 🚀 Super Quick Start (1 Minute)

Already have Azure OpenAI? Try it now:

```bash
# 1. Set environment variables
export AZURE_OPENAI_KEY=your-key-here
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# 2. Install and run
pip install -r requirements.txt
python src/main.py --interactive
```

That's it! Start asking questions like:
- "List all VMs matching CI template pattern"
- "Show me build failures from last week"

---

## 📋 Full Setup (5 Minutes)

### Step 1: Clone & Install (1 min)

```bash
cd mulagent
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Configure (2 min)

```bash
# Copy environment template
cp .env.example .env

# Edit .env file - add your Azure OpenAI credentials
nano .env  # or use any editor
```

Required in `.env`:
```bash
AZURE_OPENAI_KEY=your-azure-openai-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
ENVIRONMENT=development
```

### Step 3: Verify (1 min)

```bash
# Test configuration
python -c "from src.config_loader import config_loader; print('✓ Config OK')"

# Show examples
python src/main.py --examples
```

### Step 4: Run (1 min)

Choose your preferred interface:

**Option A: Interactive CLI**
```bash
python src/main.py --interactive
```

**Option B: Single Command**
```bash
python src/main.py --command "List all VM patterns"
```

**Option C: REST API**
```bash
# Start API server
python src/main.py --api

# In another terminal
curl http://localhost:8000/health
curl http://localhost:8000/examples
```

---

## 🐳 Docker Quick Start (2 Minutes)

### Option 1: Docker Compose (Easiest)

```bash
# 1. Configure
cp .env.example .env
# Edit .env with your credentials

# 2. Start
docker-compose up -d

# 3. Test
curl http://localhost:8000/health

# 4. Use
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"message": "List all agents"}'
```

### Option 2: Docker CLI

```bash
docker build -t mulagent .

docker run -d \
  --name mulagent \
  -p 8000:8000 \
  -e AZURE_OPENAI_KEY=your-key \
  -e AZURE_OPENAI_ENDPOINT=your-endpoint \
  mulagent
```

---

## 🎯 First Commands to Try

### Azure Resources

```bash
# Interactive mode
> List all VMs matching CI template pattern
> Show me VMs older than 30 days
> What VMs would be deleted in cleanup?
> Check VM compliance with naming patterns
```

```bash
# Command line
python src/main.py --command "List all VM patterns"
python src/main.py --command "Show me non-compliant VMs"
```

```bash
# API
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"message": "List all VMs matching CI template pattern"}'
```

### Build Monitoring

```bash
# Interactive
> Show build failures from last 7 days
> Analyze build failures and identify patterns
> Get build success rate for last week

# Command line
python src/main.py --command "Analyze build failures"

# API
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"message": "Show build failures from last week"}'
```

### Storage & Files

```bash
# Interactive
> What is our blob retention policy?
> List all Python files in src
> Calculate storage usage

# Command line
python src/main.py --command "Show blob retention policies"

# API
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"message": "What blobs would be deleted?"}'
```

---

## 🧪 Testing Your Setup

### 1. Test Configuration Loading

```bash
python -c "
from src.config_loader import config_loader
pattern = config_loader.get_vm_pattern('ci_templates')
print('✓ Pattern loaded:', pattern['pattern'])
"
```

### 2. Test Pattern Matching

```bash
python -c "
from src.config_loader import config_loader
name = 'vhds-ci-wat-template-26-1-0.beta-20260213025457'
matches = config_loader.matches_pattern(name, 'ci_templates')
print('✓ Pattern match:', matches)
"
```

### 3. Run Unit Tests

```bash
python tests/run_tests.py
# Should see: ✓ All tests passing
```

### 4. Test API Health

```bash
# Start API
python src/main.py --api &

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/config
curl http://localhost:8000/agents
curl http://localhost:8000/examples

# View docs
open http://localhost:8000/docs  # Opens in browser
```

---

## 🔧 Common Issues & Fixes

### Issue 1: "Azure OpenAI configuration missing"

**Fix:**
```bash
# Verify environment variables are set
echo $AZURE_OPENAI_KEY
echo $AZURE_OPENAI_ENDPOINT

# Or check .env file
cat .env | grep AZURE_OPENAI
```

### Issue 2: "Configuration file not found"

**Fix:**
```bash
# Verify you're in the project root
ls config/  # Should show YAML files

# Or specify full path
export PYTHONPATH=/path/to/mulagent:$PYTHONPATH
```

### Issue 3: "Import errors"

**Fix:**
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Verify Python version
python --version  # Should be 3.9+
```

### Issue 4: "API won't start"

**Fix:**
```bash
# Check if port 8000 is in use
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows

# Use different port
uvicorn src.api.app:app --port 8001
```

---

## 📖 Next Steps

### 1. Explore Examples

```bash
# View all examples
python src/main.py --examples

# Try each one in interactive mode
python src/main.py --interactive
```

### 2. Customize Configuration

Edit configuration files in `config/`:
- `azure_resources.yaml` - VM patterns, cleanup rules
- `storage_cleanup.yaml` - Blob retention policies
- `build_monitoring.yaml` - Build thresholds
- `environments.yaml` - Environment overrides

### 3. Read Documentation

- [USAGE-GUIDE.md](USAGE-GUIDE.md) - Detailed usage examples
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment
- [README.md](README.md) - Complete documentation

### 4. Deploy to Production

```bash
# Local testing → Docker → Azure Container Apps
# See DEPLOYMENT.md for complete guide
```

---

## 💡 Pro Tips

### 1. Use Dry Run First

Always test destructive operations:
```bash
> Show me what VMs would be deleted
# Review results
> Delete VMs with confirmation
```

### 2. Leverage Configuration

Don't hardcode values:
```bash
# Good
> Clean up VMs following our retention policy

# Less Good
> Delete VMs older than 30 days  # Might not match config
```

### 3. Check Examples

When unsure, check examples:
```bash
python src/main.py --examples
curl http://localhost:8000/examples
```

### 4. Use Verbose Mode for Debugging

```bash
python src/main.py --interactive --verbose
```

### 5. Monitor API Logs

```bash
# Docker
docker-compose logs -f

# Direct
tail -f logs/api.log
```

---

## 🎉 Success!

You're now ready to use the Multi-Agent DevOps Automation System!

**What you can do:**
- ✅ Ask questions in natural language
- ✅ Manage VMs with configured patterns
- ✅ Monitor builds and analyze failures
- ✅ Cleanup storage based on retention policies
- ✅ Integrate with your portal via REST API

**Need help?**
- Interactive: Type `examples` for sample commands
- CLI: `python src/main.py --examples`
- API: http://localhost:8000/docs
- Docs: See [USAGE-GUIDE.md](USAGE-GUIDE.md)

---

Happy Automating! 🚀
