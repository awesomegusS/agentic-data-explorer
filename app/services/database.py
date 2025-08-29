# app/services/database.py
"""
Database service for managing Snowflake connections and queries.
Clean implementation without syntax errors.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
import snowflake.connector
from snowflake.connector import DictCursor
import time

from app.utils.config import get_settings

logger = logging.getLogger(__name__)

class DatabaseService:
    """Manages Snowflake database connections and query execution"""
    
    def __init__(self):
        self.settings = get_settings()
        self.connection = None
        self._connection_params = {
            'user': self.settings.snowflake_user,
            'password': self.settings.snowflake_password,
            'account': self.settings.snowflake_account,
            'database': self.settings.snowflake_database,
            'schema': self.settings.snowflake_schema,  # Use analytics schema
            'warehouse': self.settings.snowflake_warehouse,
            'role': self.settings.snowflake_role
        }
    
    async def connect(self) -> None:
        """Establish connection to Snowflake"""
        try:
            logger.info("🔗 Connecting to Snowflake...")
            
            # Run connection in thread pool since it's blocking
            loop = asyncio.get_event_loop()
            self.connection = await loop.run_in_executor(
                None, 
                lambda: snowflake.connector.connect(**self._connection_params)
            )
            
            # Test connection
            await self.execute_query("SELECT CURRENT_VERSION()")
            logger.info("✅ Successfully connected to Snowflake")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Snowflake: {str(e)}")
            raise
    
    async def disconnect(self) -> None:
        """Close Snowflake connection"""
        if self.connection:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.connection.close)
                logger.info("🔌 Disconnected from Snowflake")
            except Exception as e:
                logger.warning(f"Error closing connection: {str(e)}")
    
    async def execute_query(self, 
                          query: str, 
                          params: Optional[Dict] = None,
                          max_rows: int = 1000) -> Tuple[List[Dict[str, Any]], float]:
        """
        Execute SQL query and return results with timing
        
        Returns:
            Tuple of (results_list, execution_time_ms)
        """
        if not self.connection:
            raise ConnectionError("Database connection not established")
        
        start_time = time.time()
        
        try:
            loop = asyncio.get_event_loop()
            
            # Execute query in thread pool
            def _execute():
                cursor = self.connection.cursor(DictCursor)
                try:
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)
                    
                    # Fetch results with limit
                    results = cursor.fetchmany(max_rows)
                    return [dict(row) for row in results]
                finally:
                    cursor.close()
            
            results = await loop.run_in_executor(None, _execute)
            execution_time = (time.time() - start_time) * 1000
            
            logger.info(f"📊 Query executed: {len(results)} rows in {execution_time:.2f}ms")
            return results, execution_time
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"💥 Query execution failed after {execution_time:.2f}ms: {str(e)}")
            raise
    
    async def test_connection(self) -> bool:
        """Test if database connection is healthy"""
        try:
            await self.execute_query("SELECT 1 as test")
            return True
        except Exception:
            return False
    
    async def get_schema_info(self) -> Dict[str, Any]:
        """Get information about available tables and columns"""
        try:
            # Get table information
            tables_query = """
            SELECT 
                table_name,
                table_type,
                comment
            FROM information_schema.tables 
            WHERE table_schema = UPPER(%s)
            ORDER BY table_name
            """
            
            tables, _ = await self.execute_query(
                tables_query, 
                params=[self.settings.snowflake_schema]
            )
            
            # Get column information for each table
            schema_info = {
                "schema": self.settings.snowflake_schema,
                "tables": {}
            }
            
            for table in tables:
                table_name = table['TABLE_NAME']
                
                columns_query = """
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    comment
                FROM information_schema.columns 
                WHERE table_schema = UPPER(%s) 
                  AND table_name = UPPER(%s)
                ORDER BY ordinal_position
                """
                
                columns, _ = await self.execute_query(
                    columns_query,
                    params=[self.settings.snowflake_schema, table_name]
                )
                
                schema_info["tables"][table_name.lower()] = {
                    "type": table['TABLE_TYPE'],
                    "comment": table.get('COMMENT'),
                    "columns": [
                        {
                            "name": col['COLUMN_NAME'].lower(),
                            "type": col['DATA_TYPE'],
                            "nullable": col['IS_NULLABLE'] == 'YES',
                            "comment": col.get('COMMENT')
                        }
                        for col in columns
                    ]
                }
            
            return schema_info
            
        except Exception as e:
            logger.error(f"Failed to get schema info: {str(e)}")
            return {"error": str(e)}
    
    async def get_table_sample(self, table_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get a sample of data from a table for reference"""
        try:
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            results, _ = await self.execute_query(query)
            return results
        except Exception as e:
            logger.error(f"Failed to get sample from {table_name}: {str(e)}")
            return []
    
    async def validate_table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the current schema"""
        try:
            query = """
            SELECT COUNT(*) as count
            FROM information_schema.tables 
            WHERE table_schema = UPPER(%s) 
              AND table_name = UPPER(%s)
            """
            
            results, _ = await self.execute_query(
                query, 
                params=[self.settings.snowflake_schema, table_name]
            )
            
            return results[0]['COUNT'] > 0 if results else False
            
        except Exception as e:
            logger.error(f"Failed to validate table {table_name}: {str(e)}")
            return False
    
    async def get_row_count(self, table_name: str) -> int:
        """Get the total number of rows in a table"""
        try:
            query = f"SELECT COUNT(*) as row_count FROM {table_name}"
            results, _ = await self.execute_query(query)
            return results[0]['ROW_COUNT'] if results else 0
        except Exception as e:
            logger.error(f"Failed to get row count for {table_name}: {str(e)}")
            return 0
    
    async def get_table_stats(self) -> Dict[str, Any]:
        """Get statistics about all tables in the schema"""
        try:
            schema_info = await self.get_schema_info()
            
            if 'error' in schema_info:
                return schema_info
            
            stats = {
                "schema": schema_info["schema"],
                "total_tables": len(schema_info["tables"]),
                "table_details": {}
            }
            
            # Get row counts for each table
            for table_name in schema_info["tables"].keys():
                try:
                    row_count = await self.get_row_count(table_name)
                    stats["table_details"][table_name] = {
                        "row_count": row_count,
                        "columns": len(schema_info["tables"][table_name]["columns"])
                    }
                except Exception as e:
                    stats["table_details"][table_name] = {
                        "row_count": "error",
                        "error": str(e)
                    }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get table statistics: {str(e)}")
            return {"error": str(e)}
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get information about the current connection"""
        return {
            "database": self.settings.snowflake_database,
            "schema": self.settings.snowflake_schema,
            "warehouse": self.settings.snowflake_warehouse,
            "role": self.settings.snowflake_role,
            "user": self.settings.snowflake_user,
            "account": self.settings.snowflake_account,
            "connected": self.connection is not None
        }