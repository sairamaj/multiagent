"""
REST API for Multi-Agent System

Provides HTTP endpoints for portal integration.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from agents import ManagerAgentSystem
from config_loader import config_loader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Multi-Agent DevOps Automation API",
    description="AI-driven multi-agent system for Azure DevOps automation",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global manager system instance
manager_system: Optional[ManagerAgentSystem] = None


# Pydantic models for API
class TaskRequest(BaseModel):
    """Request model for task execution"""
    message: str
    context: Optional[Dict[str, Any]] = None


class TaskResponse(BaseModel):
    """Response model for task execution"""
    success: bool
    task_id: str
    message: str
    summary: Optional[str] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    agents: List[str]
    config_loaded: bool


class ConfigResponse(BaseModel):
    """Configuration information response"""
    vm_patterns: Dict[str, Any]
    blob_retention: Dict[str, Any]
    environment: str


# API Routes

@app.on_event("startup")
async def startup_event():
    """Initialize the multi-agent system on startup"""
    global manager_system
    
    logger.info("Starting Multi-Agent System API")
    
    # Configure Azure OpenAI
    llm_config = {
        "model": os.getenv("AZURE_OPENAI_MODEL", "gpt-4"),
        "api_type": "azure",
        "api_key": os.getenv("AZURE_OPENAI_KEY"),
        "api_base": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
        "temperature": 0.7
    }
    
    # Validate configuration
    if not llm_config["api_key"] or not llm_config["api_base"]:
        logger.error("Azure OpenAI configuration missing!")
        logger.error("Set AZURE_OPENAI_KEY and AZURE_OPENAI_ENDPOINT environment variables")
        # Don't initialize manager system
        return
    
    try:
        manager_system = ManagerAgentSystem(llm_config)
        logger.info("Multi-Agent System initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize manager system: {e}")


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "Multi-Agent DevOps Automation API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if manager_system is not None else "not_initialized",
        version="1.0.0",
        agents=["manager", "azure_agent", "build_agent", "file_agent"],
        config_loaded=True
    )


@app.get("/config", response_model=ConfigResponse)
async def get_config():
    """Get current configuration"""
    try:
        vm_patterns = config_loader.get_all_vm_patterns()
        blob_retention = config_loader.get_all_blob_retention_policies()
        environment = config_loader.environment
        
        return ConfigResponse(
            vm_patterns=vm_patterns,
            blob_retention=blob_retention,
            environment=environment
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading configuration: {str(e)}")


@app.post("/execute", response_model=TaskResponse)
async def execute_task(task: TaskRequest):
    """
    Execute a task through the multi-agent system.
    
    Args:
        task: Task request with natural language message
    
    Returns:
        Task execution result
    """
    if manager_system is None:
        raise HTTPException(
            status_code=503,
            detail="Multi-agent system not initialized. Check Azure OpenAI configuration."
        )
    
    logger.info(f"Received task: {task.message}")
    
    try:
        # Execute task through manager system
        result = manager_system.execute_task(task.message)
        
        # Generate task ID (in production, use UUID and store in database)
        import hashlib
        task_id = hashlib.md5(task.message.encode()).hexdigest()[:8]
        
        return TaskResponse(
            success=result.get("success", False),
            task_id=task_id,
            message=task.message,
            summary=result.get("summary"),
            error=result.get("error")
        )
    
    except Exception as e:
        logger.error(f"Error executing task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/execute/async")
async def execute_task_async(task: TaskRequest, background_tasks: BackgroundTasks):
    """
    Execute a task asynchronously.
    
    Args:
        task: Task request
        background_tasks: FastAPI background tasks
    
    Returns:
        Task ID for status checking
    """
    if manager_system is None:
        raise HTTPException(
            status_code=503,
            detail="Multi-agent system not initialized"
        )
    
    # Generate task ID
    import hashlib
    import time
    task_id = hashlib.md5(f"{task.message}{time.time()}".encode()).hexdigest()[:8]
    
    # Add task to background
    def run_task():
        try:
            result = manager_system.execute_task(task.message)
            logger.info(f"Task {task_id} completed: {result.get('success')}")
            # In production, store result in database for retrieval
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
    
    background_tasks.add_task(run_task)
    
    return {
        "task_id": task_id,
        "status": "queued",
        "message": "Task queued for execution"
    }


@app.get("/agents")
async def list_agents():
    """List available agents"""
    return {
        "agents": [
            {
                "name": "manager",
                "description": "Coordinates between specialized agents",
                "capabilities": ["task delegation", "result synthesis"]
            },
            {
                "name": "azure_agent",
                "description": "Azure resource management",
                "capabilities": ["VM operations", "resource queries", "cleanup"]
            },
            {
                "name": "build_agent",
                "description": "Azure DevOps build monitoring",
                "capabilities": ["pipeline status", "failure analysis", "metrics"]
            },
            {
                "name": "file_agent",
                "description": "File system operations",
                "capabilities": ["file read/write", "directory listing", "search"]
            }
        ]
    }


@app.get("/examples")
async def get_examples():
    """Get example tasks"""
    return {
        "examples": [
            {
                "category": "Azure Resources",
                "tasks": [
                    "List all virtual machines matching the CI template pattern",
                    "Show me VMs that would be deleted in cleanup",
                    "Check which VMs are older than 30 days"
                ]
            },
            {
                "category": "Build Monitoring",
                "tasks": [
                    "Show build failures from the last 7 days",
                    "Analyze build failures and identify patterns",
                    "Get build metrics and success rate"
                ]
            },
            {
                "category": "Storage",
                "tasks": [
                    "Show me what blobs would be cleaned up",
                    "Calculate storage usage for CI artifacts",
                    "List blob retention policies"
                ]
            },
            {
                "category": "Files",
                "tasks": [
                    "List all Python files in the src directory",
                    "Show me configuration files",
                    "Calculate total size of config directory"
                ]
            }
        ]
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    logger.error(f"HTTP error: {exc.status_code} - {exc.detail}")
    return {
        "error": exc.detail,
        "status_code": exc.status_code
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unexpected error: {exc}")
    return {
        "error": "Internal server error",
        "detail": str(exc),
        "status_code": 500
    }


# Run with: uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
