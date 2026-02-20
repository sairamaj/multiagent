# Usage Guide

Complete guide for using the Multi-Agent DevOps Automation System.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [CLI Usage](#cli-usage)
3. [REST API Usage](#rest-api-usage)
4. [Example Tasks](#example-tasks)
5. [Best Practices](#best-practices)

---

## Getting Started

### First Time Setup

1. **Install and configure:**
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Configure environment
   cp .env.example .env
   # Edit .env with your credentials
   ```

2. **Verify configuration:**
   ```bash
   python src/main.py --examples
   ```

3. **Test with a simple command:**
   ```bash
   python src/main.py --command "List all VM naming patterns"
   ```

---

## CLI Usage

### Interactive Mode

Most user-friendly way to interact with the system:

```bash
python src/main.py --interactive
```

**Features:**
- Natural language input
- Conversational interface
- Type `examples` to see sample commands
- Type `exit` to quit

**Example Session:**
```
> List all VMs matching CI template pattern

Executing task...
✓ Task completed successfully

Summary:
Found 3 VMs matching CI template pattern:
- vhds-ci-wat-template-26-1-0.beta-20260213025457 (Running)
- vhds-ci-wat-template-25-2-1.release-20260115103022 (Stopped)
```

### Single Command Mode

Execute one command and exit:

```bash
python src/main.py --command "YOUR COMMAND HERE"
```

**Examples:**
```bash
# Azure resources
python src/main.py --command "Show me VMs older than 30 days"

# Build monitoring
python src/main.py --command "Analyze build failures from last week"

# Storage
python src/main.py --command "What blobs would be deleted in cleanup?"
```

### Verbose Mode

Enable detailed logging:

```bash
python src/main.py --interactive --verbose
```

### Show Examples

```bash
python src/main.py --examples
```

---

## REST API Usage

### Starting the API

```bash
# Method 1: Using main.py
python src/main.py --api

# Method 2: Using uvicorn directly
uvicorn src.api.app:app --host 0.0.0.0 --port 8000

# Method 3: Using Docker
docker-compose up -d
```

### API Endpoints

#### Health Check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "agents": ["manager", "azure_agent", "build_agent", "file_agent"],
  "config_loaded": true
}
```

#### Get Configuration

```bash
curl http://localhost:8000/config
```

**Response:**
```json
{
  "vm_patterns": {
    "ci_templates": {
      "pattern": "vhds-ci-wat-template-{release}.{release_type}-{timestamp}",
      "regex": "^vhds-ci-wat-template-\\d+-\\d+-\\d+\\.(beta|rc|release)-\\d{14}$"
    }
  },
  "blob_retention": {
    "ci_artifacts": {
      "keep_latest_count": 5,
      "age_threshold_days": 90
    }
  },
  "environment": "development"
}
```

#### Execute Task

```bash
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "message": "List all VMs matching CI template pattern"
  }'
```

**Response:**
```json
{
  "success": true,
  "task_id": "a3f2b891",
  "message": "List all VMs matching CI template pattern",
  "summary": "Found 3 VMs matching the CI template pattern..."
}
```

#### Execute Task Asynchronously

For long-running tasks:

```bash
curl -X POST http://localhost:8000/execute/async \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analyze all build failures and correlate with VM issues"
  }'
```

**Response:**
```json
{
  "task_id": "b5d8c123",
  "status": "queued",
  "message": "Task queued for execution"
}
```

#### List Available Agents

```bash
curl http://localhost:8000/agents
```

#### Get Example Tasks

```bash
curl http://localhost:8000/examples
```

### API Documentation

Interactive API documentation available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Example Tasks

### Azure Resources

#### List VMs by Pattern

```bash
# CLI
python src/main.py --command "List all VMs matching CI template pattern"

# API
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"message": "List all VMs matching CI template pattern"}'
```

#### Check VM Compliance

```bash
# CLI
python src/main.py --command "Check which VMs don't match our naming patterns"

# API
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"message": "Check which VMs are non-compliant with naming patterns"}'
```

#### Simulate VM Cleanup

```bash
# CLI
python src/main.py --command "Show me what VMs would be deleted in cleanup"

# API
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"message": "Dry run cleanup for CI template VMs"}'
```

### Build Monitoring

#### Check Build Status

```bash
# CLI
python src/main.py --command "Show me the status of all monitored pipelines"

# API
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the current status of our build pipelines?"}'
```

#### Analyze Failures

```bash
# CLI
python src/main.py --command "Analyze build failures from the last 7 days"

# API
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"message": "Analyze build failures and identify patterns"}'
```

#### Get Build Metrics

```bash
# CLI
python src/main.py --command "Show me build success rate for last week"

# API
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"message": "Get build metrics for the last 7 days"}'
```

### Storage Management

#### Check Blob Retention

```bash
# CLI
python src/main.py --command "What is our blob retention policy?"

# API
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me all blob retention policies"}'
```

#### Storage Usage

```bash
# CLI
python src/main.py --command "How much storage are we using for CI artifacts?"

# API
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"message": "Calculate storage usage for CI artifacts"}'
```

### File Operations

#### List Files

```bash
# CLI
python src/main.py --command "List all Python files in the src directory"

# API
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"message": "List Python files in src"}'
```

#### Read Configuration

```bash
# CLI
python src/main.py --command "Show me the Azure resources configuration"

# API
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"message": "Read azure_resources.yaml configuration"}'
```

### Complex Multi-Step Tasks

#### Correlate Build Failures with VM Issues

```bash
# CLI
python src/main.py --command "Find build failures and check if the related VMs have resource constraints"

# API
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"message": "Analyze build failures and correlate with VM performance issues"}'
```

#### Comprehensive Cleanup Report

```bash
# CLI
python src/main.py --command "Generate a report of what would be cleaned up across VMs and storage"

# API
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"message": "Create cleanup report for VMs and blobs"}'
```

---

## Best Practices

### 1. Start with Dry Run

For destructive operations, always do a dry run first:

```bash
# Good
python src/main.py --command "Show me what VMs would be deleted"
# Review results, then:
python src/main.py --command "Clean up VMs with confirmation"

# Avoid
python src/main.py --command "Delete all old VMs immediately"
```

### 2. Be Specific in Requests

**Better:**
```
"List VMs matching CI template pattern created in the last 30 days"
```

**Less Clear:**
```
"Show me some VMs"
```

### 3. Use Configuration Effectively

Leverage the configuration system instead of hardcoding values:

**Good:**
```
"Clean up VMs following our configured retention policy"
```

**Less Good:**
```
"Delete VMs older than 30 days"  # This might not match config
```

### 4. Review Before Confirming

Always review what will be changed:

```bash
# Step 1: Review
python src/main.py --command "What blobs would be deleted?"

# Step 2: Confirm if okay
python src/main.py --command "Clean up blobs with confirmation"
```

### 5. Monitor API Usage

For production API usage:

- Enable logging
- Set up monitoring
- Implement rate limiting
- Use authentication

### 6. Test in Development First

Use environment-specific configuration:

```bash
# Test in development
export ENVIRONMENT=development
python src/main.py --command "Test cleanup"

# Then in production
export ENVIRONMENT=production
python src/main.py --command "Execute cleanup"
```

### 7. Handle Errors Gracefully

Check response status:

```python
import requests

response = requests.post(
    "http://localhost:8000/execute",
    json={"message": "Your task"}
)

if response.json()["success"]:
    print("Success:", response.json()["summary"])
else:
    print("Error:", response.json()["error"])
```

---

## Advanced Usage

### Custom Agent Configurations

Modify agent system messages in `src/agents/manager_agent.py` to customize behavior.

### Adding New Tools

1. Create tool function in appropriate agent
2. Register tool with agent
3. Update agent system message
4. Test with CLI/API

### Extending Configuration

Add new configuration files in `config/` directory and update `config_loader.py`.

---

## Troubleshooting

### Command Not Understood

If the agent doesn't understand your command:

1. Try rephrasing more explicitly
2. Break down into smaller tasks
3. Use examples as templates
4. Check logs with `--verbose`

### API Returns Error

```bash
# Check API health
curl http://localhost:8000/health

# Check configuration
curl http://localhost:8000/config

# View logs
docker-compose logs -f
```

### Slow Response

- Complex tasks take longer
- Use async endpoint for long-running tasks
- Check Azure OpenAI quota
- Consider using GPT-3.5-turbo for simpler tasks

---

## Getting Help

- View examples: `python src/main.py --examples`
- API documentation: http://localhost:8000/docs
- Check logs: `docker-compose logs -f`
- Review configuration: `curl http://localhost:8000/config`

---

**Happy Automating!** 🚀
