#!/bin/bash
# Deployment script for Agentic Data Explorer
# This script helps deploy the application in different environments

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed"
}

# Check if .env file exists
check_env_file() {
    if [[ ! -f ".env" ]]; then
        print_warning ".env file not found. Creating from template..."
        cp .env.example .env
        print_error "Please edit .env file with your Snowflake credentials before continuing."
        print_status "Edit the following required fields in .env:"
        echo "  - SNOWFLAKE_USER"
        echo "  - SNOWFLAKE_PASSWORD"
        echo "  - SNOWFLAKE_ACCOUNT"
        exit 1
    fi
    print_success ".env file found"
}

# Check if Snowflake credentials are set
check_snowflake_config() {
    source .env
    if [[ "$SNOWFLAKE_USER" == "your_username" ]] || [[ -z "$SNOWFLAKE_USER" ]]; then
        print_error "Snowflake credentials not configured in .env file"
        exit 1
    fi
    print_success "Snowflake configuration appears to be set"
}

# Deploy function
deploy() {
    local mode=${1:-"production"}
    
    print_status "Deploying in $mode mode..."
    
    case $mode in
        "production"|"prod")
            print_status "Starting full production stack..."
            docker-compose down
            docker-compose up -d
            ;;
        "development"|"dev")
            print_status "Starting development stack..."
            docker-compose -f docker-compose.dev.yml down
            docker-compose -f docker-compose.dev.yml up -d
            ;;
        "minimal")
            print_status "Starting minimal stack (API + Frontend only)..."
            docker-compose down
            docker-compose up -d api frontend
            ;;
        *)
            print_error "Unknown deployment mode: $mode"
            print_status "Available modes: production, development, minimal"
            exit 1
            ;;
    esac
}

# Wait for services to be healthy
wait_for_services() {
    print_status "Waiting for services to start..."
    
    # Wait for API health check
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f http://localhost:8000/api/v1/health &> /dev/null; then
            print_success "API is healthy"
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            print_error "API failed to start within timeout"
            print_status "Check logs with: docker-compose logs api"
            exit 1
        fi
        
        print_status "Waiting for API... (attempt $attempt/$max_attempts)"
        sleep 5
        ((attempt++))
    done
    
    # Check if frontend is accessible
    if curl -f http://localhost:8501 &> /dev/null; then
        print_success "Frontend is accessible"
    else
        print_warning "Frontend may still be starting up"
    fi
}

# Setup Ollama models
setup_ollama() {
    print_status "Setting up Ollama AI models..."
    
    # Wait for Ollama to be ready
    sleep 10
    
    # Pull the configured model
    source .env
    local model=${LOCAL_AI_MODEL:-"llama3.1:8b"}
    
    print_status "Pulling AI model: $model"
    docker-compose exec ollama ollama pull "$model" || print_warning "Failed to pull model automatically"
    
    print_status "You can manually pull models with:"
    print_status "docker-compose exec ollama ollama pull llama3.1:8b"
    print_status "docker-compose exec ollama ollama pull codellama:7b"
}

# Show status and URLs
show_status() {
    print_success "\n=== Agentic Data Explorer Deployed ==="
    print_status "Application URLs:"
    echo "  🎨 Frontend:     http://localhost:8501"
    echo "  📡 API:          http://localhost:8000"
    echo "  📚 API Docs:     http://localhost:8000/docs"
    echo "  ❤️  Health:       http://localhost:8000/api/v1/health"
    
    if docker-compose ps | grep grafana &> /dev/null; then
        echo "  📊 Grafana:      http://localhost:3000 (admin/admin123)"
    fi
    
    if docker-compose ps | grep prometheus &> /dev/null; then
        echo "  📈 Prometheus:   http://localhost:9090"
    fi
    
    print_status "\nUseful commands:"
    echo "  📋 View logs:    docker-compose logs -f"
    echo "  🔄 Restart:      docker-compose restart"
    echo "  🛑 Stop:         docker-compose down"
    echo "  🧹 Clean up:     docker-compose down -v"
    
    print_status "\nTry asking: 'What was the total revenue last month?'"
}

# Main deployment flow
main() {
    local mode=${1:-"production"}
    
    print_status "🚀 Agentic Data Explorer Deployment Script"
    print_status "=========================================="
    
    check_docker
    check_env_file
    check_snowflake_config
    
    deploy "$mode"
    wait_for_services
    setup_ollama
    show_status
    
    print_success "\n🎉 Deployment completed successfully!"
}

# Help function
show_help() {
    echo "Agentic Data Explorer Deployment Script"
    echo ""
    echo "Usage: $0 [MODE]"
    echo ""
    echo "Modes:"
    echo "  production   Full production stack with monitoring (default)"
    echo "  development  Development mode with hot reload"
    echo "  minimal      API and Frontend only"
    echo ""
    echo "Examples:"
    echo "  $0                    # Deploy in production mode"
    echo "  $0 development        # Deploy in development mode"
    echo "  $0 minimal            # Deploy minimal stack"
    echo ""
    echo "Requirements:"
    echo "  - Docker and Docker Compose installed"
    echo "  - .env file with Snowflake credentials"
    echo "  - 8GB+ RAM for AI models"
}

# Handle command line arguments
if [[ $# -eq 0 ]]; then
    main "production"
elif [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    show_help
else
    main "$1"
fi