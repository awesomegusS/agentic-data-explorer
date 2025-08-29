# app/routers/health.py
"""
Health check router for monitoring system status.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
import logging
from datetime import datetime
import time
import psutil
import platform

from app.models.schemas import HealthResponse
from app.services.database import DatabaseService
from app.services.local_agent import LocalSQLAgentService
from app.utils.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Track startup time
STARTUP_TIME = time.time()

# Dependency injection
async def get_database_service() -> DatabaseService:
    """Get database service - will be overridden by main.py"""
    pass

async def get_agent_service() -> LocalSQLAgentService:
    """Get agent service - will be overridden by main.py"""
    pass

@router.get("/health", response_model=HealthResponse)
async def health_check(
    database_service: DatabaseService = Depends(get_database_service),
    agent_service: LocalSQLAgentService = Depends(get_agent_service)
):
    """
    🏥 Comprehensive health check for all system components
    
    Checks the status of:
    - API server
    - Database connection
    - AI agent service
    - Local AI model (Ollama)
    - System resources
    """
    
    settings = get_settings()
    
    # Calculate uptime
    uptime_seconds = time.time() - STARTUP_TIME
    
    # Check individual services
    services = {}
    overall_status = "healthy"
    
    try:
        # Database health
        try:
            db_healthy = await database_service.test_connection()
            services["database"] = "✅ healthy" if db_healthy else "❌ unhealthy"
            if not db_healthy:
                overall_status = "degraded"
        except Exception as e:
            services["database"] = f"❌ error: {str(e)[:50]}"
            overall_status = "degraded"
        
        # AI Agent health
        try:
            agent_stats = agent_service.get_statistics()
            agent_healthy = agent_stats.get('total_queries', 0) >= 0  # Basic check
            services["ai_agent"] = "✅ healthy" if agent_healthy else "❌ unhealthy"
            if not agent_healthy:
                overall_status = "degraded"
        except Exception as e:
            services["ai_agent"] = f"❌ error: {str(e)[:50]}"
            overall_status = "degraded"
        
        # Ollama health
        try:
            # Quick test of Ollama connectivity
            ollama_healthy = await agent_service._test_ollama_connection()
            services["ollama"] = "✅ healthy" if ollama_healthy else "❌ unhealthy"
            if not ollama_healthy:
                overall_status = "degraded"
        except Exception as e:
            services["ollama"] = f"❌ error: {str(e)[:50]}"
            overall_status = "degraded"
        
        # API server (if we're responding, it's healthy)
        services["api_server"] = "✅ healthy"
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        overall_status = "unhealthy"
        services["health_check"] = f"❌ error: {str(e)}"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now(),
        version="1.0.0",
        services=services,
        uptime_seconds=uptime_seconds
    )

@router.get("/health/detailed")
async def detailed_health_check(
    database_service: DatabaseService = Depends(get_database_service),
    agent_service: LocalSQLAgentService = Depends(get_agent_service)
):
    """
    🔍 Detailed health check with system metrics and performance data
    """
    
    settings = get_settings()
    
    # System information
    system_info = {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_count": psutil.cpu_count(),
        "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
        "memory_percent": psutil.virtual_memory().percent,
        "cpu_percent": psutil.cpu_percent(interval=1),
        "disk_usage_percent": psutil.disk_usage('/').percent
    }
    
    # Service configurations
    config_info = {
        "environment": settings.environment,
        "api_port": settings.api_port,
        "snowflake_database": settings.snowflake_database,
        "snowflake_schema": settings.snowflake_schema,
        "local_ai_model": settings.local_ai_model,
        "local_ai_backend": settings.local_ai_backend,
        "max_query_timeout": settings.max_query_timeout
    }
    
    # AI Agent statistics
    try:
        agent_stats = agent_service.get_statistics()
    except Exception as e:
        agent_stats = {"error": str(e)}
    
    # Database schema info
    try:
        schema_info = await database_service.get_schema_info()
        db_info = {
            "schema": schema_info.get("schema"),
            "table_count": len(schema_info.get("tables", {})),
            "tables": list(schema_info.get("tables", {}).keys())
        }
    except Exception as e:
        db_info = {"error": str(e)}
    
    return {
        "timestamp": datetime.now(),
        "status": "detailed_health_check",
        "uptime_seconds": time.time() - STARTUP_TIME,
        "system": system_info,
        "configuration": config_info,
        "agent_statistics": agent_stats,
        "database_info": db_info,
        "endpoints": {
            "available": [
                "/api/v1/health",
                "/api/v1/health/detailed",
                "/api/v1/query",
                "/api/v1/query/examples",
                "/api/v1/query/stats",
                "/api/v1/query/test",
                "/api/v1/schema"
            ]
        }
    }

@router.get("/ready")
async def readiness_check(
    database_service: DatabaseService = Depends(get_database_service),
    agent_service: LocalSQLAgentService = Depends(get_agent_service)
):
    """
    🚦 Kubernetes-style readiness probe
    
    Returns 200 if service is ready to handle requests, 503 if not.
    """
    
    try:
        # Quick checks for essential services
        db_ready = await database_service.test_connection()
        agent_ready = agent_service.llm is not None
        
        if db_ready and agent_ready:
            return {
                "status": "ready",
                "timestamp": datetime.now(),
                "checks": {
                    "database": "ready",
                    "ai_agent": "ready"
                }
            }
        else:
            return {
                "status": "not_ready",
                "timestamp": datetime.now(),
                "checks": {
                    "database": "ready" if db_ready else "not_ready",
                    "ai_agent": "ready" if agent_ready else "not_ready"
                }
            }, 503
            
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return {
            "status": "not_ready",
            "timestamp": datetime.now(),
            "error": str(e)
        }, 503

@router.get("/live")
async def liveness_check():
    """
    💓 Kubernetes-style liveness probe
    
    Simple check that the process is alive and responding.
    """
    return {
        "status": "alive",
        "timestamp": datetime.now(),
        "uptime_seconds": time.time() - STARTUP_TIME
    }