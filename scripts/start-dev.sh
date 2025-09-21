#!/bin/bash

# Chicken House Management - Start Development Servers
# This script starts both backend and frontend development servers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to cleanup background processes on exit
cleanup() {
    print_status "Shutting down development servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

print_status "Starting Chicken House Management Development Servers..."

# Check if virtual environment exists
if [ ! -d "backend/venv" ]; then
    print_error "Virtual environment not found. Please run ./scripts/dev-setup.sh first."
    exit 1
fi

# Check if node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    print_error "Node modules not found. Please run ./scripts/dev-setup.sh first."
    exit 1
fi

# Start backend server
print_status "Starting backend server..."
cd backend
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000 &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Start frontend server
print_status "Starting frontend server..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

print_success "Development servers started!"
echo ""
print_status "Backend:  http://localhost:8000"
print_status "Frontend: http://localhost:3000"
print_status "Admin:    http://localhost:8000/admin"
echo ""
print_status "Press Ctrl+C to stop all servers"

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID
