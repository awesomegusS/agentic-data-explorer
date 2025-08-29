# app/main.py
"""
FastAPI main application for Agentic Data Explorer.
Local AI-powered natural language to SQL interface.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import logging
from datetime import datetime

from app.routers import query, health
from app.services.database import DatabaseService
from app.services.local_agent import LocalSQLAgentService
from app.utils.config import get_settings
from app.utils.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Global services
database_service: DatabaseService = None
agent_service: LocalSQLAgentService = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management - startup and shutdown"""
    # Startup
    logger.info("🚀 Starting Agentic Data Explorer API")
    
    global database_service, agent_service
    
    try:
        # Initialize database service
        logger.info("Initializing database connection...")
        database_service = DatabaseService()
        await database_service.connect()
        logger.info("✅ Database connection established")
        
        # Initialize local AI agent
        logger.info("Initializing local AI agent...")
        agent_service = LocalSQLAgentService(database_service)
        await agent_service.initialize()
        logger.info("✅ Local AI agent initialized")
        
        logger.info("🎉 Application startup complete!")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Agentic Data Explorer API")
    
    if agent_service:
        await agent_service.cleanup()
        logger.info("✅ AI agent cleaned up")
    
    if database_service:
        await database_service.disconnect()
        logger.info("✅ Database disconnected")

# Create FastAPI app
app = FastAPI(
    title="🔍 Agentic Data Explorer",
    description="""
    ## 🤖 AI-Powered Retail Data Analysis
    
    Ask questions about your retail data in natural language and get instant insights!
    
    **Powered by:**
    - 🏔️ Snowflake data warehouse
    - 🔧 dbt transformations  
    - 🤖 Local AI models (Ollama)
    - ⚡ FastAPI + LangChain
    
    ## 🎯 Example Questions
    
    - *"What was the total revenue last month?"*
    - *"Which product category has the highest sales?"*
    - *"Show me the top 5 stores by revenue"*
    - *"How do weekend sales compare to weekday sales?"*
    
    ## 🚀 Features
    
    - **Natural Language Queries** - No SQL knowledge required
    - **Local AI Processing** - Private, fast, no API costs
    - **Clean Data Pipeline** - Quality-assured dimensional model
    - **Real-time Insights** - Instant query responses
    """,
    version="1.0.0",
    contact={
        "name": "Data Team",
        "email": "data-team@company.com",
    },
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    query.router,
    prefix="/api/v1",
    tags=["queries"]
)

app.include_router(
    health.router,
    prefix="/api/v1",
    tags=["health"]
)

# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Welcome endpoint with API information"""
    return {
        "message": "🔍 Agentic Data Explorer API",
        "description": "AI-powered retail data analysis with natural language queries",
        "version": "1.0.0",
        "status": "active",
        "endpoints": {
            "docs": "/docs",
            "health": "/api/v1/health",
            "query": "/api/v1/query",
            "examples": "/api/v1/query/examples"
        },
        "example_queries": [
            "What was the total revenue last month?",
            "Which product category has the highest sales?",
            "Show me the top 5 stores by revenue",
            "How do weekend sales compare to weekday sales?"
        ],
        "ai_model": "Local Ollama (CodeLlama + Llama 3.1)",
        "timestamp": datetime.now().isoformat()
    }

# Dependency injection
async def get_database_service() -> DatabaseService:
    """Get database service instance"""
    if database_service is None:
        raise HTTPException(
            status_code=503,
            detail="Database service not available"
        )
    return database_service

async def get_agent_service() -> LocalSQLAgentService:
    """Get AI agent service instance"""
    if agent_service is None:
        raise HTTPException(
            status_code=503,
            detail="AI agent service not available"
        )
    return agent_service

# Override dependency injection for routers
from app.routers.query import get_database_service as query_get_db, get_agent_service as query_get_agent
from app.routers.health import get_database_service as health_get_db, get_agent_service as health_get_agent

app.dependency_overrides[query_get_db] = get_database_service
app.dependency_overrides[query_get_agent] = get_agent_service
app.dependency_overrides[health_get_db] = get_database_service
app.dependency_overrides[health_get_agent] = get_agent_service

# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "status_code": 500,
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    settings = get_settings()
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )