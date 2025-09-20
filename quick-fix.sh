#!/bin/bash

# Quick Fix Script for Chicken House Management System
# This script addresses common issues that may occur during development

echo "🔧 Chicken House Management - Quick Fix Script"
echo "=============================================="

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to kill processes on a port
kill_port() {
    local port=$1
    if lsof -i :$port &> /dev/null; then
        echo "⚠️  Port $port is in use. Attempting to free it..."
        lsof -ti :$port | grep -v $(docker ps -q) | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
}

# Check for port conflicts
echo "🔍 Checking for port conflicts..."
kill_port 3000
kill_port 8000
kill_port 5432

# Check Docker status
if ! command_exists docker; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if containers are running
if ! docker-compose ps | grep -q "Up"; then
    echo "🚀 Starting containers..."
    docker-compose up -d
    sleep 10
fi

# Fix database issues
echo "🗄️ Checking database..."
if ! docker-compose exec db pg_isready -U postgres &> /dev/null; then
    echo "⚠️  Database not ready. Restarting..."
    docker-compose restart db
    sleep 10
fi

# Fix migration issues
echo "📝 Checking migrations..."
if ! docker-compose exec backend python manage.py showmigrations farms &> /dev/null; then
    echo "⚠️  Creating migrations directories..."
    docker-compose exec backend mkdir -p farms/migrations houses/migrations tasks/migrations
    docker-compose exec backend touch farms/migrations/__init__.py houses/migrations/__init__.py tasks/migrations/__init__.py
    docker-compose exec backend python manage.py makemigrations
    docker-compose exec backend python manage.py migrate
fi

# Fix frontend compilation issues
echo "⚛️ Checking frontend..."
if ! curl -s http://localhost:3000 &> /dev/null; then
    echo "⚠️  Frontend not responding. Restarting..."
    docker-compose restart frontend
    sleep 15
fi

# Test API
echo "🧪 Testing API..."
if curl -s http://localhost:8000/api/auth/login/ -X POST \
    -H "Content-Type: application/json" \
    -H "Origin: http://localhost:3000" \
    -d '{"username": "admin", "password": "admin123"}' &> /dev/null; then
    echo "✅ API is working"
else
    echo "⚠️  API test failed. Restarting backend..."
    docker-compose restart backend
    sleep 10
fi

# Show status
echo ""
echo "📊 Current Status:"
echo "=================="
docker-compose ps

echo ""
echo "🌐 Application URLs:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000/api"
echo "   Admin Panel: http://localhost:8000/admin"

echo ""
echo "✅ Quick fix complete!"
echo ""
echo "If issues persist, try running: ./setup.sh"
