# app/services/local_agent.py
"""
Local AI SQL Agent service using Ollama for natural language to SQL conversion.
This is the brain of the system - converts questions to SQL queries.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import re
import time
import asyncio
from datetime import datetime

from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from sqlalchemy import create_engine

from app.utils.config import get_settings
from app.models.schemas import QueryComplexity
from app.services.database import DatabaseService

logger = logging.getLogger(__name__)

class LocalSQLAgentService:
    """Local AI-powered SQL agent using Ollama"""
    
    def __init__(self, database_service: DatabaseService):
        self.settings = get_settings()
        self.database_service = database_service
        self.llm = None
        self.sql_agent = None
        self.sqlalchemy_engine = None
        self.langchain_db = None
        self.schema_info = None
        
        # Query statistics
        self.stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'avg_response_time': 0.0,
            'model_used': f"{self.settings.local_ai_backend}:{self.settings.local_ai_model}"
        }
    
    async def initialize(self):
        """Initialize the local AI SQL agent"""
        try:
            logger.info("🤖 Initializing Local AI SQL Agent...")
            
            # Test Ollama connection
            if not await self._test_ollama_connection():
                raise Exception("Ollama service not available")
            
            # Initialize Ollama LLM with optimized settings
            self.llm = Ollama(
                model=self.settings.local_ai_model,
                base_url=f"http://{self.settings.local_ai_host}:{self.settings.local_ai_port}",
                temperature=self.settings.local_ai_temperature,
                num_predict=100,  # Further reduced for faster responses
                timeout=60  # 60 second timeout for individual requests
            )
            
            # Test LLM
            test_response = await self._test_llm()
            logger.info(f"🧠 LLM test response: {test_response[:100]}...")
            
            # Create SQLAlchemy engine for LangChain
            connection_string = self._build_connection_string()
            self.sqlalchemy_engine = create_engine(connection_string)
            self.langchain_db = SQLDatabase(self.sqlalchemy_engine)
            
            # Get schema information for better SQL generation
            self.schema_info = await self.database_service.get_schema_info()
            logger.info(f"📋 Loaded schema info for {len(self.schema_info.get('tables', {}))} tables")
            
            # Create SQL agent with optimized settings
            self.sql_agent = create_sql_agent(
                llm=self.llm,
                db=self.langchain_db,
                verbose=False,  # Disable verbose logging for speed
                agent_type="zero-shot-react-description"
            )
            
            logger.info("✅ Local AI SQL Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Local AI SQL Agent: {str(e)}")
            raise
    
    async def _test_ollama_connection(self) -> bool:
        """Test if Ollama service is available"""
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://{self.settings.local_ai_host}:{self.settings.local_ai_port}/api/tags",
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    models = response.json().get('models', [])
                    model_names = [model.get('name', '') for model in models]
                    
                    if self.settings.local_ai_model in model_names:
                        logger.info(f"✅ Found model {self.settings.local_ai_model} in Ollama")
                        return True
                    else:
                        logger.error(f"❌ Model {self.settings.local_ai_model} not found. Available: {model_names}")
                        return False
                else:
                    logger.error(f"❌ Ollama API returned {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Cannot connect to Ollama: {str(e)}")
            return False
    
    async def _test_llm(self) -> str:
        """Test LLM with a simple query"""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.llm("What is SQL? Answer in one sentence.")
            )
            return response
        except Exception as e:
            logger.error(f"LLM test failed: {str(e)}")
            raise
    
    def _build_connection_string(self) -> str:
        """Build Snowflake connection string for SQLAlchemy"""
        return (
            f"snowflake://{self.settings.snowflake_user}:"
            f"{self.settings.snowflake_password}@"
            f"{self.settings.snowflake_account}/"
            f"{self.settings.snowflake_database}/"
            f"{self.settings.snowflake_schema}"
        )
    
    def _create_retail_prompt(self) -> PromptTemplate:
        """Create optimized prompt for retail analytics"""
        
        # Build dynamic schema information
        schema_description = self._build_schema_description()
        
        template = f"""You are an expert SQL analyst for a retail analytics platform. Generate precise SQL queries for the given questions.

{schema_description}

QUERY RULES:
1. Always use proper JOINs between fact and dimension tables
2. Use meaningful column aliases for readability
3. Include proper WHERE clauses for date filtering
4. Use appropriate aggregation functions (SUM, COUNT, AVG)
5. Limit results to 10-20 rows unless specifically asked for more
6. For time periods like "last month", use relative date functions
7. Always include GROUP BY for aggregated columns
8. Use UPPER() function for string comparisons to handle case sensitivity

COMMON PATTERNS:
- Revenue/Sales: SUM(total_amount) 
- Transaction Count: COUNT(*)
- Average Order Value: AVG(total_amount)
- Last Month: WHERE sale_date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') AND sale_date < DATE_TRUNC('month', CURRENT_DATE)
- This Year: WHERE EXTRACT(year FROM sale_date) = EXTRACT(year FROM CURRENT_DATE)
- Top N: ORDER BY [metric] DESC LIMIT N

EXAMPLE QUERIES:

Q: "What was total revenue last month?"
A: SELECT SUM(total_amount) as total_revenue
   FROM fact_sales
   WHERE sale_date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
     AND sale_date < DATE_TRUNC('month', CURRENT_DATE);

Q: "Top 5 stores by revenue"
A: SELECT s.store_name, s.store_region, SUM(f.total_amount) as total_revenue
   FROM fact_sales f
   JOIN dim_store s ON f.store_id = s.store_id
   GROUP BY s.store_name, s.store_region
   ORDER BY total_revenue DESC
   LIMIT 5;

Q: "Sales by product category"
A: SELECT p.product_category, 
          COUNT(*) as transaction_count,
          SUM(f.total_amount) as total_revenue,
          AVG(f.total_amount) as avg_order_value
   FROM fact_sales f
   JOIN dim_product p ON f.product_id = p.product_id
   GROUP BY p.product_category
   ORDER BY total_revenue DESC;

Q: "How do weekend sales compare to weekday sales?"
A: SELECT 
          CASE WHEN d.day_type = 'Weekend' THEN 'Weekend' ELSE 'Weekday' END as period_type,
          COUNT(*) as transaction_count,
          SUM(f.total_amount) as total_revenue,
          AVG(f.total_amount) as avg_transaction_value
   FROM fact_sales f
   JOIN dim_date d ON f.sale_date = d.date_day
   GROUP BY CASE WHEN d.day_type = 'Weekend' THEN 'Weekend' ELSE 'Weekday' END
   ORDER BY total_revenue DESC;

Generate a single, clean SQL query for this question: {{input}}

SQL Query:"""
        
        return PromptTemplate(
            input_variables=["input"],
            template=template
        )
    
    def _build_schema_description(self) -> str:
        """Build schema description for the prompt"""
        if not self.schema_info or 'tables' not in self.schema_info:
            return "DATABASE SCHEMA: Information not available"
        
        schema_desc = "DATABASE SCHEMA:\n"
        
        for table_name, table_info in self.schema_info['tables'].items():
            schema_desc += f"\n{table_name.upper()} ({table_info.get('type', 'TABLE')}):\n"
            
            key_columns = []
            for col in table_info.get('columns', []):
                col_name = col['name']
                col_type = col['type']
                key_columns.append(f"  - {col_name} ({col_type})")
            
            schema_desc += "\n".join(key_columns[:10])  # Limit to first 10 columns
            if len(table_info.get('columns', [])) > 10:
                schema_desc += f"\n  - ... and {len(table_info['columns']) - 10} more columns"
            schema_desc += "\n"
        
        return schema_desc
    
    def _try_quick_response(self, question: str) -> Optional[str]:
        """Provide quick responses for general questions that don't require database queries"""
        question_lower = question.lower().strip()
        
        # SQL-related questions
        if any(phrase in question_lower for phrase in ["what is sql", "what's sql", "define sql"]):
            return "SQL (Structured Query Language) is a programming language designed for managing and querying relational databases. It allows you to retrieve, insert, update, and delete data from database tables."
        
        if any(phrase in question_lower for phrase in ["how does sql work", "how sql works"]):
            return "SQL works by allowing you to write declarative statements that describe what data you want, rather than how to get it. The database engine interprets these statements and executes them against the database tables."
        
        if any(phrase in question_lower for phrase in ["what is database", "what's database", "define database"]):
            return "A database is an organized collection of structured information stored electronically in a computer system. It's managed by a Database Management System (DBMS) that allows you to store, retrieve, and manipulate data efficiently."
        
        # Application-specific questions
        if any(phrase in question_lower for phrase in ["what can i ask", "what questions", "what can you do", "help me"]):
            return """You can ask me questions about your retail data, such as:
            - Sales analysis: "What was the total revenue last month?"
            - Product insights: "Which product category has the highest sales?"
            - Store performance: "Show me the top 5 stores by revenue"
            - Time-based queries: "How do weekend sales compare to weekday sales?"
            
            I'll convert your natural language questions into SQL queries and return the results."""
        
        return None
    
    def _try_template_generation(self, question: str) -> Optional[str]:
        """Try to generate SQL using predefined templates for common queries"""
        question_lower = question.lower()
        
        # Simple count queries
        if any(phrase in question_lower for phrase in ["how many", "count", "total number", "number of"]):
            if any(word in question_lower for word in ["sales", "transaction", "record"]):
                return "SELECT COUNT(*) as total_count FROM sales;"
            elif "product" in question_lower:
                return "SELECT COUNT(*) as product_count FROM products;"
            elif "store" in question_lower:
                return "SELECT COUNT(*) as store_count FROM stores;"
        
        # Revenue/sales queries
        if any(phrase in question_lower for phrase in ["total revenue", "total sales", "sum of sales"]):
            if "month" in question_lower:
                return """
                SELECT SUM(total_amount) as total_revenue 
                FROM sales 
                WHERE sale_date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
                  AND sale_date < DATE_TRUNC('month', CURRENT_DATE);
                """
            else:
                return "SELECT SUM(total_amount) as total_revenue FROM sales;"
        
        # Top/best performing queries
        if any(phrase in question_lower for phrase in ["top", "best", "highest"]) and "store" in question_lower:
            return """
            SELECT s.store_name, s.store_region, SUM(sa.total_amount) as total_revenue
            FROM sales sa
            JOIN stores s ON sa.store_id = s.store_id
            GROUP BY s.store_name, s.store_region
            ORDER BY total_revenue DESC
            LIMIT 5;
            """
        
        if any(phrase in question_lower for phrase in ["top", "best", "highest"]) and "product" in question_lower:
            return """
            SELECT p.product_name, p.product_category, SUM(s.total_amount) as total_sales
            FROM sales s
            JOIN products p ON s.product_id = p.product_id
            GROUP BY p.product_name, p.product_category
            ORDER BY total_sales DESC
            LIMIT 10;
            """
        
        # Simple select all queries
        if question_lower in ["show sales", "show all sales", "list sales"]:
            return "SELECT * FROM sales LIMIT 20;"
        elif question_lower in ["show products", "show all products", "list products"]:
            return "SELECT * FROM products LIMIT 20;"
        elif question_lower in ["show stores", "show all stores", "list stores"]:
            return "SELECT * FROM stores LIMIT 20;"
        
        # Average queries
        if "average" in question_lower and any(word in question_lower for word in ["sales", "revenue", "amount"]):
            return "SELECT AVG(total_amount) as average_sale FROM sales;"
        
        return None
    
    async def process_query(self, 
                          question: str, 
                          max_rows: int = 100,
                          include_sql: bool = False,
                          timeout_seconds: int = 20) -> Dict[str, Any]:  # Reduced default timeout
        """Process natural language query and return results"""
        
        start_time = time.time()
        self.stats['total_queries'] += 1
        
        try:
            logger.info(f"🤔 Processing query: {question}")
            
            # Preprocess question for better AI understanding
            processed_question = self._preprocess_question(question)
            
            # Check for quick non-SQL responses first
            quick_response = self._try_quick_response(processed_question)
            if quick_response:
                logger.info("⚡ Using quick response for general question")
                return {
                    'question': question,
                    'sql_query': None,
                    'results': [{'answer': quick_response}],
                    'row_count': 1,
                    'execution_time_ms': time.time() * 1000 - start_time * 1000,
                    'complexity': 'simple',
                    'timestamp': datetime.now().isoformat(),
                    'metadata': {'response_type': 'quick_answer'}
                }
            
            # Estimate query complexity
            complexity = self._estimate_complexity(processed_question)
            
            # Try fast template-based generation first
            template_sql = self._try_template_generation(processed_question)
            if template_sql:
                logger.info("🚀 Using template-based SQL generation")
                sql_result = {"result": template_sql}
            else:
                # Fallback to AI generation with shorter timeout
                logger.info("🤖 Using AI-based SQL generation")
                sql_result = await asyncio.wait_for(
                    self._execute_ai_chain(processed_question),
                    timeout=min(timeout_seconds, 60)  # Max 60 seconds for AI
                )
            
            # Extract SQL from AI response
            generated_sql = self._extract_sql_from_result(sql_result)
            
            if not generated_sql:
                raise Exception("AI failed to generate valid SQL")
            
            # Clean and validate SQL
            cleaned_sql = self._clean_sql(generated_sql)
            
            # Execute SQL against database
            db_results, query_time = await self.database_service.execute_query(
                cleaned_sql, max_rows=max_rows
            )
            
            # Post-process results for better presentation
            processed_results = self._postprocess_results(db_results, max_rows)
            
            # Calculate total execution time
            execution_time = (time.time() - start_time) * 1000
            
            # Update statistics
            self.stats['successful_queries'] += 1
            self._update_avg_response_time(execution_time)
            
            # Build response
            response = {
                'question': question,
                'results': processed_results,
                'row_count': len(processed_results),
                'execution_time_ms': execution_time,
                'complexity': complexity,
                'timestamp': datetime.now(),
                'metadata': {
                    'ai_model': self.settings.local_ai_model,
                    'sql_generation_time_ms': execution_time - query_time,
                    'database_query_time_ms': query_time,
                    'processed_question': processed_question,
                    'stats': self.stats.copy()
                }
            }
            
            if include_sql:
                response['sql_query'] = cleaned_sql
            
            logger.info(f"✅ Query processed successfully: {len(processed_results)} rows in {execution_time:.2f}ms")
            return response
            
        except asyncio.TimeoutError:
            execution_time = (time.time() - start_time) * 1000
            self.stats['failed_queries'] += 1
            
            logger.error(f"⏰ Query timed out after {execution_time:.2f}ms")
            
            return {
                'question': question,
                'results': [],
                'row_count': 0,
                'execution_time_ms': execution_time,
                'complexity': QueryComplexity.SIMPLE,
                'timestamp': datetime.now(),
                'error': 'Query timed out',
                'error_type': 'TimeoutError',
                'suggestions': [
                    'Try asking a simpler question',
                    'Be more specific about the time period',
                    'Ask for fewer results'
                ]
            }
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.stats['failed_queries'] += 1
            
            logger.error(f"💥 Query processing failed after {execution_time:.2f}ms: {str(e)}")
            
            return {
                'question': question,
                'results': [],
                'row_count': 0,
                'execution_time_ms': execution_time,
                'complexity': QueryComplexity.SIMPLE,
                'timestamp': datetime.now(),
                'error': str(e),
                'error_type': type(e).__name__,
                'suggestions': self._generate_error_suggestions(question, str(e))
            }
    
    async def _execute_ai_chain(self, question: str) -> Dict[str, Any]:
        """Execute the LangChain SQL agent"""
        try:
            loop = asyncio.get_event_loop()
            
            # Use the agent's run method instead of chain call
            result = await loop.run_in_executor(
                None,
                lambda: self.sql_agent.run(question)
            )
            
            # Wrap string result in a dict for compatibility
            if isinstance(result, str):
                return {"result": result, "intermediate_steps": []}
            
            return result
            
        except Exception as e:
            logger.error(f"AI agent execution failed: {str(e)}")
            raise
    
    def _preprocess_question(self, question: str) -> str:
        """Preprocess question for better AI understanding"""
        
        # Convert common phrases to more SQL-friendly terms
        replacements = {
            'last month': 'previous month',
            'this month': 'current month',
            'last year': 'previous year',
            'this year': 'current year',
            'best selling': 'highest sales',
            'worst performing': 'lowest sales',
            'top performing': 'highest revenue',
            'revenue': 'total sales amount',
            'sales': 'total amount'
        }
        
        processed = question.lower()
        for old, new in replacements.items():
            processed = processed.replace(old, new)
        
        # Add context for better understanding
        if 'compare' in processed or 'vs' in processed:
            processed = f"Show comparison data: {processed}"
        elif 'trend' in processed or 'over time' in processed:
            processed = f"Show time series data: {processed}"
        
        return processed
    
    def _estimate_complexity(self, question: str) -> QueryComplexity:
        """Estimate query complexity based on question content"""
        
        question_lower = question.lower()
        
        # Complex indicators
        complex_indicators = [
            'trend', 'growth', 'change over time', 'compare', 'vs', 'versus',
            'correlation', 'analysis', 'breakdown by', 'segment by',
            'month over month', 'year over year', 'moving average', 'forecast'
        ]
        
        # Moderate indicators
        moderate_indicators = [
            'top', 'bottom', 'best', 'worst', 'highest', 'lowest',
            'by category', 'by region', 'by store', 'group by',
            'average', 'total', 'sum', 'count', 'join', 'where'
        ]
        
        if any(indicator in question_lower for indicator in complex_indicators):
            return QueryComplexity.COMPLEX
        elif any(indicator in question_lower for indicator in moderate_indicators):
            return QueryComplexity.MODERATE
        else:
            return QueryComplexity.SIMPLE
    
    def _extract_sql_from_result(self, result: Dict[str, Any]) -> Optional[str]:
        """Extract SQL from LangChain agent result"""
        try:
            # For agent results, the answer is in the 'result' key
            if 'result' in result:
                result_text = str(result['result'])
                sql = self._extract_sql_from_text(result_text)
                if sql:
                    return sql
                
                # If no SQL found in text but result looks like SQL
                if 'SELECT' in result_text.upper():
                    return result_text.strip()
            
            # Last resort: try the entire result as SQL if it's a string
            if isinstance(result, str) and 'SELECT' in result.upper():
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting SQL: {str(e)}")
            return None
    
    def _extract_sql_from_text(self, text: str) -> Optional[str]:
        """Extract SQL from model response text using regex patterns"""
        
        # Multiple patterns to catch different formats
        sql_patterns = [
            r'```sql\s*(.*?)\s*```',           # SQL code blocks
            r'```\s*(SELECT.*?);?\s*```',      # Generic code blocks with SELECT
            r'(SELECT\s+.*?(?:;|\n\n|\Z))',    # SELECT statements
            r'SQL Query:\s*(SELECT.*?)(?:\n|$)',     # SQL: prefix
            r'Query:\s*(SELECT.*?)(?:\n|$)',   # Query: prefix
        ]
        
        for pattern in sql_patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                sql = match.group(1).strip()
                if sql and 'SELECT' in sql.upper():
                    return sql
        
        return None
    
    def _clean_sql(self, sql: str) -> str:
        """Clean and validate SQL"""
        if not sql:
            return sql
        
        # Remove comments and extra whitespace
        sql = re.sub(r'--.*\n', '', sql)
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
        sql = ' '.join(sql.split())
        
        # Ensure it ends with semicolon
        if not sql.endswith(';'):
            sql += ';'
        
        # Basic validation
        if not sql.upper().strip().startswith('SELECT'):
            raise ValueError("Generated query is not a SELECT statement")
        
        # Remove dangerous keywords (safety check)
        dangerous_patterns = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE TABLE', 'INSERT', 'UPDATE']
        sql_upper = sql.upper()
        for pattern in dangerous_patterns:
            if pattern in sql_upper:
                raise ValueError(f"Dangerous SQL keyword detected: {pattern}")
        
        return sql
    
    def _postprocess_results(self, results: List[Dict[str, Any]], max_rows: int) -> List[Dict[str, Any]]:
        """Post-process query results for better presentation"""
        
        if not results:
            return []
        
        # Limit rows
        limited_results = results[:max_rows]
        
        # Clean up result formatting
        cleaned_results = []
        for row in limited_results:
            cleaned_row = {}
            for key, value in row.items():
                # Convert key to more readable format
                clean_key = key.replace('_', ' ').title()
                
                # Format values
                if isinstance(value, float):
                    # Round to 2 decimal places for currency/percentages
                    cleaned_row[clean_key] = round(value, 2)
                elif isinstance(value, datetime):
                    cleaned_row[clean_key] = value.isoformat()
                elif value is None:
                    cleaned_row[clean_key] = "N/A"
                else:
                    cleaned_row[clean_key] = value
            
            cleaned_results.append(cleaned_row)
        
        return cleaned_results
    
    def _generate_error_suggestions(self, question: str, error: str) -> List[str]:
        """Generate helpful suggestions when queries fail"""
        
        suggestions = []
        error_lower = error.lower()
        question_lower = question.lower()
        
        if 'column' in error_lower and ('not found' in error_lower or 'invalid' in error_lower):
            suggestions.extend([
                "Try rephrasing your question using different terms",
                "Common columns: total_amount, quantity, store_region, product_category",
                "Ask 'What columns are available?' to see all options"
            ])
        
        if 'table' in error_lower and 'not found' in error_lower:
            suggestions.extend([
                "The query might reference unavailable tables",
                "Available data: sales, stores, products, dates"
            ])
        
        if 'timeout' in error_lower or 'time' in error_lower:
            suggestions.extend([
                "Try asking for a smaller date range",
                "Consider asking for fewer results (top 10 instead of all)",
                "Make your question more specific"
            ])
        
        if 'syntax' in error_lower or 'parse' in error_lower:
            suggestions.extend([
                "Try rephrasing your question more clearly",
                "Use simpler language",
                "Example: 'What was the total revenue last month?'"
            ])
        
        if not suggestions:
            suggestions.extend([
                "Try rephrasing your question more specifically",
                "Use terms like: revenue, sales, stores, products, categories",
                "Example: 'Show me the top 5 stores by revenue'"
            ])
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    def _update_avg_response_time(self, execution_time: float) -> None:
        """Update average response time statistics"""
        if self.stats['successful_queries'] == 1:
            self.stats['avg_response_time'] = execution_time
        else:
            current_avg = self.stats['avg_response_time']
            n = self.stats['successful_queries']
            self.stats['avg_response_time'] = ((current_avg * (n - 1)) + execution_time) / n
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get agent performance statistics"""
        stats = self.stats.copy()
        
        # Calculate additional metrics
        total_queries = stats['total_queries']
        if total_queries > 0:
            stats['success_rate'] = (stats['successful_queries'] / total_queries) * 100
            stats['error_rate'] = (stats['failed_queries'] / total_queries) * 100
        else:
            stats['success_rate'] = 0
            stats['error_rate'] = 0
        
        return stats
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.sqlalchemy_engine:
            self.sqlalchemy_engine.dispose()
            logger.info("🧹 Local SQL Agent cleaned up successfully")