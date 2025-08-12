#!/bin/bash
# scripts/setup.sh
# Complete setup script for Agentic Data Explorer with Local AI

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_header() { echo -e "${PURPLE}[SETUP]${NC} $1"; }

echo "🚀 Agentic Data Explorer - Complete Setup"
echo "=========================================="
echo "🤖 Features: Snowflake + dbt + Local AI + FastAPI + Streamlit"
echo ""

# =============================================================================
# SYSTEM REQUIREMENTS CHECK
# =============================================================================

check_system_requirements() {
    print_header "Checking system requirements..."
    
    # Check if conda is installed
    if ! command -v conda &> /dev/null; then
        print_error "Conda not found. Please install Anaconda or Miniconda first."
        echo ""
        echo "Download from:"
        echo "- Miniconda: https://docs.conda.io/en/latest/miniconda.html"
        echo "- Anaconda: https://www.anaconda.com/products/distribution"
        exit 1
    fi
    
    CONDA_VERSION=$(conda --version | cut -d' ' -f2)
    print_success "Conda $CONDA_VERSION found"
    
    # Check available space
    AVAILABLE_SPACE=$(df . | tail -1 | awk '{print $4}')
    if [ "$AVAILABLE_SPACE" -lt 10485760 ]; then  # 10GB in KB
        print_warning "Less than 10GB available space. AI models require significant storage."
    else
        print_success "Sufficient disk space available"
    fi
    
    # Check RAM
    TOTAL_RAM=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$TOTAL_RAM" -lt 8 ]; then
        print_warning "Less than 8GB RAM detected. Consider using smaller AI models."
    else
        print_success "Sufficient RAM available (${TOTAL_RAM}GB)"
    fi
}

# =============================================================================
# PROJECT STRUCTURE CREATION
# =============================================================================

create_project_structure() {
    print_header "Creating project directory structure..."
    
    # Main directories
    directories=(
        "data/output"
        "retail_analytics_dbt/models/staging"
        "retail_analytics_dbt/models/marts/core"
        "retail_analytics_dbt/tests"
        "retail_analytics_dbt/macros"
        "retail_analytics_dbt/seeds"
        "app/models"
        "app/services"
        "app/utils"
        "app/routers"
        "frontend/streamlit/components"
        "tests/test_api"
        "tests/test_data"
        "tests/benchmarks"
        "monitoring/grafana/dashboards"
        "monitoring/grafana/provisioning/dashboards"
        "monitoring/grafana/provisioning/datasources"
        "monitoring/prometheus"
        "scripts"
        "docs"
        "logs"
        "config"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        echo "Created: $dir"
    done
    
    print_success "Directory structure created"
}

create_python_packages() {
    print_header "Creating Python package files..."
    
    # Python package __init__.py files
    init_files=(
        "data/__init__.py"
        "app/__init__.py"
        "app/models/__init__.py"
        "app/services/__init__.py"
        "app/utils/__init__.py"
        "app/routers/__init__.py"
        "frontend/__init__.py"
        "frontend/streamlit/__init__.py"
        "frontend/streamlit/components/__init__.py"
        "tests/__init__.py"
        "tests/test_api/__init__.py"
        "tests/test_data/__init__.py"
        "tests/benchmarks/__init__.py"
    )
    
    for init_file in "${init_files[@]}"; do
        touch "$init_file"
        echo "Created: $init_file"
    done
    
    print_success "Python package files created"
}

# =============================================================================
# CONDA ENVIRONMENT SETUP
# =============================================================================

setup_conda_environment() {
    print_header "Setting up conda environment..."
    
    ENV_NAME="agentic_data_explorer"
    
    # Check if environment already exists
    if conda info --envs | grep -q "$ENV_NAME"; then
        print_warning "Conda environment '$ENV_NAME' already exists"
        print_status "Skipping environment creation (will update packages later)"
        CONDA_ENV_EXISTS=true
    else
        print_status "Creating new conda environment with Python 3.11..."
        conda create -n "$ENV_NAME" python=3.11 -y
        print_success "Conda environment '$ENV_NAME' created"
        CONDA_ENV_EXISTS=false
    fi
    
    # Initialize conda for this shell session
    eval "$(conda shell.bash hook)"
    
    print_status "Activating conda environment..."
    conda activate "$ENV_NAME"
    
    if [ "$CONDA_ENV_EXISTS" = false ]; then
        print_status "Updating conda and pip..."
        conda update conda -y --quiet
        pip install --upgrade pip --quiet
    fi
    
    print_success "Conda environment ready: $ENV_NAME"
}

# =============================================================================
# PACKAGE INSTALLATION
# =============================================================================

create_environment_yml() {
    print_header "Creating conda environment specification..."
    
    cat > environment.yml << 'EOF'
name: agentic_data_explorer

channels:
  - conda-forge
  - defaults

dependencies:
  # Python version
  - python=3.11

  # Core data science stack
  - pandas>=2.0.0
  - numpy>=1.24.0
  - sqlalchemy>=2.0.0
  
  # Web framework and API
  - fastapi>=0.104.0
  - uvicorn>=0.24.0
  
  # Development tools
  - pytest>=7.4.0
  - black>=23.0.0
  - isort>=5.12.0
  - jupyter>=1.0.0
  
  # Visualization
  - plotly>=5.17.0
  - requests>=2.31.0
  - python-dotenv>=1.0.0
  - click>=8.1.0
  
  # Install remaining packages via pip
  - pip
  - pip:
    # Snowflake packages
    - snowflake-connector-python>=3.0.0
    - snowflake-sqlalchemy>=1.5.0
    
    # dbt packages
    - dbt-snowflake>=1.6.0
    
    # Local AI packages
    - langchain>=0.1.0
    - langchain-community>=0.0.10
    - ollama>=0.1.0
    - transformers>=4.30.0
    - torch>=2.0.0
    - accelerate>=0.20.0
    - sentence-transformers>=2.2.0
    
    # FastAPI additional packages
    - pydantic>=2.5.0
    - pydantic-settings>=2.0.0
    - python-multipart>=0.0.6
    
    # Monitoring and logging
    - prometheus-client>=0.19.0
    - structlog>=23.0.0
    - rich>=13.0.0
    
    # Testing
    - pytest-asyncio>=0.21.0
    - pytest-benchmark>=4.0.0
    - httpx>=0.25.0
    
    # Frontend
    - streamlit>=1.28.0
EOF

    print_success "environment.yml created"
}

install_packages() {
    print_header "Installing Python packages..."
    
    if [ "$CONDA_ENV_EXISTS" = true ]; then
        print_status "Updating existing environment from environment.yml..."
        conda env update -f environment.yml --prune
    else
        print_status "Installing packages from environment.yml..."
        conda env update -f environment.yml
    fi
    
    print_success "Python packages installed/updated"
}

# =============================================================================
# LOCAL AI SETUP
# =============================================================================

setup_local_ai() {
    print_header "Setting up local AI with Ollama..."
    
    # Check if Ollama is already installed
    if command -v ollama &> /dev/null; then
        print_success "Ollama already installed"
        ollama --version
    else
        print_status "Installing Ollama..."
        curl -fsSL https://ollama.ai/install.sh | sh
        
        if command -v ollama &> /dev/null; then
            print_success "Ollama installed successfully"
        else
            print_error "Ollama installation failed"
            return 1
        fi
    fi
    
    # Start Ollama service in background
    print_status "Starting Ollama service..."
    ollama serve > /dev/null 2>&1 &
    OLLAMA_PID=$!
    
    # Wait for service to start
    sleep 5
    
    # Check if models are already downloaded
    EXISTING_MODELS=$(ollama list 2>/dev/null | tail -n +2 | wc -l)
    
    if [ "$EXISTING_MODELS" -gt 0 ]; then
        print_success "AI models already available:"
        ollama list
    else
        print_status "Downloading AI models (this may take 10-15 minutes)..."
        
        # Download models for SQL generation
        print_status "Downloading CodeLlama 7B for SQL generation (~3.8GB)..."
        ollama pull codellama:7b
        
        print_status "Downloading Llama 3.1 8B for general queries (~4.7GB)..."
        ollama pull llama3.1:8b
        
        print_success "AI models downloaded successfully!"
    fi
    
    # Test model functionality
    print_status "Testing AI model..."
    TEST_RESULT=$(ollama run codellama:7b "SELECT 1;" 2>/dev/null || echo "TEST_FAILED")
    
    if [[ "$TEST_RESULT" != "TEST_FAILED" ]]; then
        print_success "✅ AI models working correctly!"
    else
        print_warning "⚠️ AI model test had issues, but installation completed"
    fi
    
    # Keep Ollama running for development
    print_status "Ollama service running in background (PID: $OLLAMA_PID)"
}

# =============================================================================
# CONFIGURATION FILES
# =============================================================================

create_environment_config() {
    print_header "Creating environment configuration files..."
    
    # Create .env.example
    cat > .env.example << 'EOF'
# Snowflake Connection Settings
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_ACCOUNT=your_account_identifier
SNOWFLAKE_DATABASE=retail_analytics
SNOWFLAKE_SCHEMA=raw
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_ROLE=SYSADMIN

# Local AI Configuration
LOCAL_AI_BACKEND=ollama
LOCAL_AI_MODEL=codellama:7b
LOCAL_AI_HOST=localhost
LOCAL_AI_PORT=11434
LOCAL_AI_TEMPERATURE=0.1
LOCAL_AI_MAX_TOKENS=1000

# Application Settings
ENVIRONMENT=development
LOG_LEVEL=INFO
API_PORT=8000

# dbt Settings
DBT_PROFILES_DIR=./retail_analytics_dbt
DBT_PROJECT_DIR=./retail_analytics_dbt

# Monitoring Settings
GRAFANA_ADMIN_PASSWORD=admin
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
EOF

    # Create actual .env if it doesn't exist
    if [ ! -f ".env" ]; then
        cp .env.example .env
        print_success "Created .env file from template"
        print_warning "🔐 IMPORTANT: Edit .env with your actual Snowflake credentials!"
    else
        print_warning ".env file already exists - not overwriting"
    fi
}

setup_dbt_configuration() {
    print_header "Setting up dbt configuration..."
    
    # Create dbt profiles directory
    mkdir -p ~/.dbt
    
    # Create dbt profiles.yml
    cat > ~/.dbt/profiles.yml << 'EOF'
retail_analytics:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: "{{ env_var('SNOWFLAKE_USER') }}"
      password: "{{ env_var('SNOWFLAKE_PASSWORD') }}"
      role: "{{ env_var('SNOWFLAKE_ROLE') }}"
      database: "{{ env_var('SNOWFLAKE_DATABASE') }}"
      warehouse: "{{ env_var('SNOWFLAKE_WAREHOUSE') }}"
      schema: analytics
      threads: 4
      keepalives_idle: 600
EOF

    print_success "dbt profile created at ~/.dbt/profiles.yml"
    
    # Create dbt project configuration
    cat > retail_analytics_dbt/dbt_project.yml << 'EOF'
name: 'retail_analytics'
version: '1.0.0'
config-version: 2

profile: 'retail_analytics'

model-paths: ["models"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]

target-path: "target"
clean-targets:
  - "target"
  - "dbt_packages"

models:
  retail_analytics:
    staging:
      +materialized: view
      +docs:
        node_color: "lightblue"
    marts:
      +materialized: table
      +docs:
        node_color: "lightgreen"

vars:
  start_date: '2023-01-01'
  customer_segments: ['Premium', 'Standard', 'Budget']
  regions: ['North', 'South', 'East', 'West', 'Central']
EOF

    # Create dbt packages.yml
    cat > retail_analytics_dbt/packages.yml << 'EOF'
packages:
  - package: dbt-labs/dbt_utils
    version: 1.3.0
EOF

    print_success "dbt project configuration created"
    
    # Install dbt packages
    print_status "Installing dbt packages..."
    cd retail_analytics_dbt
    dbt deps
    cd ..
    
    print_success "dbt packages installed"
}

create_local_ai_config() {
    print_header "Creating local AI configuration..."
    
    cat > config/local_ai_config.yaml << 'EOF'
# Local AI Model Configuration
models:
  primary:
    name: "codellama:7b"
    type: "ollama"
    description: "Primary model for SQL generation"
    
  fallback:
    name: "llama3.1:8b"
    type: "ollama" 
    description: "Fallback model for general queries"

# Inference settings
inference:
  temperature: 0.1
  max_tokens: 1000
  timeout_seconds: 30
  
# Ollama settings  
ollama:
  host: "localhost"
  port: 11434
  
# System requirements
system:
  min_ram_gb: 4
  use_gpu: auto
EOF

    print_success "Local AI configuration created"
}

# =============================================================================
# PROJECT FILES CREATION
# =============================================================================

create_gitignore() {
    print_header "Creating .gitignore file..."
    
    cat > .gitignore << 'EOF'
# Environment variables
.env
.env.local
.env.*.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments (both venv and conda)
venv/
env/
ENV/
.venv/

# Conda
.conda/
conda-meta/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# dbt
target/
dbt_packages/
logs/

# Data files (you can uncomment these if you want to ignore data)
# data/output/*.csv
# data/output/*.json
# data/output/*.parquet

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db

# Jupyter Notebooks
.ipynb_checkpoints

# pytest
.pytest_cache/
.coverage
htmlcov/

# Docker
.dockerignore

# Temporary files
*.tmp
*.temp

# Local AI model cache (can be large)
.ollama/
model_cache/

# Monitoring
monitoring/data/

# Streamlit
.streamlit/
EOF

    print_success ".gitignore created"
}

create_readme() {
    print_header "Creating README.md..."
    
    cat > README.md << 'EOF'
# 🔍 Agentic Data Explorer

An AI-powered data exploration platform that allows non-technical users to query retail data using natural language.

## 🏗️ Architecture

- **Data Warehouse**: Snowflake
- **Data Transformation**: dbt (ELT pipeline)
- **AI Agent**: Local models via Ollama (CodeLlama, Llama 3.1)
- **Backend API**: FastAPI + LangChain
- **Frontend**: Streamlit
- **Monitoring**: Prometheus + Grafana

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Run the complete setup script
chmod +x scripts/setup.sh
./scripts/setup.sh

# Activate conda environment
conda activate agentic_data_explorer
```

### 2. Configure Credentials
```bash
# Edit .env with your Snowflake credentials
nano .env
```

### 3. Setup Data Pipeline
```bash
# Generate sample data
python data/data_generator.py

# Create Snowflake database structure
python scripts/run_snowflake_setup.py

# Load data to Snowflake
python data/data_loader.py

# Run dbt transformations
cd retail_analytics_dbt
dbt run
dbt test
cd ..
```

### 4. Start Services
```bash
# Start Ollama (if not already running)
ollama serve &

# Start FastAPI backend
uvicorn app.main:app --reload --port 8000

# Start Streamlit frontend (in another terminal)
streamlit run frontend/streamlit/demo_app.py
```

### 5. Access Applications
- **API Documentation**: http://localhost:8000/docs
- **Streamlit UI**: http://localhost:8501
- **API Health**: http://localhost:8000/health

## 📊 Example Queries

Try these natural language questions:
- "What was the total revenue last month?"
- "Which product category has the highest sales?"
- "Show me the top 5 stores by revenue"
- "How do weekend sales compare to weekday sales?"

## 🛠️ Development

### Project Structure
```
agentic-data-explorer/
├── data/                  # Data generation and loading
├── retail_analytics_dbt/  # dbt transformations
├── app/                   # FastAPI backend
├── frontend/             # Streamlit demo
├── tests/                # Test suites
├── config/               # Configuration files
└── scripts/              # Utility scripts
```

### Useful Commands
```bash
# Activate environment
conda activate agentic_data_explorer

# Run dbt models
cd retail_analytics_dbt && dbt run

# Test data quality
dbt test

# Run API tests
pytest tests/

# Format code
black . && isort .
```

## 🎯 Features

- ✅ **Natural Language Queries** - Ask questions in plain English
- ✅ **Local AI Models** - No API costs, complete privacy
- ✅ **Clean Data Pipeline** - dbt-powered ELT transformations
- ✅ **Data Quality Testing** - Automated validation
- ✅ **Performance Monitoring** - Built-in metrics
- ✅ **Interactive UI** - Streamlit-based demo interface

## 🔧 Troubleshooting

### Common Issues

**Ollama not responding:**
```bash
# Restart Ollama service
pkill ollama
ollama serve &
```

**dbt connection issues:**
```bash
# Test dbt connection
cd retail_analytics_dbt
dbt debug
```

**Environment issues:**
```bash
# Recreate conda environment
conda env remove -n agentic_data_explorer
./scripts/setup.sh
```

## 📚 Documentation

- [dbt Documentation](./retail_analytics_dbt/target/index.html) (after running `dbt docs generate`)
- [API Documentation](http://localhost:8000/docs) (when API is running)
- [Snowflake Setup Guide](./docs/snowflake_setup.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

---

Built with ❤️ using modern data stack and local AI
EOF

    print_success "README.md created"
}

# =============================================================================
# VERIFICATION AND TESTING
# =============================================================================

verify_setup() {
    print_header "Verifying setup..."
    
    # Test conda environment
    print_status "Testing conda environment..."
    if conda info --envs | grep -q "agentic_data_explorer"; then
        print_success "✅ Conda environment exists"
    else
        print_error "❌ Conda environment not found"
        return 1
    fi
    
    # Test Python packages
    print_status "Testing key Python packages..."
    conda activate agentic_data_explorer
    
    # Test core packages
    python -c "import pandas, snowflake.connector, langchain, fastapi, streamlit; print('✅ Core packages imported successfully')" 2>/dev/null || {
        print_error "❌ Some core packages failed to import"
        return 1
    }
    
    # Test dbt
    print_status "Testing dbt..."
    cd retail_analytics_dbt
    if dbt debug --quiet 2>/dev/null; then
        print_success "✅ dbt configuration valid"
    else
        print_warning "⚠️ dbt configuration needs Snowflake credentials"
    fi
    cd ..
    
    # Test Ollama
    print_status "Testing Ollama..."
    if curl -s http://localhost:11434/api/tags > /dev/null; then
        print_success "✅ Ollama service responding"
    else
        print_warning "⚠️ Ollama service not responding (may need restart)"
    fi
    
    print_success "Setup verification completed!"
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

main() {
    print_header "Starting complete setup process..."
    
    check_system_requirements
    create_project_structure
    create_python_packages
    setup_conda_environment
    create_environment_yml
    install_packages
    setup_local_ai
    create_environment_config
    setup_dbt_configuration
    create_local_ai_config
    create_gitignore
    create_readme
    verify_setup
    
    echo ""
    print_success "🎉 Setup completed successfully!"
    echo ""
    echo "📋 What was created:"
    echo "  ✅ Complete project directory structure"
    echo "  ✅ Conda environment: agentic_data_explorer"
    echo "  ✅ All Python packages installed"
    echo "  ✅ Ollama with AI models (CodeLlama 7B, Llama 3.1 8B)"
    echo "  ✅ dbt project configured"
    echo "  ✅ Configuration files (.env, profiles.yml)"
    echo "  ✅ Documentation (README.md)"
    echo ""
    echo "🚀 Next steps:"
    echo "  1. Edit .env with your Snowflake credentials"
    echo "  2. Run: python data/data_generator.py"
    echo "  3. Run: python data/data_loader.py"
    echo "  4. Run: cd retail_analytics_dbt && dbt run"
    echo "  5. Start building the FastAPI backend!"
    echo ""
    echo "💡 To activate environment: conda activate agentic_data_explorer"
    echo "💡 To restart Ollama: ollama serve &"
    echo ""
    print_success "Happy coding! 🎯"
}

# Run main function
main "$@"
EOF

# Make the script executable
chmod +x scripts/setup.sh

print_success "Complete setup script created at scripts/setup.sh"