#!/bin/bash

# Chicken House Management - Fix Code Script
# This script automatically fixes common code issues

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

# Function to fix frontend code
fix_frontend() {
    print_status "Fixing frontend code..."
    cd frontend
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        print_error "Node modules not found. Please run npm install first."
        exit 1
    fi
    
    # Run ESLint with --fix
    print_status "Running ESLint with auto-fix..."
    npm run lint
    
    # Run Prettier
    print_status "Running Prettier..."
    npm run format
    
    print_success "Frontend code fixed"
    cd ..
}

# Function to fix backend code
fix_backend() {
    print_status "Fixing backend code..."
    cd backend
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_error "Virtual environment not found. Please run ./scripts/dev-setup.sh first."
        exit 1
    fi
    
    source venv/bin/activate
    
    # Install formatting tools if not already installed
    print_status "Installing Python formatting tools..."
    pip install black isort
    
    # Run Black
    print_status "Running Black..."
    black .
    
    # Run isort
    print_status "Running isort..."
    isort .
    
    print_success "Backend code fixed"
    cd ..
}

# Main execution
print_status "Fixing code formatting and linting issues..."

# Fix frontend
fix_frontend

# Fix backend
fix_backend

print_success "Code fixing completed!"
print_status "Run ./scripts/lint-check.sh to verify all issues are resolved."
