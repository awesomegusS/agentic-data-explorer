# 🔍 Agentic Data Explorer

> **AI-Powered Natural Language to SQL Interface**
> 
> Transform your business questions into instant data insights using local AI models and natural language processing.

![Architecture](https://img.shields.io/badge/Architecture-FastAPI%20%2B%20Streamlit-green)
![AI](https://img.shields.io/badge/AI-Local%20Ollama-blue)
![Database](https://img.shields.io/badge/Database-Snowflake-lightblue)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🚀 Quick Start (Docker)

### Prerequisites
- Docker & Docker Compose
- 8GB+ RAM (for AI models)
- Snowflake database credentials

### 1. Clone & Setup
```bash
git clone <your-repo-url>
cd agentic-data-explorer
cp .env.example .env
# Edit .env with your Snowflake credentials
```

### 2. Launch with Docker
```bash
# Full stack with monitoring
docker-compose up -d

# Or minimal setup (API + Frontend only)
docker-compose -f docker-compose.dev.yml up -d
```

### 3. Access the Application
- **Frontend**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health
- **Monitoring** (optional): http://localhost:3000 (Grafana)

## 💡 What Can You Ask?

```
"What was the total revenue last month?"
"Which product category has the highest sales?"
"Show me the top 5 stores by revenue"
"How do weekend sales compare to weekday sales?"
"What is SQL?"  # Fast responses for common questions
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │────│   FastAPI       │────│   Snowflake     │
│   Frontend      │    │   Backend       │    │   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         │              ┌─────────────────┐
         └──────────────│   Ollama AI     │
                        │   (Local LLM)   │
                        └─────────────────┘
```

## 🐳 Deployment Options

### Option 1: Full Production Stack
```bash
# Includes API, Frontend, AI, Monitoring
docker-compose up -d
```

### Option 2: Development Mode
```bash
# Hot reload enabled
docker-compose -f docker-compose.dev.yml up -d
```

### Option 3: Minimal Setup
```bash
# Just API and Frontend
docker-compose up -d api frontend
```

### Option 4: Local Development
```bash
# Install conda environment
conda env create -f environment.yml
conda activate agentic_data_explorer

# Start services
ollama serve &  # In another terminal
uvicorn app.main:app --reload
streamlit run frontend/streamlit/demo_app.py
```

## ⚡ Performance & Timeout Issues

### Quick Fixes for AI Timeouts
The app includes several optimizations for timeout issues:

1. **Fast Responses**: Common questions like "what is SQL?" get instant answers
2. **Template Queries**: Frequent data queries use pre-built SQL templates
3. **Configurable Timeouts**: Adjust in `.env` file:
   ```
   MAX_QUERY_TIMEOUT=120
   LOCAL_AI_TIMEOUT_SECONDS=60
   ```

### AI Model Options
```bash
# Faster but less accurate
LOCAL_AI_MODEL=llama3.1:8b

# Slower but more SQL-focused
LOCAL_AI_MODEL=codellama:7b

# Pull models manually
ollama pull llama3.1:8b
ollama pull codellama:7b
```

## 🔧 Configuration

### Environment Variables
Key settings in `.env`:

```bash
# Database
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_ACCOUNT=your_account

# AI Model
LOCAL_AI_MODEL=llama3.1:8b
MAX_QUERY_TIMEOUT=120

# API
API_PORT=8000
LOG_LEVEL=INFO
```

### Data Setup
1. Run the data generator:
   ```bash
   python data/data_generator.py
   python data/data_loader.py
   ```

2. Setup dbt models:
   ```bash
   cd retail_analytics_dbt
   dbt run
   ```

## 🛠️ Troubleshooting

### Common Issues

**AI Timeouts**
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
docker-compose restart ollama

# Use faster model
LOCAL_AI_MODEL=llama3.1:8b
```

**Database Connection**
```bash
# Test connection
curl http://localhost:8000/api/v1/health

# Check logs
docker-compose logs api
```

**Port Conflicts**
```bash
# Change ports in docker-compose.yml
ports:
  - "8080:8000"  # API
  - "8502:8501"  # Frontend
```

## 📊 Monitoring

Optional monitoring stack included:
- **Prometheus**: Metrics collection (port 9090)
- **Grafana**: Dashboards (port 3000, admin/admin123)
- **Health Checks**: Built-in API health endpoints

## 🚦 API Reference

### Key Endpoints
```bash
# Query natural language
POST /api/v1/query
{
  "question": "What was total revenue?",
  "timeout_seconds": 90
}

# Health check
GET /api/v1/health

# API documentation
GET /docs
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Add tests for new functionality
4. Submit a pull request

### Development Setup
```bash
# Clone and setup
git clone <your-fork>
cd agentic-data-explorer
conda env create -f environment.yml
conda activate agentic_data_explorer

# Run tests
pytest tests/

# Code formatting
black app/
isort app/
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the `docs/` folder
- **Issues**: Create GitHub issues for bugs
- **Discussions**: Use GitHub discussions for questions

## 🎯 Roadmap

- [ ] Support for more AI models (GPT, Claude)
- [ ] Multi-database support (PostgreSQL, MySQL)
- [ ] Advanced visualization features
- [ ] Query history and favorites
- [ ] User authentication
- [ ] Real-time data streaming

---

**Built with ❤️ by the Data Team**

*Transform your data into insights with the power of AI*