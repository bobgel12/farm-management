#!/bin/bash

# Chicken House Management - Development Setup Script
# This script sets up the development environment

set -e

echo "🐔 Setting up Chicken House Management Development Environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed. Please install npm."
    exit 1
fi

print_status "Setting up backend environment..."

# Create virtual environment for backend
if [ ! -d "backend/venv" ]; then
    print_status "Creating Python virtual environment..."
    cd backend
    python3 -m venv venv
    cd ..
    print_success "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
print_status "Installing Python dependencies..."
cd backend
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cd ..
print_success "Python dependencies installed"

print_status "Setting up frontend environment..."

# Install frontend dependencies
cd frontend
if [ ! -d "node_modules" ]; then
    print_status "Installing Node.js dependencies..."
    npm install
    print_success "Node.js dependencies installed"
else
    print_warning "Node.js dependencies already installed"
fi
cd ..

# Create environment files if they don't exist
print_status "Setting up environment files..."

if [ ! -f "backend/.env" ]; then
    print_status "Creating backend .env file..."
    cp env.example backend/.env
    print_warning "Please update backend/.env with your configuration"
else
    print_warning "Backend .env file already exists"
fi

if [ ! -f "frontend/.env" ]; then
    print_status "Creating frontend .env file..."
    cat > frontend/.env << EOF
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_ENVIRONMENT=development
EOF
    print_success "Frontend .env file created"
else
    print_warning "Frontend .env file already exists"
fi

# Set up database
print_status "Setting up database..."
cd backend
source venv/bin/activate
python manage.py migrate
print_success "Database migrations completed"

# Create superuser if it doesn't exist
print_status "Creating superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"
cd ..

print_success "Development environment setup completed!"
echo ""
print_status "To start the development servers:"
echo "  Backend:  cd backend && source venv/bin/activate && python manage.py runserver"
echo "  Frontend: cd frontend && npm start"
echo ""
print_status "Or use the provided scripts:"
echo "  ./scripts/start-dev.sh"
echo ""
print_status "Default admin credentials:"
echo "  Username: admin"
echo "  Password: admin123"
