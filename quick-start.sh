#!/bin/bash
# Quick start script for Agentic Data Explorer
# Minimal setup for testing and development

set -e

echo "🔍 Agentic Data Explorer - Quick Start"
echo "====================================="

# Check for .env file
if [[ ! -f ".env" ]]; then
    echo "⚠️  Creating .env file from template..."
    cp .env.example .env
    echo "📝 Please edit .env file with your Snowflake credentials:"
    echo "   - SNOWFLAKE_USER"
    echo "   - SNOWFLAKE_PASSWORD" 
    echo "   - SNOWFLAKE_ACCOUNT"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# Start minimal services
echo "🚀 Starting services..."
docker-compose -f docker-compose.simple.yml up -d

echo "⏳ Waiting for services to start..."
sleep 15

# Check if services are running
if curl -f http://localhost:8000/api/v1/health &> /dev/null; then
    echo "✅ API is running!"
else
    echo "❌ API is not responding yet, check logs with:"
    echo "   docker-compose -f docker-compose.simple.yml logs api"
fi

if curl -f http://localhost:8501 &> /dev/null; then
    echo "✅ Frontend is running!"
else
    echo "⏳ Frontend is still starting up..."
fi

echo ""
echo "🎉 Quick start complete!"
echo ""
echo "Access your application:"
echo "  🎨 Frontend:  http://localhost:8501"
echo "  📡 API:       http://localhost:8000"
echo "  📚 API Docs:  http://localhost:8000/docs"
echo ""
echo "Useful commands:"
echo "  📊 View logs: docker-compose -f docker-compose.simple.yml logs -f"
echo "  🔄 Restart:   docker-compose -f docker-compose.simple.yml restart"
echo "  🛑 Stop:      docker-compose -f docker-compose.simple.yml down"
echo ""
echo "💡 Try asking: 'What is SQL?' or 'What was the total revenue?'"
echo ""
echo "📋 First-time setup:"
echo "  1. Pull AI model: docker-compose -f docker-compose.simple.yml exec ollama ollama pull llama3.1:8b"
echo "  2. Test health: curl http://localhost:8000/api/v1/health"
echo "  3. Start exploring your data!"
