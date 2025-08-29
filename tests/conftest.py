# tests/conftest.py
"""
Pytest configuration and shared fixtures for Agentic Data Explorer tests.
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
import pandas as pd
from datetime import datetime, timedelta

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.database import DatabaseService
from app.services.local_agent import LocalSQLAgentService
from app.utils.config import get_settings

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    settings = MagicMock()
    settings.snowflake_user = "test_user"
    settings.snowflake_password = "test_password"
    settings.snowflake_account = "test_account"
    settings.snowflake_database = "test_database"
    settings.snowflake_schema = "test_schema"
    settings.snowflake_warehouse = "test_warehouse"
    settings.snowflake_role = "test_role"
    settings.local_ai_backend = "ollama"
    settings.local_ai_model = "codellama:7b"
    settings.local_ai_host = "localhost"
    settings.local_ai_port = 11434
    settings.local_ai_temperature = 0.1
    settings.local_ai_max_tokens = 1000
    settings.api_port = 8000
    settings.environment = "test"
    settings.log_level = "DEBUG"
    return settings

@pytest.fixture
def sample_sales_data():
    """Generate sample sales data for testing"""
    data = []
    base_date = datetime(2024, 1, 1)
    
    for i in range(100):
        data.append({
            'transaction_id': i + 1,
            'store_id': (i % 10) + 1,
            'product_id': (i % 20) + 1,
            'sale_date': base_date + timedelta(days=i % 365),
            'sale_timestamp': base_date + timedelta(days=i % 365, hours=i % 24),
            'quantity': (i % 5) + 1,
            'unit_price': round(10.0 + (i % 100), 2),
            'total_amount': round((10.0 + (i % 100)) * ((i % 5) + 1), 2),
            'discount_applied': round((i % 10) * 0.5, 2),
            'customer_segment': ['Premium', 'Standard', 'Budget'][i % 3],
            'payment_method': ['Credit Card', 'Debit Card', 'Cash'][i % 3]
        })
    
    return data

@pytest.fixture
def sample_stores_data():
    """Generate sample stores data for testing"""
    return [
        {
            'store_id': i + 1,
            'store_name': f'Store {i + 1:03d}',
            'store_region': ['North', 'South', 'East', 'West', 'Central'][i % 5],
            'store_size': ['Small', 'Medium', 'Large'][i % 3],
            'store_city': f'City {i + 1}',
            'store_state': ['CA', 'NY', 'TX'][i % 3]
        }
        for i in range(10)
    ]

@pytest.fixture
def sample_products_data():
    """Generate sample products data for testing"""
    categories = ['Electronics', 'Clothing', 'Home & Garden', 'Books', 'Sports']
    return [
        {
            'product_id': i + 1,
            'product_name': f'Product {i + 1:03d}',
            'product_category': categories[i % len(categories)],
            'product_brand': f'Brand {chr(65 + (i % 10))}',
            'product_price': round(10.0 + (i % 100), 2),
            'product_status': 'Active'
        }
        for i in range(20)
    ]

@pytest.fixture
def mock_database_service():
    """Mock database service for testing"""
    mock_service = AsyncMock(spec=DatabaseService)
    
    # Mock connection methods
    mock_service.connect = AsyncMock()
    mock_service.disconnect = AsyncMock()
    mock_service.test_connection = AsyncMock(return_value=True)
    
    # Mock query execution
    mock_service.execute_query = AsyncMock(return_value=([], 100.0))
    
    # Mock schema info
    mock_service.get_schema_info = AsyncMock(return_value={
        "schema": "test_schema",
        "tables": {
            "fact_sales": {
                "type": "TABLE",
                "columns": [
                    {"name": "transaction_id", "type": "NUMBER"},
                    {"name": "store_id", "type": "NUMBER"},
                    {"name": "product_id", "type": "NUMBER"},
                    {"name": "total_amount", "type": "NUMBER"}
                ]
            },
            "dim_store": {
                "type": "TABLE",
                "columns": [
                    {"name": "store_id", "type": "NUMBER"},
                    {"name": "store_name", "type": "VARCHAR"},
                    {"name": "store_region", "type": "VARCHAR"}
                ]
            }
        }
    })
    
    return mock_service

@pytest.fixture
def mock_ai_agent_service():
    """Mock AI agent service for testing"""
    mock_service = AsyncMock(spec=LocalSQLAgentService)
    
    # Mock initialization
    mock_service.initialize = AsyncMock()
    mock_service.cleanup = AsyncMock()
    
    # Mock query processing
    mock_service.process_query = AsyncMock(return_value={
        'question': 'test question',
        'results': [{'test_column': 'test_value'}],
        'row_count': 1,
        'execution_time_ms': 150.0,
        'complexity': 'SIMPLE',
        'timestamp': datetime.now(),
        'metadata': {
            'ai_model': 'test_model',
            'sql_generation_time_ms': 50.0,
            'database_query_time_ms': 100.0
        }
    })
    
    # Mock statistics
    mock_service.get_statistics = MagicMock(return_value={
        'total_queries': 10,
        'successful_queries': 9,
        'failed_queries': 1,
        'avg_response_time': 200.0,
        'success_rate': 90.0,
        'error_rate': 10.0
    })
    
    # Mock Ollama connection test
    mock_service._test_ollama_connection = AsyncMock(return_value=True)
    
    return mock_service

@pytest.fixture
def sample_query_response():
    """Sample API query response for testing"""
    return {
        "question": "What was the total revenue last month?",
        "sql_query": "SELECT SUM(total_amount) FROM fact_sales WHERE sale_date >= '2024-01-01'",
        "results": [{"Total Revenue": 45000.50}],
        "row_count": 1,
        "execution_time_ms": 250.5,
        "complexity": "SIMPLE",
        "timestamp": "2024-02-01T10:30:00",
        "metadata": {
            "ai_model": "codellama:7b",
            "sql_generation_time_ms": 150.0,
            "database_query_time_ms": 100.5
        }
    }

@pytest.fixture
def sample_error_response():
    """Sample API error response for testing"""
    return {
        "error": "Column 'invalid_column' not found",
        "error_type": "DatabaseError",
        "suggestions": [
            "Check column names in your question",
            "Try rephrasing with different terms",
            "Ask for available columns"
        ]
    }

# Utility functions for tests
def assert_valid_query_response(response):
    """Assert that a query response has the expected structure"""
    required_fields = ['question', 'results', 'row_count', 'execution_time_ms', 'complexity', 'timestamp']
    
    for field in required_fields:
        assert field in response, f"Missing required field: {field}"
    
    assert isinstance(response['results'], list), "Results should be a list"
    assert isinstance(response['row_count'], int), "Row count should be an integer"
    assert isinstance(response['execution_time_ms'], (int, float)), "Execution time should be numeric"
    assert response['complexity'] in ['SIMPLE', 'MODERATE', 'COMPLEX'], "Invalid complexity value"

def assert_valid_error_response(response):
    """Assert that an error response has the expected structure"""
    required_fields = ['error', 'error_type']
    
    for field in required_fields:
        assert field in response, f"Missing required field: {field}"
    
    assert isinstance(response['error'], str), "Error should be a string"
    assert isinstance(response['error_type'], str), "Error type should be a string"

# Test data generators
class TestDataGenerator:
    """Generate test data for various scenarios"""
    
    @staticmethod
    def generate_large_dataset(num_rows: int = 1000):
        """Generate large dataset for performance testing"""
        import random
        
        data = []
        for i in range(num_rows):
            data.append({
                'id': i,
                'category': random.choice(['A', 'B', 'C', 'D']),
                'value': random.uniform(1, 1000),
                'date': datetime.now() - timedelta(days=random.randint(0, 365))
            })
        return data
    
    @staticmethod
    def generate_edge_case_queries():
        """Generate edge case queries for testing"""
        return [
            "",  # Empty query
            "   ",  # Whitespace only
            "a" * 1000,  # Very long query
            "SELECT * FROM users; DROP TABLE users;",  # SQL injection attempt
            "What is the meaning of life?",  # Non-data question
            "Show me data from table_that_does_not_exist",  # Invalid table
            "Give me 1000000 rows of data",  # Very large request
        ]

# Markers for different test categories
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.performance = pytest.mark.performance
pytest.mark.e2e = pytest.mark.e2e

