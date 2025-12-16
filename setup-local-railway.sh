#!/bin/bash

# Local Development Setup Script with Railway Environment
# This script installs necessary components and sets up the application
# to run locally using Docker with Railway environment variables

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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

print_header() {
    echo -e "${CYAN}"
    echo "════════════════════════════════════════════════════════════"
    echo "$1"
    echo "════════════════════════════════════════════════════════════"
    echo -e "${NC}"
}

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_warning "This script is optimized for macOS. Some installation steps may differ on other systems."
fi

print_header "🐔 Chicken House Management - Local Setup with Railway"

# ============================================================================
# Step 1: Check and Install Colima (Docker Runtime)
# ============================================================================
print_header "Step 1: Checking Colima and Docker Installation"

# Check if Homebrew is installed (required for Colima)
if ! command -v brew &> /dev/null; then
    print_error "Homebrew is not installed!"
    echo ""
    echo "Colima requires Homebrew for installation on macOS."
    echo ""
    read -p "Would you like to install Homebrew now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        print_success "Homebrew installed"
        
        # Add Homebrew to PATH if needed (for Apple Silicon Macs)
        if [[ -f "/opt/homebrew/bin/brew" ]]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
    else
        print_error "Homebrew is required. Exiting."
        exit 1
    fi
fi

# Check and install Colima
if ! command -v colima &> /dev/null; then
    print_warning "Colima is not installed"
    echo ""
    echo "Colima is a lightweight Docker runtime alternative to Docker Desktop."
    echo "It provides Docker compatibility without needing the Docker Desktop GUI."
    echo ""
    read -p "Would you like to install Colima now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Installing Colima..."
        brew install colima
        print_success "Colima installed"
    else
        print_error "Colima is required. Exiting."
        exit 1
    fi
fi

# Check and install Docker CLI (if not already installed)
if ! command -v docker &> /dev/null; then
    print_warning "Docker CLI is not installed"
    print_status "Installing Docker CLI..."
    brew install docker
    print_success "Docker CLI installed"
fi

# Check Colima status and start if needed
if colima status &> /dev/null; then
    COLIMA_STATUS=$(colima status 2>/dev/null | head -1 || echo "running")
    print_success "Colima is running: $COLIMA_STATUS"
else
    print_warning "Colima is not running"
    print_status "Starting Colima (this may take a minute)..."
    
    # Start Colima with reasonable defaults
    # You can customize CPU/memory if needed: colima start --cpu 4 --memory 8
    colima start
    
    # Verify it started successfully
    if colima status &> /dev/null; then
        print_success "Colima started successfully"
    else
        print_error "Failed to start Colima"
        exit 1
    fi
fi

# Verify Docker is working with Colima
if docker info &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    DOCKER_CONTEXT=$(docker context show 2>/dev/null || echo "default")
    print_success "Docker is working: $DOCKER_VERSION (context: $DOCKER_CONTEXT)"
else
    print_warning "Docker info check failed, but Colima is running"
    print_status "Setting Docker context to Colima..."
    
    # Check if colima context exists
    if docker context ls | grep -q colima; then
        docker context use colima 2>/dev/null || true
    fi
    
    # Verify again
    if docker info &> /dev/null; then
        print_success "Docker is now working with Colima"
    else
        print_error "Docker is not responding. Try restarting Colima: colima restart"
        exit 1
    fi
fi

# Detect docker-compose command
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    print_warning "Docker Compose not found, installing..."
    brew install docker-compose
    DOCKER_COMPOSE="docker compose"
fi

print_success "Docker Compose: $DOCKER_COMPOSE"

# ============================================================================
# Step 2: Check and Install Node.js (for Railway CLI)
# ============================================================================
print_header "Step 2: Checking Node.js Installation"

if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    print_success "Node.js is installed: $NODE_VERSION"
    
    # Check version (need v14+)
    NODE_MAJOR=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_MAJOR" -lt 14 ]; then
        print_warning "Node.js version $NODE_VERSION may be too old. Railway CLI requires Node.js 14+"
    fi
else
    print_warning "Node.js is not installed"
    echo ""
    echo "Node.js is required to install the Railway CLI."
    echo ""
    read -p "Would you like to install Node.js using Homebrew? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if command -v brew &> /dev/null; then
            print_status "Installing Node.js via Homebrew..."
            brew install node
            print_success "Node.js installed"
        else
            print_error "Homebrew is not installed. Please install Node.js manually:"
            echo "  Visit: https://nodejs.org/"
            echo "  Or install Homebrew first: https://brew.sh/"
            exit 1
        fi
    else
        print_error "Node.js is required for Railway CLI. Exiting."
        exit 1
    fi
fi

# ============================================================================
# Step 3: Check and Install Railway CLI
# ============================================================================
print_header "Step 3: Checking Railway CLI Installation"

if command -v railway &> /dev/null; then
    RAILWAY_VERSION=$(railway --version 2>/dev/null || echo "installed")
    print_success "Railway CLI is installed: $RAILWAY_VERSION"
else
    print_warning "Railway CLI is not installed"
    echo ""
    read -p "Would you like to install Railway CLI now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Installing Railway CLI..."
        npm install -g @railway/cli
        
        if command -v railway &> /dev/null; then
            print_success "Railway CLI installed successfully"
        else
            print_error "Failed to install Railway CLI"
            print_status "You may need to add npm global bin to your PATH"
            print_status "Or install manually: npm install -g @railway/cli"
            exit 1
        fi
    else
        print_error "Railway CLI is required to fetch environment variables. Exiting."
        exit 1
    fi
fi

# ============================================================================
# Step 4: Login to Railway
# ============================================================================
print_header "Step 4: Railway Authentication"

if railway whoami &> /dev/null; then
    RAILWAY_USER=$(railway whoami 2>/dev/null || echo "authenticated")
    print_success "Logged in to Railway as: $RAILWAY_USER"
else
    print_warning "Not logged in to Railway"
    echo ""
    echo "You need to log in to Railway to fetch environment variables."
    echo ""
    read -p "Would you like to log in to Railway now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Opening Railway login..."
        railway login
        
        if railway whoami &> /dev/null; then
            print_success "Successfully logged in to Railway"
        else
            print_error "Failed to log in to Railway"
            exit 1
        fi
    else
        print_error "Railway login is required. Exiting."
        exit 1
    fi
fi

# ============================================================================
# Step 5: Link to Railway Project
# ============================================================================
print_header "Step 5: Linking to Railway Project"

if railway status &> /dev/null; then
    print_success "Already linked to a Railway project"
    railway status
else
    print_warning "Not linked to a Railway project"
    echo ""
    echo "You need to link this project to a Railway project."
    echo "This will allow fetching environment variables from Railway."
    echo ""
    read -p "Would you like to link to a Railway project now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Linking to Railway project..."
        print_status "Please select your Railway project when prompted..."
        railway link
        
        if railway status &> /dev/null; then
            print_success "Successfully linked to Railway project"
            railway status
        else
            print_error "Failed to link to Railway project"
            exit 1
        fi
    else
        print_warning "Skipping Railway project linking"
        print_warning "You can link later with: railway link"
    fi
fi

# ============================================================================
# Step 6: Fetch Environment Variables from Railway
# ============================================================================
print_header "Step 6: Fetching Environment Variables from Railway"

if railway status &> /dev/null; then
    print_status "Fetching environment variables from Railway..."
    
    # Create temporary file for Railway env vars
    TEMP_ENV=".env.railway.tmp"
    
    # Try to fetch variables
    if railway variables --kv > "$TEMP_ENV" 2>/dev/null; then
        # Success with --kv flag
        print_success "Fetched environment variables from Railway"
    elif railway variables --json 2>/dev/null | python3 -c "
import json, sys
try:
    vars = json.load(sys.stdin)
    with open('$TEMP_ENV', 'w') as f:
        for k, v in vars.items():
            f.write(f'{k}={v}\n')
    sys.exit(0)
except:
    sys.exit(1)
" 2>/dev/null; then
        # Success with --json flag
        print_success "Fetched environment variables from Railway (JSON format)"
    else
        print_warning "Could not fetch variables automatically"
        print_status "You can manually fetch variables with: make railway-env"
        rm -f "$TEMP_ENV"
    fi
    
    # Merge with existing .env if it exists
    if [ -f "$TEMP_ENV" ] && [ -s "$TEMP_ENV" ]; then
        if [ -f ".env" ]; then
            print_status "Merging Railway variables with existing .env file..."
            
            # Use Python to merge properly
            python3 << EOF 2>/dev/null || print_warning "Python merge failed, using Railway vars only"
import os

railway_vars = {}
existing_vars = {}

# Read Railway variables
if os.path.exists('$TEMP_ENV'):
    with open('$TEMP_ENV', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, _, value = line.partition('=')
                railway_vars[key] = value

# Read existing .env
if os.path.exists('.env'):
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, _, value = line.partition('=')
                if key not in railway_vars:
                    existing_vars[key] = value

# Write merged .env
with open('.env', 'w') as f:
    f.write('# Environment variables from Railway\n')
    f.write('# Merged with local variables\n')
    f.write('# Run this script again to update from Railway\n\n')
    
    # Write Railway vars first (they take precedence)
    for key, value in sorted(railway_vars.items()):
        f.write(f'{key}={value}\n')
    
    # Then write local-only vars
    for key, value in sorted(existing_vars.items()):
        f.write(f'{key}={value}\n')

print("Merged", len(railway_vars), "Railway variables with", len(existing_vars), "local variables")
EOF
            
        else
            # No existing .env, just use Railway vars
            mv "$TEMP_ENV" .env
            print_success "Created .env file from Railway variables"
        fi
        
        # Clean up temp file
        rm -f "$TEMP_ENV"
        
        # Show what variables were fetched
        VAR_COUNT=$(grep -v '^#' .env 2>/dev/null | grep -v '^$' | grep '=' | wc -l | tr -d ' ')
        print_success "Environment file ready with $VAR_COUNT variables"
        
        # Show a sample of variables (without values)
        print_status "Sample variables (keys only):"
        grep -v '^#' .env 2>/dev/null | grep -v '^$' | grep '=' | cut -d'=' -f1 | head -10 | sed 's/^/   - /' || echo "   (none)"
        
    elif [ ! -f ".env" ]; then
        # No Railway vars and no .env, create from template
        print_warning "No environment variables found in Railway and no .env file"
        if [ -f "env.example" ]; then
            print_status "Creating .env file from template..."
            cp env.example .env
            print_success "Created .env file from template"
            print_warning "You may need to customize the .env file"
        fi
    fi
else
    print_warning "Not linked to Railway project, using template .env file"
    if [ ! -f ".env" ] && [ -f "env.example" ]; then
        print_status "Creating .env file from template..."
        cp env.example .env
        print_success "Created .env file from template"
    fi
fi

# ============================================================================
# Step 7: Build and Start Docker Containers
# ============================================================================
print_header "Step 7: Building and Starting Docker Containers"

print_status "Building Docker images (this may take a few minutes the first time)..."
$DOCKER_COMPOSE build

print_status "Starting all services..."
$DOCKER_COMPOSE up -d

# Wait a bit for services to start
print_status "Waiting for services to initialize..."
sleep 5

# Check service status
print_status "Checking service status..."
$DOCKER_COMPOSE ps

# ============================================================================
# Step 8: Verify Services
# ============================================================================
print_header "Step 8: Verifying Services"

# Wait for backend to be ready
print_status "Waiting for backend to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f -s http://localhost:8002/api/health/ > /dev/null 2>&1 || \
       curl -f -s http://localhost:8002/api/ > /dev/null 2>&1; then
        print_success "Backend is ready!"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
        echo -n "."
        sleep 2
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    print_warning "Backend may still be starting. Check logs with: $DOCKER_COMPOSE logs backend"
else
    echo ""
fi

# ============================================================================
# Summary
# ============================================================================
print_header "✅ Setup Complete!"

echo ""
print_success "🎉 Your application is now running locally!"
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
echo "   View backend:     $DOCKER_COMPOSE logs -f backend"
echo "   View frontend:    $DOCKER_COMPOSE logs -f frontend"
echo "   Stop services:    $DOCKER_COMPOSE down"
echo "   Restart services: $DOCKER_COMPOSE restart"
echo "   Check status:     $DOCKER_COMPOSE ps"
echo ""
echo "   Or use Make commands:"
echo "   make logs         - View all logs"
echo "   make logs-backend - View backend logs"
echo "   make logs-frontend - View frontend logs"
echo "   make down         - Stop services"
echo "   make restart      - Restart services"
echo "   make status       - Show service status"
echo "   make migrate      - Run database migrations"
echo "   make seed         - Seed sample data"
echo ""
print_warning "Note: It may take a minute or two for all services to fully start."
print_status "Monitor the logs with: $DOCKER_COMPOSE logs -f"
echo ""
echo "🔧 Colima Management:"
echo "   colima status   - Check Colima status"
echo "   colima stop     - Stop Colima"
echo "   colima start    - Start Colima"
echo "   colima restart  - Restart Colima"
echo ""
echo "💡 To customize Colima resources (CPU/Memory), stop it first:"
echo "   colima stop"
echo "   colima start --cpu 4 --memory 8  # Example: 4 CPUs, 8GB RAM"

