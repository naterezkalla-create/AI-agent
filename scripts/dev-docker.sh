#!/bin/bash
# Local Docker development setup

set -e

echo "🐳 Setting up Docker development environment..."
echo ""

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running"
    echo "   Start Docker Desktop or the Docker daemon"
    exit 1
fi

# Build images
echo "🔨 Building Docker images..."
docker-compose build

# Create .env if it doesn't exist
if [ ! -f ./backend/.env ]; then
    echo ""
    echo "📝 Creating backend/.env from template..."
    cp ./backend/.env.example ./backend/.env
    echo "⚠️  Update backend/.env with your configuration:"
    echo "   - SUPABASE_URL and SUPABASE_KEY"
    echo "   - JWT_SECRET and other settings"
fi

# Start services
echo ""
echo "🚀 Starting Docker services..."
docker-compose up -d

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to start..."
sleep 5

# Check health
echo ""
echo "🏥 Checking service health..."

if curl -s http://localhost:8000/health &> /dev/null; then
    echo "✅ Backend is running on http://localhost:8000"
else
    echo "⚠️  Backend may still be starting..."
fi

if curl -s http://localhost:3000 &> /dev/null; then
    echo "✅ Frontend is running on http://localhost:3000"
else
    echo "⚠️  Frontend may still be starting..."
fi

echo ""
echo "📚 Useful commands:"
echo "   docker-compose logs -f          # View logs"
echo "   docker-compose down             # Stop services"
echo "   docker-compose ps               # List services"
echo ""
echo "🎉 Development environment ready!"
