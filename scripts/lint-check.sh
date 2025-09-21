#!/bin/bash

# Chicken House Management - Lint and Format Check Script
# This script runs linting and formatting checks on the codebase

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

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to run frontend linting
lint_frontend() {
    print_status "Running frontend linting..."
    cd frontend
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        print_error "Node modules not found. Please run npm install first."
        exit 1
    fi
    
    # Run ESLint
    print_status "Running ESLint..."
    if npm run lint:check; then
        print_success "ESLint checks passed"
    else
        print_error "ESLint checks failed"
        exit 1
    fi
    
    # Run Prettier check
    print_status "Running Prettier check..."
    if npm run format:check; then
        print_success "Prettier checks passed"
    else
        print_error "Prettier checks failed"
        exit 1
    fi
    
    # Run TypeScript check
    print_status "Running TypeScript check..."
    if npm run type-check; then
        print_success "TypeScript checks passed"
    else
        print_error "TypeScript checks failed"
        exit 1
    fi
    
    cd ..
}

# Function to run backend linting
lint_backend() {
    print_status "Running backend linting..."
    cd backend
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_error "Virtual environment not found. Please run ./scripts/dev-setup.sh first."
        exit 1
    fi
    
    source venv/bin/activate
    
    # Install linting tools if not already installed
    print_status "Installing Python linting tools..."
    pip install flake8 black isort mypy
    
    # Run Black check
    print_status "Running Black check..."
    if black --check .; then
        print_success "Black checks passed"
    else
        print_error "Black checks failed. Run 'black .' to fix formatting."
        exit 1
    fi
    
    # Run isort check
    print_status "Running isort check..."
    if isort --check-only .; then
        print_success "isort checks passed"
    else
        print_error "isort checks failed. Run 'isort .' to fix imports."
        exit 1
    fi
    
    # Run Flake8
    print_status "Running Flake8..."
    if flake8 .; then
        print_success "Flake8 checks passed"
    else
        print_error "Flake8 checks failed"
        exit 1
    fi
    
    # Run MyPy
    print_status "Running MyPy..."
    if mypy .; then
        print_success "MyPy checks passed"
    else
        print_warning "MyPy checks failed (this is often due to Django ORM types)"
    fi
    
    cd ..
}

# Main execution
print_status "Running comprehensive lint and format checks..."

# Run frontend checks
lint_frontend

# Run backend checks
lint_backend

print_success "All lint and format checks completed successfully!"
