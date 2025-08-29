# 🛠️ Troubleshooting Guide - Agentic Data Explorer

## 🎯 Overview

This guide covers common issues, debugging techniques, and solutions for the Agentic Data Explorer platform.

## 🔍 Quick Diagnostics

### **System Health Check:**
```bash
# Run comprehensive health check
./scripts/health_check.sh

# Check individual services
curl http://localhost:8000/api/v1/health
curl http://localhost:8501
curl http://localhost:11434/api/tags
```

### **Log Analysis:**
```bash
# View real-time logs
tail -f logs/agentic_data_explorer_*.log

# Search for errors
grep -i error logs/agentic_data_explorer_*.log

# Check Docker logs
docker-compose logs --tail=100 agentic-api
docker-compose logs --tail=100 ollama
```

## 🐛 Common Issues & Solutions

### **1. API Service Issues**

#### **❌ "Connection refused" / API not starting**

**Symptoms:**
- `curl http://localhost:8000` fails
- FastAPI not responding
- Health check failures

**Diagnosis:**
```bash
# Check if port is in use
netstat -tulpn | grep :8000

# Check API logs
docker-compose logs agentic-api
```

**Solutions:**
```bash
# Option 1: Restart API service
docker-compose restart agentic-api

# Option 2: Rebuild and restart
docker-compose down
docker-compose up --build agentic-api

# Option 3: Check environment variables
docker-compose exec agentic-api printenv | grep SNOWFLAKE

# Option 4: Free up port
sudo lsof -ti:8000 | xargs kill -9
```

#### **❌ "Database connection failed"**

**Symptoms:**
- API starts but can't connect to Snowflake
- Database health check fails
- Query errors about connection

**Diagnosis:**
```bash
# Test Snowflake connection manually
python -c "
import snowflake.connector
import os
from dotenv import load_dotenv
load_dotenv()

try:
    conn = snowflake.connector.connect(
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        database=os.getenv('SNOWFLAKE_DATABASE'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE')
    )
    print('✅ Snowflake connection successful')
    conn.close()
except Exception as e:
    print(f'❌ Connection failed: {e}')
"
```

**Solutions:**
```bash
# Check credentials in .env file
cat .env | grep SNOWFLAKE

# Verify Snowflake account format
# Should be: account_name.region (e.g., abc123.us-east-1)

# Test with Snowflake CLI
snow connection test --connection-name default

# Check firewall/network access
telnet your_account.snowflakecomputing.com 443
```

### **2. AI/Ollama Issues**

#### **❌ "Ollama service not available"**

**Symptoms:**
- AI agent initialization fails
- "Cannot connect to Ollama" errors
- Query processing fails at AI step

**Diagnosis:**
```bash
# Check Ollama service status
curl http://localhost:11434/api/tags

# Check if Ollama is running
ps aux | grep ollama

# Check Docker container
docker ps | grep ollama
```

**Solutions:**
```bash
# Option 1: Start Ollama service
ollama serve &

# Option 2: Restart Ollama container
docker-compose restart ollama

# Option 3: Rebuild Ollama
docker-compose down ollama
docker-compose up --build ollama

# Option 4: Check Ollama logs
docker-compose logs ollama
```

#### **❌ "Model not found" errors**

**Symptoms:**
- AI queries fail with model errors
- "codellama:7b not found"
- Model loading failures

**Diagnosis:**
```bash
# List available models
ollama list

# Check model in container
docker exec ollama ollama list
```

**Solutions:**
```bash
# Pull required models
ollama pull codellama:7b
ollama pull llama3.1:8b

# Or via Docker
docker exec ollama ollama pull codellama:7b

# Verify model is available
curl http://localhost:11434/api/tags | jq '.models[].name'
```

### **3. Frontend Issues**

#### **❌ Streamlit not loading / blank page**

**Symptoms:**
- Streamlit page doesn't load
- White/blank screen
- Connection errors in browser

**Diagnosis:**
```bash
# Check Streamlit process
ps aux | grep streamlit

# Check port availability
netstat -tulpn | grep :8501

# Check frontend logs
docker-compose logs agentic-frontend
```

**Solutions:**
```bash
# Option 1: Restart Streamlit
streamlit run frontend/streamlit/demo_app.py --server.port 8501

# Option 2: Clear Streamlit cache
rm -rf ~/.streamlit/

# Option 3: Check browser console for errors
# Open browser dev tools (F12) and check console

# Option 4: Restart frontend container
docker-compose restart agentic-frontend
```

#### **❌ "API connection failed" in frontend**

**Symptoms:**
- Frontend loads but can't reach API
- Query button not working
- Network errors in Streamlit

**Diagnosis:**
```bash
# Test API from frontend container
docker exec agentic-frontend curl http://agentic-api:8000/api/v1/health

# Check network connectivity
docker network ls
docker network inspect agentic-data-explorer_default
```

**Solutions:**
```bash
# Update API_BASE_URL in demo_app.py
# For Docker: http://agentic-api:8000/api/v1
# For local: http://localhost:8000/api/v1

# Restart both services
docker-compose restart agentic-api agentic-frontend
```

### **4. Performance Issues**

#### **❌ Slow query responses**

**Symptoms:**
- Queries take > 30 seconds
- Timeouts
- High CPU/memory usage

**Diagnosis:**
```bash
# Monitor system resources
htop
docker stats

# Check query performance logs
grep "execution_time_ms" logs/agentic_data_explorer_*.log | tail -20

# Profile API performance
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/v1/health
```

**Solutions:**
```bash
# Option 1: Use smaller AI model
# Edit .env: LOCAL_AI_MODEL=codellama:7b-q4_0

# Option 2: Increase timeouts
# Edit .env: MAX_QUERY_TIMEOUT=120

# Option 3: Optimize Snowflake warehouse
# Scale up warehouse size in Snowflake console

# Option 4: Add more resources
# Edit docker-compose.yml:
#   deploy:
#     resources:
#       limits:
#         memory: 8G
#         cpus: '4'
```

#### **❌ High memory usage**

**Symptoms:**
- System running out of memory
- Container OOM kills
- Slow performance

**Diagnosis:**
```bash
# Check memory usage
free -h
docker stats --no-stream

# Check largest processes
ps aux --sort=-%mem | head -10

# Monitor memory over time
watch -n 2 'free -h && echo && docker stats --no-stream'
```

**Solutions:**
```bash
# Option 1: Use quantized models
# Edit .env: LOCAL_AI_MODEL=codellama:7b-q4_0

# Option 2: Reduce batch sizes
# Edit AI agent configuration to process smaller batches

# Option 3: Add memory limits
# Edit docker-compose.yml with appropriate memory limits

# Option 4: Increase swap space
sudo dd if=/dev/zero of=/swapfile bs=1G count=4
sudo mkswap /swapfile
sudo swapon /swapfile
```

### **5. Data/Query Issues**

#### **❌ "Table not found" errors**

**Symptoms:**
- SQL generation works but execution fails
- "Table 'fact_sales' doesn't exist"
- Schema-related errors

**Diagnosis:**
```bash
# Check database schema
curl http://localhost:8000/api/v1/schema | jq

# Test dbt models
cd retail_analytics_dbt
dbt test
dbt run
```

**Solutions:**
```bash
# Option 1: Run dbt transformations
cd retail_analytics_dbt
dbt deps
dbt run

# Option 2: Check Snowflake schema
# Login to Snowflake console and verify tables exist

# Option 3: Reload data
python data/data_loader.py

# Option 4: Update schema info
# Restart API to refresh cached schema information
docker-compose restart agentic-api
```

#### **❌ SQL generation produces invalid queries**

**Symptoms:**
- AI generates syntactically incorrect SQL
- "SQL syntax error" responses
- Logic errors in generated queries

**Diagnosis:**
```bash
# Enable SQL debugging
# Edit .env: LOG_LEVEL=DEBUG

# Test AI model directly
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "codellama:7b", "prompt": "Generate SQL: SELECT * FROM fact_sales LIMIT 5"}'
```

**Solutions:**
```bash
# Option 1: Update AI model
ollama pull codellama:13b  # Larger, more accurate model

# Option 2: Improve prompts
# Edit app/services/local_agent.py -> _create_retail_prompt()

# Option 3: Add query validation
# Implement SQL parsing before execution

# Option 4: Provide better examples
# Update the retail prompt with more example queries
```

## 🔧 Advanced Debugging

### **Enable Debug Mode:**
```bash
# Edit .env file
LOG_LEVEL=DEBUG
ENVIRONMENT=development

# Restart services
docker-compose restart
```

### **Database Query Debugging:**
```python
# Add to app/services/database.py
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

### **AI Agent Debugging:**
```python
# Add to app/services/local_agent.py
self.sql_chain = SQLDatabaseChain.from_llm(
    llm=self.llm,
    db=self.langchain_db,
    verbose=True,  # Enable verbose mode
    return_intermediate_steps=True
)
```

### **Network Debugging:**
```bash
# Check Docker networks
docker network ls
docker network inspect agentic-data-explorer_default

# Test connectivity between containers
docker exec agentic-frontend ping agentic-api
docker exec agentic-api ping ollama

# Check port bindings
docker port agentic-api
docker port ollama
```

## 📊 Monitoring & Alerting

### **Setup Monitoring:**
```bash
# Start monitoring stack
docker-compose -f docker-compose.yml -f monitoring/docker-compose.monitoring.yml up -d

# Access Grafana
open http://localhost:3000  # admin/admin123

# Check Prometheus targets
open http://localhost:9090/targets
```

### **Key Metrics to Monitor:**
- **API Response Time**: < 2 seconds average
- **Query Success Rate**: > 95%
- **Memory Usage**: < 80%
- **CPU Usage**: < 70%
- **Database Connection Pool**: Available connections > 50%

### **Alert Thresholds:**
```yaml
# monitoring/prometheus/alert_rules.yml
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
  
- alert: SlowQueries  
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 10
  
- alert: HighMemoryUsage
  expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
```

## 📞 Getting Help

### **Community Support:**
- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: Check docs/ folder for detailed guides
- **Stack Overflow**: Tag questions with `agentic-data-explorer`

### **Self-Help Resources:**
- **Health Check Script**: `./scripts/health_check.sh`
- **Test Suite**: `./scripts/run_tests.sh --all`
- **Log Analysis**: `grep -i error logs/*.log`
- **Performance Testing**: `./scripts/run_tests.sh --performance`

## 🔄 Recovery Procedures

### **Complete System Reset:**
```bash
# Stop all services
docker-compose down -v

# Clean up containers and images
docker system prune -a

# Rebuild from scratch
git pull origin main
docker-compose build --no-cache
docker-compose up -d

# Verify deployment
./scripts/health_check.sh
```

### **Data Recovery:**
```bash
# Restore from backup
tar -xzf backup-config-*.tar.gz
tar -xzf backup-logs-*.tar.gz

# Reload data
python data/data_generator.py
python data/data_loader.py
cd retail_analytics_dbt && dbt run
```

### **Configuration Reset:**
```bash
# Reset to defaults
cp .env.example .env
# Edit with your credentials

# Reset Docker configuration
docker-compose down
docker-compose up --force-recreate
```