#!/bin/bash

# Start the Chicken House Management app using Docker

echo "🚀 Starting Chicken House Management Application..."

# Check if Docker is installed and running
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    echo "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop/"
    echo "After installation, start Docker Desktop and run this script again."
    exit 1
fi

# Check if Docker daemon is running
if ! docker ps &> /dev/null; then
    echo "⚠️  Docker daemon is not running"
    echo "Please start Docker Desktop first, then run this script again."
    exit 1
fi

# Check if docker compose is available
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
elif docker-compose version &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo "❌ Docker Compose is not available"
    echo "Please install Docker Compose or use Docker Desktop which includes it."
    exit 1
fi

echo "✅ Docker is running"
echo "📦 Starting services..."

# Navigate to project directory
cd "$(dirname "$0")"

# Start services in detached mode
$COMPOSE_CMD up -d

# Wait a moment for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Run migrations
echo "🗄️  Running database migrations..."
$COMPOSE_CMD exec -T backend python manage.py migrate

# Check service status
echo ""
echo "📊 Service Status:"
$COMPOSE_CMD ps

echo ""
echo "✅ Application is starting!"
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8002/api"
echo "📊 Django Admin: http://localhost:8002/admin"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "📋 View logs with: $COMPOSE_CMD logs -f"
echo "🛑 Stop services with: $COMPOSE_CMD down"
echo ""

