# Deployment Guide

Complete guide for deploying the Multi-Agent DevOps Automation System.

---

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Azure Container Apps](#azure-container-apps)
4. [Configuration](#configuration)
5. [Monitoring](#monitoring)
6. [Troubleshooting](#troubleshooting)

---

## Local Development

### Prerequisites

- Python 3.9 or higher
- Azure OpenAI service
- Azure subscription (for actual Azure operations)

### Setup

1. **Clone repository and navigate to project:**
   ```bash
   cd mulagent
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   # Copy example environment file
   cp .env.example .env
   
   # Edit .env and add your Azure credentials
   nano .env  # or use your preferred editor
   ```

5. **Test configuration loading:**
   ```bash
   python -c "from src.config_loader import config_loader; print('Config OK')"
   ```

### Running Locally

#### Option 1: Interactive CLI

```bash
python src/main.py --interactive
```

#### Option 2: Single Command

```bash
python src/main.py --command "List all VMs matching CI template pattern"
```

#### Option 3: REST API

```bash
# Start API server
python src/main.py --api

# Or using uvicorn directly
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

Access API docs at: http://localhost:8000/docs

---

## Docker Deployment

### Build Docker Image

```bash
# Build image
docker build -t mulagent:latest .

# Test image
docker run --rm mulagent:latest python -c "print('Image OK')"
```

### Run with Docker

#### Single Container

```bash
docker run -d \
  --name mulagent \
  -p 8000:8000 \
  -e AZURE_OPENAI_KEY=your-key \
  -e AZURE_OPENAI_ENDPOINT=your-endpoint \
  -e ENVIRONMENT=production \
  mulagent:latest
```

#### Docker Compose

```bash
# Create .env file with your credentials
cp .env.example .env

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Docker Health Check

```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' mulagent

# View health check logs
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' mulagent
```

---

## Azure Container Apps

### Prerequisites

- Azure CLI installed
- Azure subscription
- Resource group created

### Deployment Steps

#### 1. Create Container Registry

```bash
# Variables
RESOURCE_GROUP="rg-mulagent"
ACR_NAME="mulagentregistry"
LOCATION="eastus"

# Create ACR
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic \
  --location $LOCATION

# Login to ACR
az acr login --name $ACR_NAME
```

#### 2. Build and Push Image

```bash
# Build and tag
docker build -t $ACR_NAME.azurecr.io/mulagent:latest .

# Push to ACR
docker push $ACR_NAME.azurecr.io/mulagent:latest
```

#### 3. Create Container App Environment

```bash
# Create environment
az containerapp env create \
  --name mulagent-env \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Create Log Analytics workspace (for monitoring)
az monitor log-analytics workspace create \
  --resource-group $RESOURCE_GROUP \
  --workspace-name mulagent-logs \
  --location $LOCATION
```

#### 4. Deploy Container App

```bash
# Create container app
az containerapp create \
  --name mulagent-api \
  --resource-group $RESOURCE_GROUP \
  --environment mulagent-env \
  --image $ACR_NAME.azurecr.io/mulagent:latest \
  --target-port 8000 \
  --ingress external \
  --registry-server $ACR_NAME.azurecr.io \
  --secrets \
    azure-openai-key=$AZURE_OPENAI_KEY \
    azure-openai-endpoint=$AZURE_OPENAI_ENDPOINT \
  --env-vars \
    ENVIRONMENT=production \
    AZURE_OPENAI_KEY=secretref:azure-openai-key \
    AZURE_OPENAI_ENDPOINT=secretref:azure-openai-endpoint \
    AZURE_OPENAI_MODEL=gpt-4 \
  --cpu 1.0 \
  --memory 2.0Gi \
  --min-replicas 1 \
  --max-replicas 3
```

#### 5. Get Application URL

```bash
# Get FQDN
az containerapp show \
  --name mulagent-api \
  --resource-group $RESOURCE_GROUP \
  --query properties.configuration.ingress.fqdn \
  --output tsv
```

### Update Deployment

```bash
# Build new version
docker build -t $ACR_NAME.azurecr.io/mulagent:v2 .
docker push $ACR_NAME.azurecr.io/mulagent:v2

# Update container app
az containerapp update \
  --name mulagent-api \
  --resource-group $RESOURCE_GROUP \
  --image $ACR_NAME.azurecr.io/mulagent:v2
```

### Scaling

```bash
# Manual scaling
az containerapp update \
  --name mulagent-api \
  --resource-group $RESOURCE_GROUP \
  --min-replicas 2 \
  --max-replicas 5

# Auto-scaling rules
az containerapp update \
  --name mulagent-api \
  --resource-group $RESOURCE_GROUP \
  --scale-rule-name cpu-rule \
  --scale-rule-type cpu \
  --scale-rule-metadata "concurrency=10"
```

---

## Configuration

### Environment Variables

Required:
- `AZURE_OPENAI_KEY`: Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint URL
- `ENVIRONMENT`: Deployment environment (development/staging/production)

Optional:
- `AZURE_OPENAI_MODEL`: Model name (default: gpt-4)
- `AZURE_OPENAI_API_VERSION`: API version (default: 2024-02-01)
- `AZURE_SUBSCRIPTION_ID`: Azure subscription ID
- `AZURE_TENANT_ID`: Azure tenant ID
- `AZURE_DEVOPS_ORG`: Azure DevOps organization
- `AZURE_DEVOPS_PAT`: Azure DevOps personal access token
- `LOG_LEVEL`: Logging level (default: INFO)

### Azure Key Vault Integration

For production, store secrets in Azure Key Vault:

```bash
# Create Key Vault
az keyvault create \
  --name mulagent-kv \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Add secrets
az keyvault secret set \
  --vault-name mulagent-kv \
  --name azure-openai-key \
  --value $AZURE_OPENAI_KEY

# Grant container app access
az containerapp identity assign \
  --name mulagent-api \
  --resource-group $RESOURCE_GROUP \
  --system-assigned

# Get principal ID
PRINCIPAL_ID=$(az containerapp show \
  --name mulagent-api \
  --resource-group $RESOURCE_GROUP \
  --query identity.principalId -o tsv)

# Grant access to Key Vault
az keyvault set-policy \
  --name mulagent-kv \
  --object-id $PRINCIPAL_ID \
  --secret-permissions get list
```

Update app to use Key Vault references:
```bash
az containerapp update \
  --name mulagent-api \
  --resource-group $RESOURCE_GROUP \
  --secrets \
    azure-openai-key=keyvaultref:https://mulagent-kv.vault.azure.net/secrets/azure-openai-key
```

---

## Monitoring

### Application Insights

```bash
# Create Application Insights
az monitor app-insights component create \
  --app mulagent-insights \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP \
  --application-type web

# Get instrumentation key
INSTRUMENTATION_KEY=$(az monitor app-insights component show \
  --app mulagent-insights \
  --resource-group $RESOURCE_GROUP \
  --query instrumentationKey -o tsv)

# Update container app
az containerapp update \
  --name mulagent-api \
  --resource-group $RESOURCE_GROUP \
  --env-vars \
    APPINSIGHTS_INSTRUMENTATIONKEY=$INSTRUMENTATION_KEY
```

### Viewing Logs

```bash
# Stream logs
az containerapp logs show \
  --name mulagent-api \
  --resource-group $RESOURCE_GROUP \
  --follow

# Query logs
az monitor log-analytics query \
  --workspace mulagent-logs \
  --analytics-query "ContainerAppConsoleLogs_CL | where TimeGenerated > ago(1h)"
```

### Metrics

```bash
# View metrics
az monitor metrics list \
  --resource /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.App/containerApps/mulagent-api \
  --metric-names Requests
```

### Alerts

```bash
# Create alert for high error rate
az monitor metrics alert create \
  --name mulagent-high-errors \
  --resource-group $RESOURCE_GROUP \
  --scopes /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.App/containerApps/mulagent-api \
  --condition "avg Requests > 100" \
  --description "Alert when error rate is high"
```

---

## Troubleshooting

### Common Issues

#### 1. Azure OpenAI Configuration Error

**Error:** `Multi-agent system not initialized`

**Solution:**
```bash
# Verify environment variables are set
echo $AZURE_OPENAI_KEY
echo $AZURE_OPENAI_ENDPOINT

# Test connection
curl https://your-resource.openai.azure.com/openai/deployments?api-version=2024-02-01 \
  -H "api-key: $AZURE_OPENAI_KEY"
```

#### 2. Container Health Check Failing

**Error:** `Container unhealthy`

**Solution:**
```bash
# Check logs
docker logs mulagent

# Test health endpoint
curl http://localhost:8000/health

# Verify configuration is loaded
curl http://localhost:8000/config
```

#### 3. High Latency

**Issue:** Slow response times

**Solutions:**
- Increase container resources (CPU/memory)
- Enable response caching
- Use GPT-3.5-turbo for simpler tasks
- Implement request queuing

```bash
# Increase resources
az containerapp update \
  --name mulagent-api \
  --resource-group $RESOURCE_GROUP \
  --cpu 2.0 \
  --memory 4.0Gi
```

#### 4. Configuration Not Loading

**Error:** `Configuration file not found`

**Solution:**
```bash
# Verify config files are in image
docker run --rm mulagent:latest ls -la /app/config

# Test config loading
docker run --rm mulagent:latest python -c "from src.config_loader import config_loader; print(config_loader.get_vm_pattern('ci_templates'))"
```

### Debug Mode

Enable verbose logging:

```bash
# Local
python src/main.py --interactive --verbose

# Docker
docker run -e LOG_LEVEL=DEBUG mulagent:latest

# Azure Container Apps
az containerapp update \
  --name mulagent-api \
  --resource-group $RESOURCE_GROUP \
  --env-vars LOG_LEVEL=DEBUG
```

### Performance Tuning

1. **Optimize Token Usage:**
   - Use shorter system prompts
   - Implement response caching
   - Use streaming for long responses

2. **Scale Horizontally:**
   - Increase max replicas
   - Implement load balancing
   - Use Azure Front Door

3. **Cache Configuration:**
   - Configuration is cached by default
   - Reload with `config_loader.reload_all()`

---

## Security Best Practices

1. **Secrets Management:**
   - Use Azure Key Vault for secrets
   - Never commit `.env` files
   - Rotate API keys regularly

2. **Network Security:**
   - Use VNet integration
   - Enable private endpoints
   - Restrict ingress to specific IPs

3. **Authentication:**
   - Implement Azure AD authentication
   - Use API keys for portal integration
   - Enable CORS only for specific origins

4. **Monitoring:**
   - Enable audit logging
   - Set up security alerts
   - Monitor for unusual patterns

---

## Backup and Recovery

### Configuration Backup

```bash
# Backup configuration
az storage blob upload-batch \
  --destination config-backup \
  --source ./config \
  --account-name mulagentstorage
```

### Disaster Recovery

1. **Automated Backups:**
   - Container images in ACR (geo-replicated)
   - Configuration in Git
   - Secrets in Key Vault (with backup)

2. **Recovery Steps:**
   ```bash
   # Restore from latest image
   az containerapp update \
     --name mulagent-api \
     --resource-group $RESOURCE_GROUP \
     --image $ACR_NAME.azurecr.io/mulagent:latest
   
   # Restore configuration from Git
   git checkout main
   git pull origin main
   ```

---

## Next Steps

1. Set up CI/CD pipeline (GitHub Actions / Azure DevOps)
2. Implement rate limiting
3. Add authentication layer
4. Set up automated testing
5. Configure backups and monitoring

See [README.md](README.md) for usage examples and API documentation.
