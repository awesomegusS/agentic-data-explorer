# app/models/schemas.py
"""
Pydantic models for request/response validation.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

class QueryComplexity(str, Enum):
    """Query complexity classification"""
    SIMPLE = "simple"      # Single table, basic aggregation
    MODERATE = "moderate"  # Multiple tables, joins
    COMPLEX = "complex"    # Multiple joins, subqueries, analytics

class QueryRequest(BaseModel):
    """Natural language query request"""
    
    question: str = Field(
        ...,
        description="Natural language question about the data",
        example="What was the total revenue last month?",
        min_length=3,
        max_length=500
    )
    
    max_rows: Optional[int] = Field(
        default=100,
        description="Maximum number of rows to return",
        ge=1,
        le=1000
    )
    
    include_sql: Optional[bool] = Field(
        default=False,
        description="Whether to include the generated SQL in the response"
    )
    
    timeout_seconds: Optional[int] = Field(
        default=90,
        description="Query timeout in seconds",
        ge=5,
        le=120
    )
    
    @validator('question')
    def validate_question(cls, v):
        """Validate question content"""
        if not v.strip():
            raise ValueError('Question cannot be empty')
        
        # Basic SQL injection prevention
        dangerous_patterns = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE TABLE', 'INSERT', 'UPDATE']
        question_upper = v.upper()
        for pattern in dangerous_patterns:
            if pattern in question_upper:
                raise ValueError(f'Question contains potentially dangerous keyword: {pattern}')
        
        return v.strip()

class QueryResponse(BaseModel):
    """Query response with results and metadata"""
    
    question: str = Field(description="Original question")
    
    sql_query: Optional[str] = Field(
        default=None,
        description="Generated SQL query (if requested)"
    )
    
    results: List[Dict[str, Any]] = Field(
        description="Query results as list of dictionaries"
    )
    
    row_count: int = Field(description="Number of rows returned")
    
    execution_time_ms: float = Field(description="Total execution time in milliseconds")
    
    complexity: QueryComplexity = Field(description="Estimated query complexity")
    
    timestamp: datetime = Field(description="Response timestamp")
    
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata about the query execution"
    )

class QueryError(BaseModel):
    """Error response for failed queries"""
    
    error: str = Field(description="Error message")
    error_type: str = Field(description="Type of error")
    question: Optional[str] = Field(default=None, description="Original question")
    suggestions: Optional[List[str]] = Field(default=None, description="Suggested fixes")
    timestamp: datetime = Field(description="Error timestamp")

class HealthResponse(BaseModel):
    """Health check response"""
    
    status: str = Field(description="Overall service status")
    timestamp: datetime = Field(description="Health check timestamp")
    version: str = Field(description="API version")
    services: Dict[str, str] = Field(description="Individual service statuses")
    uptime_seconds: Optional[float] = Field(default=None, description="Service uptime")

class ExampleQueriesResponse(BaseModel):
    """Example queries response"""
    
    categories: Dict[str, List[str]] = Field(description="Example queries by category")
    tips: List[str] = Field(description="Tips for writing good questions")
    timestamp: datetime = Field(description="Response timestamp")