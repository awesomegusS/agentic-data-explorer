# 🚀 Deployment Guide - Agentic Data Explorer

## 🎯 Overview

This guide covers deployment options for the Agentic Data Explorer, from local development to production environments.

## 📋 Prerequisites

### **System Requirements:**
- **CPU**: 4+ cores recommended (8+ for production)
- **RAM**: 8GB minimum, 16GB+ recommended
- **Storage**: 20GB+ free space
- **OS**: Linux, macOS, or Windows with WSL2

### **Software Dependencies:**
- **Docker & Docker Compose** (for containerized deployment)
- **Conda/Miniconda** (for local development)
- **Ollama** (for AI model hosting)
- **Git** (for source code management)

## 🐳 Docker Deployment (Recommended)

### **Quick Start:**
```bash
# Clone repository
git clone 
cd agentic-data-explorer

# Configure environment
cp .env.example .env
# Edit .env with your Snowflake credentials

# Start all services
docker-compose up -d

# Verify deployment
curl http://localhost:8000/api/v1/health
```

### **Production Docker Setup:**
```bash
# Production deployment with monitoring
docker-compose -f docker-compose.yml -f monitoring/docker-compose.monitoring.yml up -d

# Access services
# API: http://localhost:8000
# Frontend: http://localhost:8501  
# Grafana: http://localhost:3000 (admin/admin123)
# Prometheus: http://localhost:9090
```

### **Docker Services:**
- **agentic-api**: FastAPI backend application
- **agentic-frontend**: Streamlit dashboard
- **ollama**: Local AI model service
- **prometheus**: Metrics collection
- **grafana**: Monitoring dashboards
- **node-exporter**: System metrics
- **cadvisor**: Container metrics

## 🏠 Local Development Deployment

### **Setup with Conda:**
```bash
# Clone and setup
git clone 
cd agentic-data-explorer

# Run comprehensive setup
chmod +x scripts/setup_project.sh
./scripts/setup_project.sh

# Activate environment
conda activate agentic_data_explorer

# Configure credentials
cp .env.example .env
# Edit .env with your settings

# Start Ollama
ollama serve &

# Start backend (Terminal 1)
uvicorn app.main:app --reload --port 8000

# Start frontend (Terminal 2)
streamlit run frontend/streamlit/demo_app.py --port 8501
```

## ☸️ Kubernetes Deployment

### **Prerequisites:**
- Kubernetes cluster (1.20+)
- kubectl configured
- Helm 3.x (optional)

### **Basic Kubernetes Deployment:**

Create `k8s/namespace.yaml`:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: agentic-data-explorer
```

Create `k8s/deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agentic-api
  namespace: agentic-data-explorer
spec:
  replicas: 3
  selector:
    matchLabels:
      app: agentic-api
  template:
    metadata:
      labels:
        app: agentic-api
    spec:
      containers:
      - name: api
        image: agentic-data-explorer:latest
        ports:
        - containerPort: 8000
        env:
        - name: API_PORT
          value: "8000"
        envFrom:
        - secretRef:
            name: agentic-secrets
        resources:
          requests:
            memory: "2Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /api/v1/live
            port: 8000
          initialDelaySeconds: 30
        readinessProbe:
          httpGet:
            path: /api/v1/ready
            port: 8000
          initialDelaySeconds: 5
```

### **Deploy to Kubernetes:**
```bash
# Apply manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n agentic-data-explorer
kubectl rollout status deployment/agentic-api -n agentic-data-explorer

# Scale deployment
kubectl scale deployment agentic-api --replicas=5 -n agentic-data-explorer
```

## 🔧 Environment Configuration

### **Environment Variables:**

**Required:**
```bash
# Snowflake Configuration
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_DATABASE=retail_analytics
SNOWFLAKE_SCHEMA=analytics

# Local AI Configuration
LOCAL_AI_MODEL=codellama:7b
LOCAL_AI_HOST=localhost
LOCAL_AI_PORT=11434
```

**Optional:**
```bash
# Application Settings
ENVIRONMENT=production
API_PORT=8000
LOG_LEVEL=INFO

# Performance Tuning
MAX_QUERY_TIMEOUT=60
DEFAULT_MAX_ROWS=100
DB_POOL_SIZE=10

# Monitoring
ENABLE_METRICS=true
GRAFANA_ADMIN_PASSWORD=secure_password

# Security
ALLOWED_ORIGINS=https://yourdomain.com
ENABLE_RATE_LIMITING=true
```

## 🔐 Security Configuration

### **Production Security Checklist:**

**✅ HTTPS/TLS:**
```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;
    
    location / {
        proxy_pass http://agentic-api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**✅ Rate Limiting:**
```python
# Add to app/main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/v1/query")
@limiter.limit("10/minute")
async def query_endpoint(request: Request, ...):
    # Endpoint logic
```

## 📊 Load Balancing & Scaling

### **Horizontal Pod Autoscaling (Kubernetes):**
```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: agentic-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agentic-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## 🔄 CI/CD Pipeline

### **GitHub Actions Example:**
```yaml
# .github/workflows/deploy.yml
name: Deploy Agentic Data Explorer

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest
      
      - name: Run tests
        run: pytest tests/ -v

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker image
        run: |
          docker build -t agentic-data-explorer:${{ github.sha }} .
          docker tag agentic-data-explorer:${{ github.sha }} agentic-data-explorer:latest
      
      - name: Deploy to production
        run: |
          ./scripts/deploy.sh --env production --type docker
```

## 🐛 Troubleshooting

### **Common Issues:**

**🔍 API Not Starting:**
```bash
# Check logs
docker-compose logs agentic-api

# Solutions:
docker-compose down
docker-compose up --build
```

**🔍 Ollama Connection Issues:**
```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Restart Ollama
docker-compose restart ollama
```

**🔍 Database Connection Failed:**
```bash
# Test connection manually
python -c "
import snowflake.connector
conn = snowflake.connector.connect(
    user='$SNOWFLAKE_USER',
    password='$SNOWFLAKE_PASSWORD',
    account='$SNOWFLAKE_ACCOUNT'
)
print('✅ Connection successful')
"
```

## 📈 Performance Optimization

### **Production Optimizations:**

**✅ Resource Limits:**
```yaml
# docker-compose.yml
services:
  agentic-api:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2'
        reservations:
          memory: 2G
          cpus: '1'
```

**✅ Database Connection Pooling:**
```python
# app/services/database.py
DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '10'))
DB_MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '20'))
```

## 🔄 Backup & Recovery

### **Data Backup Strategy:**
```bash
#!/bin/bash
# scripts/backup.sh

# Backup configuration
tar -czf "backup-config-$(date +%Y%m%d).tar.gz" .env docker-compose.yml

# Backup logs
tar -czf "backup-logs-$(date +%Y%m%d).tar.gz" logs/

# Backup Grafana dashboards
docker exec grafana grafana-cli admin export-dashboard > "backup-dashboards-$(date +%Y%m%d).json"
```