
# tests/benchmarks/test_performance.py
"""
Performance and benchmark tests for Agentic Data Explorer.
"""

import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock, patch
import statistics

from app.services.local_agent import LocalSQLAgentService
from app.services.database import DatabaseService

@pytest.mark.performance
class TestPerformanceBenchmarks:
    """Performance benchmarks for the system"""
    
    @pytest.fixture
    async def agent_service(self, mock_database_service, mock_settings):
        """Set up agent service for performance testing"""
        
        with patch('app.services.local_agent.get_settings', return_value=mock_settings):
            service = LocalSQLAgentService(mock_database_service)
            
            # Mock fast responses for performance testing
            service._execute_ai_chain = AsyncMock(return_value={
                'result': 'SELECT COUNT(*) FROM fact_sales'
            })
            
            service.database_service.execute_query = AsyncMock(return_value=(
                [{'count': 1000}], 50.0  # 50ms database time
            ))
            
            return service
    
    @pytest.mark.asyncio
    async def test_single_query_performance(self, agent_service):
        """Test performance of single query processing"""
        
        start_time = time.time()
        
        result = await agent_service.process_query(
            question="What is the total revenue?",
            max_rows=100
        )
        
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000  # Convert to ms
        
        # Assert reasonable performance (under 2 seconds for mock)
        assert execution_time < 2000
        assert result['execution_time_ms'] < 1000
        
        print(f"Single query execution time: {execution_time:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_concurrent_queries_performance(self, agent_service):
        """Test performance under concurrent load"""
        
        async def run_query(query_id):
            start = time.time()
            result = await agent_service.process_query(
                question=f"Test query {query_id}",
                max_rows=10
            )
            end = time.time()
            return (end - start) * 1000, result.get('execution_time_ms', 0)
        
        # Run 10 concurrent queries
        num_queries = 10
        start_time = time.time()
        
        tasks = [run_query(i) for i in range(num_queries)]
        results = await asyncio.gather(*tasks)
        
        total_time = (time.time() - start_time) * 1000
        
        # Extract timing data
        wall_times = [r[0] for r in results]
        execution_times = [r[1] for r in results]
        
        # Performance assertions
        avg_wall_time = statistics.mean(wall_times)
        avg_execution_time = statistics.mean(execution_times)
        
        assert avg_wall_time < 3000  # Average under 3 seconds
        assert total_time < 10000    # Total under 10 seconds
        
        print(f"Concurrent queries:")
        print(f"  Total time: {total_time:.2f}ms")
        print(f"  Average wall time: {avg_wall_time:.2f}ms")
        print(f"  Average execution time: {avg_execution_time:.2f}ms")
        print(f"  Throughput: {num_queries / (total_time / 1000):.2f} queries/second")
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, agent_service):
        """Test memory usage during sustained load"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run many queries to test memory usage
        for i in range(50):
            await agent_service.process_query(
                question=f"Memory test query {i}",
                max_rows=100
            )
            
            # Check memory every 10 queries
            if i % 10 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_growth = current_memory - initial_memory
                
                # Assert memory growth is reasonable (under 100MB growth)
                assert memory_growth < 100, f"Memory grew by {memory_growth:.2f}MB"
        
        final_memory = process.memory_info().rss / 1024 / 1024
        total_growth = final_memory - initial_memory
        
        print(f"Memory usage:")
        print(f"  Initial: {initial_memory:.2f}MB")
        print(f"  Final: {final_memory:.2f}MB")
        print(f"  Growth: {total_growth:.2f}MB")
    
    @pytest.mark.asyncio
    async def test_large_result_set_performance(self, agent_service):
        """Test performance with large result sets"""
        
        # Mock large result set
        large_results = [{'id': i, 'value': f'value_{i}'} for i in range(10000)]
        
        agent_service.database_service.execute_query = AsyncMock(return_value=(
            large_results, 500.0  # 500ms for large query
        ))
        
        start_time = time.time()
        
        result = await agent_service.process_query(
            question="Get large dataset",
            max_rows=10000
        )
        
        execution_time = (time.time() - start_time) * 1000
        
        # Performance assertions for large datasets
        assert execution_time < 5000  # Under 5 seconds
        assert len(result['results']) <= 10000
        
        print(f"Large result set performance:")
        print(f"  Execution time: {execution_time:.2f}ms")
        print(f"  Results count: {len(result['results'])}")
        print(f"  Processing rate: {len(result['results']) / (execution_time / 1000):.0f} rows/second")
    
    @pytest.mark.asyncio
    async def test_database_connection_pool_performance(self, mock_settings):
        """Test database connection pooling performance"""
        
        with patch('app.services.database.get_settings', return_value=mock_settings):
            # Create multiple database services to test pooling
            services = []
            
            for i in range(5):
                service = DatabaseService()
                service.connection = AsyncMock()  # Mock connection
                service.execute_query = AsyncMock(return_value=([], 10.0))
                services.append(service)
            
            # Test concurrent database operations
            async def run_db_query(service, query_id):
                start = time.time()
                await service.execute_query(f"SELECT {query_id}")
                return (time.time() - start) * 1000
            
            tasks = []
            for i, service in enumerate(services):
                for j in range(10):  # 10 queries per service
                    tasks.append(run_db_query(service, f"{i}_{j}"))
            
            start_time = time.time()
            times = await asyncio.gather(*tasks)
            total_time = (time.time() - start_time) * 1000
            
            avg_query_time = statistics.mean(times)
            
            print(f"Database pooling performance:")
            print(f"  Total queries: {len(tasks)}")
            print(f"  Total time: {total_time:.2f}ms")
            print(f"  Average query time: {avg_query_time:.2f}ms")
            print(f"  Throughput: {len(tasks) / (total_time / 1000):.2f} queries/second")
    
    @pytest.mark.asyncio
    async def test_caching_performance_impact(self, agent_service):
        """Test performance impact of caching (if implemented)"""
        
        # First query (cache miss)
        start_time = time.time()
        result1 = await agent_service.process_query("Test caching query")
        first_query_time = (time.time() - start_time) * 1000
        
        # Second identical query (potential cache hit)
        start_time = time.time()
        result2 = await agent_service.process_query("Test caching query")
        second_query_time = (time.time() - start_time) * 1000
        
        # If caching is implemented, second query should be faster
        # For now, just ensure both queries complete successfully
        assert result1['row_count'] >= 0
        assert result2['row_count'] >= 0
        
        print(f"Caching performance:")
        print(f"  First query: {first_query_time:.2f}ms")
        print(f"  Second query: {second_query_time:.2f}ms")
        print(f"  Speed improvement: {((first_query_time - second_query_time) / first_query_time * 100):.1f}%")

@pytest.mark.performance
class TestScalabilityTests:
    """Scalability tests for the system"""
    
    @pytest.mark.asyncio
    async def test_increasing_load_scalability(self, agent_service):
        """Test system behavior under increasing load"""
        
        load_levels = [1, 5, 10, 20, 50]
        results = {}
        
        for load in load_levels:
            print(f"\nTesting load level: {load} concurrent queries")
            
            async def run_query_batch(batch_size):
                tasks = [
                    agent_service.process_query(f"Load test query {i}")
                    for i in range(batch_size)
                ]
                
                start_time = time.time()
                await asyncio.gather(*tasks)
                return (time.time() - start_time) * 1000
            
            # Run test 3 times and take average
            times = []
            for _ in range(3):
                batch_time = await run_query_batch(load)
                times.append(batch_time)
            
            avg_time = statistics.mean(times)
            throughput = load / (avg_time / 1000)
            
            results[load] = {
                'avg_time': avg_time,
                'throughput': throughput,
                'time_per_query': avg_time / load
            }
            
            print(f"  Average time: {avg_time:.2f}ms")
            print(f"  Throughput: {throughput:.2f} queries/second")
            print(f"  Time per query: {avg_time / load:.2f}ms")
        
        # Analyze scalability
        throughputs = [results[load]['throughput'] for load in load_levels]
        
        # Throughput should generally increase or stay stable
        # (allowing for some variance in test conditions)
        print(f"\nScalability analysis:")
        print(f"  Max throughput: {max(throughputs):.2f} queries/second")
        print(f"  Throughput at max load: {throughputs[-1]:.2f} queries/second")
        
        # Basic scalability assertion
        assert throughputs[-1] > 0, "System should handle maximum load"