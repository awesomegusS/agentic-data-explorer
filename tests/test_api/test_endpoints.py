# tests/test_api/test_endpoints.py
"""
Test cases for API endpoints.
"""

import pytest
import asyncio
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import QueryRequest, QueryResponse

@pytest.mark.asyncio
class TestQueryEndpoints:
    """Test cases for query-related endpoints"""
    
    @pytest.fixture
    def client(self):
        """Test client for API testing"""
        return TestClient(app)
    
    @pytest.mark.unit
    def test_query_endpoint_valid_request(self, client, mock_ai_agent_service, sample_query_response):
        """Test valid query request"""
        
        with patch('app.main.get_agent_service', return_value=mock_ai_agent_service):
            response = client.post(
                "/api/v1/query",
                json={
                    "question": "What was the total revenue last month?",
                    "max_rows": 100,
                    "include_sql": True,
                    "timeout_seconds": 30
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "question" in data
        assert "results" in data
        assert "row_count" in data
        assert "execution_time_ms" in data
    
    @pytest.mark.unit
    def test_query_endpoint_invalid_request(self, client):
        """Test invalid query request"""
        
        # Empty question
        response = client.post(
            "/api/v1/query",
            json={
                "question": "",
                "max_rows": 100
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.unit
    def test_query_endpoint_sql_injection_prevention(self, client):
        """Test SQL injection prevention"""
        
        dangerous_queries = [
            "SELECT * FROM users; DROP TABLE users;",
            "'; DELETE FROM sales; --",
            "UNION SELECT * FROM system_tables"
        ]
        
        for dangerous_query in dangerous_queries:
            response = client.post(
                "/api/v1/query",
                json={"question": dangerous_query}
            )
            
            # Should either reject or sanitize
            assert response.status_code in [400, 422, 200]
            
            if response.status_code == 200:
                # If processed, ensure no dangerous SQL was executed
                data = response.json()
                if "sql_query" in data:
                    sql = data["sql_query"].upper()
                    assert "DROP" not in sql
                    assert "DELETE" not in sql
                    assert "TRUNCATE" not in sql
    
    @pytest.mark.unit
    def test_examples_endpoint(self, client):
        """Test examples endpoint"""
        
        response = client.get("/api/v1/query/examples")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "categories" in data
        assert "tips" in data
        assert isinstance(data["categories"], dict)
        assert isinstance(data["tips"], list)
    
    @pytest.mark.unit
    def test_stats_endpoint(self, client, mock_ai_agent_service):
        """Test statistics endpoint"""
        
        with patch('app.main.get_agent_service', return_value=mock_ai_agent_service):
            response = client.get("/api/v1/query/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "statistics" in data
        stats = data["statistics"]
        
        # Validate statistics structure
        expected_fields = ['total_queries', 'successful_queries', 'failed_queries', 'avg_response_time']
        for field in expected_fields:
            assert field in stats
    
    @pytest.mark.integration
    def test_query_test_endpoint(self, client, mock_database_service, mock_ai_agent_service):
        """Test the AI agent test endpoint"""
        
        with patch('app.main.get_database_service', return_value=mock_database_service), \
             patch('app.main.get_agent_service', return_value=mock_ai_agent_service):
            
            response = client.post("/api/v1/query/test")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "tests" in data
        assert "overall_status" in data
        assert "ready_for_queries" in data
    
    @pytest.mark.unit
    def test_schema_endpoint(self, client, mock_database_service):
        """Test schema information endpoint"""
        
        with patch('app.main.get_database_service', return_value=mock_database_service):
            response = client.get("/api/v1/schema")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "database" in data
        assert "tables" in data
        assert "summary" in data

@pytest.mark.asyncio
class TestHealthEndpoints:
    """Test cases for health check endpoints"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.mark.unit
    def test_basic_health_check(self, client, mock_database_service, mock_ai_agent_service):
        """Test basic health check endpoint"""
        
        with patch('app.main.get_database_service', return_value=mock_database_service), \
             patch('app.main.get_agent_service', return_value=mock_ai_agent_service):
            
            response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "services" in data
        assert "timestamp" in data
        assert "uptime_seconds" in data
    
    @pytest.mark.unit
    def test_detailed_health_check(self, client, mock_database_service, mock_ai_agent_service):
        """Test detailed health check endpoint"""
        
        with patch('app.main.get_database_service', return_value=mock_database_service), \
             patch('app.main.get_agent_service', return_value=mock_ai_agent_service):
            
            response = client.get("/api/v1/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "system" in data
        assert "configuration" in data
        assert "agent_statistics" in data
    
    @pytest.mark.unit
    def test_readiness_probe(self, client, mock_database_service, mock_ai_agent_service):
        """Test Kubernetes readiness probe"""
        
        with patch('app.main.get_database_service', return_value=mock_database_service), \
             patch('app.main.get_agent_service', return_value=mock_ai_agent_service):
            
            response = client.get("/api/v1/ready")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "checks" in data
    
    @pytest.mark.unit
    def test_liveness_probe(self, client):
        """Test Kubernetes liveness probe"""
        
        response = client.get("/api/v1/live")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert data["status"] == "alive"

