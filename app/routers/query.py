# app/routers/query.py
"""
Query router for natural language to SQL conversion and execution.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, Any, List
import logging
from datetime import datetime
import asyncio

from app.models.schemas import (
    QueryRequest, 
    QueryResponse, 
    QueryError, 
    ExampleQueriesResponse,
    QueryComplexity
)
from app.services.database import DatabaseService
from app.services.local_agent import LocalSQLAgentService

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependency injection - these will be provided by main.py
async def get_database_service() -> DatabaseService:
    """Get database service - will be overridden by main.py"""
    pass

async def get_agent_service() -> LocalSQLAgentService:
    """Get agent service - will be overridden by main.py"""
    pass

@router.post("/query", response_model=QueryResponse)
async def process_natural_language_query(
    request: QueryRequest,
    agent_service: LocalSQLAgentService = Depends(get_agent_service)
):
    """
    🤖 Process natural language query and return results
    
    Convert natural language questions into SQL queries, execute them,
    and return structured results with metadata.
    
    **Example Questions:**
    - "What was the total revenue last month?"
    - "Show me the top 5 stores by sales"
    - "Which product category has the highest average order value?"
    """
    
    try:
        logger.info(f"🔍 Processing query: '{request.question}'")
        
        # Process query through AI agent
        result = await agent_service.process_query(
            question=request.question,
            max_rows=request.max_rows,
            include_sql=request.include_sql,
            timeout_seconds=request.timeout_seconds
        )
        
        # Check if processing was successful
        if 'error' in result:
            logger.warning(f"⚠️ Query processing failed: {result['error']}")
            return QueryResponse(
                question=request.question,
                sql_query=result.get('sql_query') if request.include_sql else None,
                results=[],
                row_count=0,
                execution_time_ms=result.get('execution_time_ms', 0),
                complexity=result.get('complexity', QueryComplexity.SIMPLE),
                timestamp=datetime.now(),
                metadata={
                    "error": result['error'],
                    "error_type": result.get('error_type'),
                    "suggestions": result.get('suggestions', [])
                }
            )
        
        # Return successful response
        response = QueryResponse(
            question=result['question'],
            sql_query=result.get('sql_query') if request.include_sql else None,
            results=result['results'],
            row_count=result['row_count'],
            execution_time_ms=result['execution_time_ms'],
            complexity=result['complexity'],
            timestamp=result['timestamp'],
            metadata=result.get('metadata')
        )
        
        logger.info(f"✅ Query processed successfully: {response.row_count} rows returned")
        return response
        
    except asyncio.TimeoutError:
        logger.error(f"⏰ Query timed out after {request.timeout_seconds}s")
        raise HTTPException(
            status_code=408,
            detail={
                "error": "Query execution timed out",
                "timeout_seconds": request.timeout_seconds,
                "suggestions": [
                    "Try asking a simpler question",
                    "Reduce the time range in your question",
                    "Ask for fewer results"
                ]
            }
        )
        
    except Exception as e:
        logger.error(f"💥 Unexpected error processing query: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error during query processing",
                "message": str(e),
                "suggestions": [
                    "Check if your question is clearly phrased",
                    "Try rephrasing using simpler terms",
                    "Contact support if the issue persists"
                ]
            }
        )

@router.get("/query/examples", response_model=ExampleQueriesResponse)
async def get_example_queries():
    """
    📚 Get example queries organized by category
    
    Returns curated example questions that work well with the retail analytics data.
    """
    
    examples = {
        "Revenue & Sales": [
            "What was the total revenue last month?",
            "Show me monthly revenue for the past 6 months",
            "Which store has the highest total sales?",
            "What's the average order value across all stores?",
            "How much revenue did we generate from electronics category?"
        ],
        
        "Product Analysis": [
            "Which product category has the highest sales?",
            "Show me the top 10 best-selling products",
            "What's the average price by product category?",
            "Which products have the lowest sales volume?",
            "Compare sales between clothing and electronics categories"
        ],
        
        "Store Performance": [
            "Show me the top 5 stores by revenue",
            "Which region has the highest sales?",
            "Compare store performance between large and small stores",
            "What's the average transaction value per store?",
            "Which stores are underperforming?"
        ],
        
        "Time Analysis": [
            "How do weekend sales compare to weekday sales?",
            "Show me sales trends by month",
            "What day of the week has the highest sales?",
            "Compare this year's sales to last year",
            "What was our best sales day?"
        ],
        
        "Customer Insights": [
            "What's the average quantity per transaction?",
            "How many transactions did we process last month?",
            "What's the most popular payment method?",
            "Show me customer segment distribution",
            "What's the average discount rate applied?"
        ]
    }
    
    tips = [
        "Use specific time periods like 'last month' or 'this year'",
        "Ask for 'top N' results to get manageable data sets",
        "Use comparison words like 'compare', 'versus', 'highest', 'lowest'",
        "Be specific about metrics: 'revenue', 'sales volume', 'average order value'",
        "You can ask for data 'by category', 'by store', 'by region', etc.",
        "Include SQL in response by setting include_sql=true for learning"
    ]
    
    return ExampleQueriesResponse(
        categories=examples,
        tips=tips,
        timestamp=datetime.now()
    )

@router.get("/query/stats")
async def get_query_statistics(
    agent_service: LocalSQLAgentService = Depends(get_agent_service)
):
    """
    📊 Get query processing statistics and performance metrics
    """
    try:
        stats = agent_service.get_statistics()
        
        return {
            "statistics": stats,
            "timestamp": datetime.now(),
            "status": "active"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving statistics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve query statistics"
        )

@router.post("/query/test")
async def test_ai_agent(
    agent_service: LocalSQLAgentService = Depends(get_agent_service),
    database_service: DatabaseService = Depends(get_database_service)
):
    """
    🧪 Test the AI agent and database connectivity
    
    Runs basic connectivity and functionality tests.
    """
    
    test_results = {
        "timestamp": datetime.now(),
        "tests": {}
    }
    
    try:
        # Test database connection
        logger.info("Testing database connection...")
        db_healthy = await database_service.test_connection()
        test_results["tests"]["database_connection"] = {
            "status": "✅ PASS" if db_healthy else "❌ FAIL",
            "healthy": db_healthy
        }
        
        # Test AI agent with simple query
        logger.info("Testing AI agent...")
        test_query = "SELECT COUNT(*) as total_transactions FROM fact_sales"
        
        try:
            test_result = await agent_service.process_query(
                question="How many total transactions are in the database?",
                max_rows=1,
                timeout_seconds=10
            )
            
            agent_working = 'error' not in test_result and len(test_result.get('results', [])) > 0
            test_results["tests"]["ai_agent"] = {
                "status": "✅ PASS" if agent_working else "❌ FAIL",
                "working": agent_working,
                "test_result": test_result.get('results', [])[:1] if agent_working else None,
                "execution_time_ms": test_result.get('execution_time_ms', 0)
            }
            
        except Exception as e:
            test_results["tests"]["ai_agent"] = {
                "status": "❌ FAIL",
                "working": False,
                "error": str(e)
            }
        
        # Test schema access
        logger.info("Testing schema access...")
        try:
            schema_info = await database_service.get_schema_info()
            schema_accessible = 'tables' in schema_info and len(schema_info['tables']) > 0
            
            test_results["tests"]["schema_access"] = {
                "status": "✅ PASS" if schema_accessible else "❌ FAIL",
                "accessible": schema_accessible,
                "table_count": len(schema_info.get('tables', {})),
                "tables": list(schema_info.get('tables', {}).keys())
            }
            
        except Exception as e:
            test_results["tests"]["schema_access"] = {
                "status": "❌ FAIL",
                "accessible": False,
                "error": str(e)
            }
        
        # Overall status
        all_tests_passed = all(
            test.get("status", "").startswith("✅") 
            for test in test_results["tests"].values()
        )
        
        test_results["overall_status"] = "✅ ALL SYSTEMS OPERATIONAL" if all_tests_passed else "⚠️ SOME ISSUES DETECTED"
        test_results["ready_for_queries"] = all_tests_passed
        
        return test_results
        
    except Exception as e:
        logger.error(f"Test execution failed: {str(e)}")
        test_results["overall_status"] = "❌ TEST EXECUTION FAILED"
        test_results["error"] = str(e)
        
        raise HTTPException(
            status_code=500,
            detail=test_results
        )

@router.get("/schema")
async def get_database_schema(
    database_service: DatabaseService = Depends(get_database_service)
):
    """
    🗃️ Get database schema information
    
    Returns information about available tables and columns for reference.
    """
    try:
        schema_info = await database_service.get_schema_info()
        
        # Format for better readability
        formatted_schema = {
            "database": schema_info.get("schema", "Unknown"),
            "tables": {},
            "summary": {
                "total_tables": len(schema_info.get("tables", {})),
                "table_names": list(schema_info.get("tables", {}).keys())
            }
        }
        
        # Add detailed table information
        for table_name, table_info in schema_info.get("tables", {}).items():
            formatted_schema["tables"][table_name] = {
                "type": table_info.get("type", "TABLE"),
                "column_count": len(table_info.get("columns", [])),
                "columns": [
                    {
                        "name": col["name"],
                        "type": col["type"],
                        "nullable": col.get("nullable", True)
                    }
                    for col in table_info.get("columns", [])
                ]
            }
        
        return formatted_schema
        
    except Exception as e:
        logger.error(f"Failed to retrieve schema: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve database schema: {str(e)}"
        )