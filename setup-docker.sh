#!/bin/bash

# Docker Setup Script for Chicken House Management System
# This script sets up and runs the application using Docker

set -e

echo "🐔 Setting up Chicken House Management System with Docker..."

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

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed!"
    echo ""
    echo "Please install Docker Desktop for Mac:"
    echo "  1. Visit: https://www.docker.com/products/docker-desktop"
    echo "  2. Download and install Docker Desktop"
    echo "  3. Launch Docker Desktop and complete the setup"
    echo "  4. Run this script again"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    print_error "Docker is not running!"
    echo ""
    echo "Please start Docker Desktop and wait for it to fully start, then run this script again."
    exit 1
fi

print_success "Docker is installed and running"

# Detect docker-compose command
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    print_error "Docker Compose is not available!"
    exit 1
fi

print_success "Found Docker Compose: $DOCKER_COMPOSE"

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_status "Creating .env file from template..."
    if [ -f "env.example" ]; then
        cp env.example .env
        print_success ".env file created"
        print_warning "You may want to customize .env file, but default values work for local development"
    else
        print_error "env.example file not found!"
        exit 1
    fi
else
    print_warning ".env file already exists, skipping..."
fi

# Build and start containers
print_status "Building Docker images (this may take a few minutes the first time)..."
$DOCKER_COMPOSE build

print_status "Starting all services..."
$DOCKER_COMPOSE up -d

# Wait for services to be healthy
print_status "Waiting for services to be ready..."
sleep 10

# Check service status
print_status "Checking service status..."
$DOCKER_COMPOSE ps

echo ""
print_success "🎉 Setup complete! Services are starting..."
echo ""
echo "📱 Access the application:"
echo "   Frontend:  http://localhost:3002"
echo "   Backend:   http://localhost:8002/api"
echo "   Admin:     http://localhost:8002/admin"
echo ""
echo "👤 Default admin credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "📋 Useful commands:"
echo "   View logs:        $DOCKER_COMPOSE logs -f"
echo "   Stop services:    $DOCKER_COMPOSE down"
echo "   Restart services: $DOCKER_COMPOSE restart"
echo "   Check status:     $DOCKER_COMPOSE ps"
echo ""
echo "   Or use Make commands:"
echo "   make logs         - View logs"
echo "   make down         - Stop services"
echo "   make restart      - Restart services"
echo "   make status       - Show status"
echo ""
print_warning "Note: It may take a minute or two for all services to fully start."
print_status "Monitor the logs with: $DOCKER_COMPOSE logs -f"

