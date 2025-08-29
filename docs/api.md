# 📚 Agentic Data Explorer - API Documentation

## 🎯 Overview

The Agentic Data Explorer API provides a RESTful interface for natural language querying of retail analytics data. The API converts natural language questions into SQL queries, executes them against a Snowflake data warehouse, and returns structured results with metadata.

## 🔗 Base URL

```
Development: http://localhost:8000
Production: https://your-domain.com
```

## 🔐 Authentication

Currently, the API does not require authentication for development environments. For production deployments, consider implementing:

- API Key authentication
- JWT tokens
- OAuth 2.0

## 📋 API Endpoints

### **Query Processing**

#### `POST /api/v1/query`

Process a natural language query and return results.

**Request Body:**
```json
{
  "question": "What was the total revenue last month?",
  "max_rows": 100,
  "include_sql": true,
  "timeout_seconds": 30
}
```

**Response:**
```json
{
  "question": "What was the total revenue last month?",
  "sql_query": "SELECT SUM(total_amount) FROM fact_sales WHERE...",
  "results": [
    {"Total Revenue": 45000.50}
  ],
  "row_count": 1,
  "execution_time_ms": 1250.5,
  "complexity": "SIMPLE",
  "timestamp": "2024-02-01T10:30:00Z",
  "metadata": {
    "ai_model": "codellama:7b",
    "sql_generation_time_ms": 800.0,
    "database_query_time_ms": 450.5
  }
}
```

**Error Response:**
```json
{
  "error": "Column 'invalid_column' not found",
  "error_type": "DatabaseError",
  "suggestions": [
    "Check column names in your question",
    "Try rephrasing with different terms"
  ]
}
```

#### `GET /api/v1/query/examples`

Get curated example queries organized by category.

**Response:**
```json
{
  "categories": {
    "Revenue & Sales": [
      "What was the total revenue last month?",
      "Show me monthly revenue for the past 6 months"
    ],
    "Product Analysis": [
      "Which product category has the highest sales?",
      "Show me the top 10 best-selling products"
    ]
  },
  "tips": [
    "Use specific time periods like 'last month'",
    "Ask for 'top N' results to get manageable data sets"
  ],
  "timestamp": "2024-02-01T10:30:00Z"
}
```

#### `GET /api/v1/query/stats`

Get query processing statistics and performance metrics.

**Response:**
```json
{
  "statistics": {
    "total_queries": 150,
    "successful_queries": 142,
    "failed_queries": 8,
    "avg_response_time": 1200.5,
    "success_rate": 94.7,
    "error_rate": 5.3,
    "model_used": "ollama:codellama:7b"
  },
  "timestamp": "2024-02-01T10:30:00Z",
  "status": "active"
}
```

### **System Health**

#### `GET /api/v1/health`

Basic health check for system status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-02-01T10:30:00Z",
  "version": "1.0.0",
  "services": {
    "database": "✅ healthy",
    "ai_agent": "✅ healthy",
    "ollama": "✅ healthy",
    "api_server": "✅ healthy"
  },
  "uptime_seconds": 3600.5
}
```

## 🔍 Example Natural Language Queries

### **Revenue Analysis:**
- "What was the total revenue last month?"
- "Show me monthly revenue for the past 6 months"
- "Which store has the highest revenue?"

### **Product Analysis:**
- "What are the top 5 best-selling products?"
- "Which product category has the highest sales?"
- "Show me average order value by category"

### **Time Analysis:**
- "How do weekend sales compare to weekdays?"
- "What's our busiest day of the week?"
- "Show me sales trends over the past quarter"

## 🚀 SDK Examples

### **Python:**
```python
import requests

# Basic query
response = requests.post(
    "http://localhost:8000/api/v1/query",
    json={
        "question": "What was the total revenue last month?",
        "max_rows": 100,
        "include_sql": True
    }
)

data = response.json()
print(f"Results: {data['results']}")
print(f"Generated SQL: {data['sql_query']}")
```

### **JavaScript:**
```javascript
// Basic query
const response = await fetch('http://localhost:8000/api/v1/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    question: 'What was the total revenue last month?',
    max_rows: 100,
    include_sql: true
  })
});

const data = await response.json();
console.log('Results:', data.results);
console.log('Generated SQL:', data.sql_query);
```

### **cURL:**
```bash
# Basic query
curl -X POST "http://localhost:8000/api/v1/query" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "What was the total revenue last month?",
       "max_rows": 100,
       "include_sql": true
     }'

# Health check
curl "http://localhost:8000/api/v1/health"
```

## 📝 OpenAPI Documentation

Interactive API documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`