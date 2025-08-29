
# tests/test_api/test_agent.py
"""
Test cases for AI agent functionality.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.local_agent import LocalSQLAgentService
from app.models.schemas import QueryComplexity

@pytest.mark.asyncio
class TestLocalSQLAgent:
    """Test cases for local SQL agent service"""
    
    @pytest.fixture
    async def agent_service(self, mock_database_service, mock_settings):
        """Create agent service for testing"""
        
        with patch('app.services.local_agent.get_settings', return_value=mock_settings):
            service = LocalSQLAgentService(mock_database_service)
            
            # Mock the LLM and chain
            service.llm = MagicMock()
            service.sql_chain = MagicMock()
            service.schema_info = {
                "tables": {
                    "fact_sales": {"columns": [{"name": "total_amount", "type": "NUMBER"}]},
                    "dim_store": {"columns": [{"name": "store_name", "type": "VARCHAR"}]}
                }
            }
            
            return service
    
    @pytest.mark.unit
    async def test_agent_initialization(self, mock_database_service, mock_settings):
        """Test agent service initialization"""
        
        with patch('app.services.local_agent.get_settings', return_value=mock_settings), \
             patch.object(LocalSQLAgentService, '_test_ollama_connection', return_value=True), \
             patch.object(LocalSQLAgentService, '_test_llm', return_value="Test response"):
            
            service = LocalSQLAgentService(mock_database_service)
            
            # Mock the initialization process
            with patch('langchain_community.llms.Ollama'), \
                 patch('langchain.chains.SQLDatabaseChain'), \
                 patch('sqlalchemy.create_engine'):
                
                await service.initialize()
                
                # Verify initialization completed
                assert service.stats['total_queries'] == 0
                assert service.stats['model_used'] == "ollama:codellama:7b"
    
    @pytest.mark.unit
    async def test_process_simple_query(self, agent_service):
        """Test processing a simple query"""
        
        # Mock the AI chain execution
        agent_service._execute_ai_chain = AsyncMock(return_value={
            'result': 'SELECT SUM(total_amount) FROM fact_sales',
            'intermediate_steps': []
        })
        
        # Mock database execution
        agent_service.database_service.execute_query = AsyncMock(return_value=(
            [{'total_revenue': 45000.50}], 100.0
        ))
        
        result = await agent_service.process_query(
            question="What was the total revenue?",
            max_rows=100,
            include_sql=True
        )
        
        assert result['question'] == "What was the total revenue?"
        assert result['row_count'] == 1
        assert 'sql_query' in result
        assert result['complexity'] == QueryComplexity.SIMPLE
        assert len(result['results']) == 1
    
    @pytest.mark.unit
    async def test_query_complexity_estimation(self, agent_service):
        """Test query complexity estimation"""
        
        # Simple query
        complexity = agent_service._estimate_complexity("What is the total revenue?")
        assert complexity == QueryComplexity.SIMPLE
        
        # Moderate query
        complexity = agent_service._estimate_complexity("Show me top 5 stores by revenue")
        assert complexity == QueryComplexity.MODERATE
        
        # Complex query
        complexity = agent_service._estimate_complexity("Show me revenue trends over time by region")
        assert complexity == QueryComplexity.COMPLEX
    
    @pytest.mark.unit
    async def test_question_preprocessing(self, agent_service):
        """Test question preprocessing"""
        
        # Test common phrase replacements
        processed = agent_service._preprocess_question("What was revenue last month?")
        assert "previous month" in processed
        
        processed = agent_service._preprocess_question("Show me best selling products")
        assert "highest sales" in processed
        
        # Test comparison detection
        processed = agent_service._preprocess_question("Compare sales vs revenue")
        assert "comparison data" in processed.lower()
    
    @pytest.mark.unit
    async def test_sql_extraction(self, agent_service):
        """Test SQL extraction from AI responses"""
        
        # Test SQL in code blocks
        ai_result = {
            'result': '```sql\nSELECT * FROM fact_sales\n```'
        }
        sql = agent_service._extract_sql_from_result(ai_result)
        assert sql == "SELECT * FROM fact_sales"
        
        # Test SQL in intermediate steps
        ai_result = {
            'intermediate_steps': [{'sql_cmd': 'SELECT COUNT(*) FROM dim_store'}]
        }
        sql = agent_service._extract_sql_from_result(ai_result)
        assert sql == "SELECT COUNT(*) FROM dim_store"
    
    @pytest.mark.unit
    async def test_sql_cleaning_and_validation(self, agent_service):
        """Test SQL cleaning and validation"""
        
        # Test basic cleaning
        dirty_sql = "  SELECT * FROM fact_sales  -- comment\n  "
        clean_sql = agent_service._clean_sql(dirty_sql)
        assert clean_sql == "SELECT * FROM fact_sales;"
        
        # Test dangerous SQL rejection
        with pytest.raises(ValueError, match="Dangerous SQL keyword"):
            agent_service._clean_sql("DROP TABLE users")
        
        with pytest.raises(ValueError, match="not a SELECT statement"):
            agent_service._clean_sql("INSERT INTO table VALUES (1)")
    
    @pytest.mark.unit
    async def test_error_handling(self, agent_service):
        """Test error handling and suggestions"""
        
        # Test timeout handling
        agent_service._execute_ai_chain = AsyncMock(side_effect=asyncio.TimeoutError())
        
        result = await agent_service.process_query(
            question="Test timeout",
            timeout_seconds=1
        )
        
        assert 'error' in result
        assert result['error'] == 'Query timed out'
        assert 'suggestions' in result
    
    @pytest.mark.unit
    async def test_performance_tracking(self, agent_service):
        """Test performance statistics tracking"""
        
        # Mock successful query
        agent_service._execute_ai_chain = AsyncMock(return_value={
            'result': 'SELECT 1'
        })
        agent_service.database_service.execute_query = AsyncMock(return_value=(
            [{'result': 1}], 50.0
        ))
        
        # Process multiple queries
        for i in range(5):
            await agent_service.process_query(f"Test query {i}")
        
        stats = agent_service.get_statistics()
        
        assert stats['total_queries'] == 5
        assert stats['successful_queries'] == 5
        assert stats['failed_queries'] == 0
        assert stats['success_rate'] == 100.0
        assert stats['avg_response_time'] > 0
    
    @pytest.mark.unit
    def test_error_suggestions_generation(self, agent_service):
        """Test error suggestion generation"""
        
        # Column not found error
        suggestions = agent_service._generate_error_suggestions(
            "Show me invalid_column",
            "Column 'invalid_column' not found"
        )
        assert any("column" in s.lower() for s in suggestions)
        
        # Timeout error
        suggestions = agent_service._generate_error_suggestions(
            "Large query",
            "Query execution timeout"
        )
        assert any("smaller" in s.lower() or "specific" in s.lower() for s in suggestions)
    
    @pytest.mark.unit
    def test_result_postprocessing(self, agent_service):
        """Test result post-processing"""
        
        raw_results = [
            {
                'total_amount': 1234.567,
                'sale_date': datetime(2024, 1, 15),
                'store_name': 'Test Store',
                'null_value': None
            }
        ]
        
        processed = agent_service._postprocess_results(raw_results, 100)
        
        assert len(processed) == 1
        result = processed[0]
        
        # Check formatting
        assert result['Total Amount'] == 1234.57  # Rounded to 2 decimal places
        assert result['Sale Date'] == '2024-01-15T00:00:00'  # ISO format
        assert result['Store Name'] == 'Test Store'  # Title case key
        assert result['Null Value'] == 'N/A'  # Null handling

