# Chicken House Management System
# Makefile for local development and deployment

.PHONY: help install dev build up down restart logs clean test seed email-test deploy-railway railway-env railway-up railway-dev railway-link logs-email

# Default target
help: ## Show this help message
	@echo "Chicken House Management System"
	@echo "=============================="
	@echo ""
	@echo "Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development Setup
install: ## Install dependencies and setup project
	@echo "🚀 Setting up Chicken House Management System..."
	@chmod +x setup.sh
	@./setup.sh
	@echo "✅ Setup complete!"

dev: ## Start development environment
	@echo "🔧 Starting development environment..."
	docker-compose up -d
	@echo "✅ Development environment started!"
	@echo "📱 Frontend: http://localhost:3002"
	@echo "🔧 Backend: http://localhost:8002"
	@echo "📊 Admin: http://localhost:8002/admin (admin/admin123)"

# Railway Commands
railway-link: ## Link project to Railway (if not already linked)
	@echo "🔗 Linking project to Railway..."
	@if ! railway status > /dev/null 2>&1; then \
		echo "⚠️  Project not linked to Railway. Please run 'railway link' manually."; \
		echo "   Or run 'make railway-env' which will attempt to link automatically."; \
	else \
		echo "✅ Project already linked to Railway"; \
	fi

railway-env: ## Fetch environment variables from Railway and save to .env
	@echo "📥 Fetching environment variables from Railway..."
	@if ! command -v railway > /dev/null 2>&1; then \
		echo "❌ Railway CLI not found. Please install it first:"; \
		echo "   npm install -g @railway/cli"; \
		exit 1; \
	fi
	@if ! railway status > /dev/null 2>&1; then \
		echo "⚠️  Project not linked to Railway. Attempting to link..."; \
		echo "   Please select your Railway project when prompted."; \
		railway link || (echo "❌ Failed to link project. Please run 'railway link' manually." && exit 1); \
	fi
	@echo "📋 Fetching variables from Railway..."
	@echo "# Environment variables fetched from Railway" > .env.railway
	@echo "# Generated automatically - do not edit manually" >> .env.railway
	@echo "# Run 'make railway-env' to update" >> .env.railway
	@echo "" >> .env.railway
	@railway variables --kv >> .env.railway 2>/dev/null || \
		(railway variables --json | python3 -c "import json, sys; \
			vars = json.load(sys.stdin); \
			with open('.env.railway', 'a') as f: \
				[f.write(f'{k}={v}\n') for k, v in vars.items()]" 2>/dev/null) || \
		(echo "❌ Failed to fetch variables. Make sure you're logged in: railway login" && rm -f .env.railway && exit 1)
	@if [ -f .env.railway ] && [ -s .env.railway ]; then \
		if [ -f .env ]; then \
			echo "📝 Merging with existing .env file..."; \
			python3 -c " \
railway_vars = {}; \
existing_vars = {}; \
with open('.env.railway', 'r') as f: \
    for line in f: \
        line = line.strip(); \
        if line and not line.startswith('#') and '=' in line: \
            key, _, value = line.partition('='); \
            railway_vars[key] = value; \
with open('.env', 'r') as f: \
    for line in f: \
        line = line.strip(); \
        if line and not line.startswith('#') and '=' in line: \
            key, _, value = line.partition('='); \
            if key not in railway_vars: \
                existing_vars[key] = value; \
with open('.env.railway', 'w') as f: \
    f.write('# Environment variables fetched from Railway\n'); \
    f.write('# Generated automatically - do not edit manually\n'); \
    f.write('# Run \"make railway-env\" to update\n\n'); \
    for key, value in sorted({**railway_vars, **existing_vars}.items()): \
        f.write(f'{key}={value}\n'); \
" 2>/dev/null || echo "⚠️  Python merge failed, using Railway vars only"; \
		fi; \
		mv .env.railway .env || exit 1; \
		echo "✅ Environment variables saved to .env"; \
		echo "📋 Variables fetched from Railway:"; \
		(grep -v '^#' .env 2>/dev/null | grep -v '^$$' | grep '=' | cut -d'=' -f1 | sed 's/^/   - /' | head -20 || echo "   (no variables found)"); \
		echo ""; \
	else \
		echo "❌ Failed to create .env file or no variables found"; \
		rm -f .env.railway; \
		exit 1; \
	fi

railway-up: railway-env up ## Fetch Railway env vars and start all services
	@echo "✅ Services started with Railway environment variables!"

railway-dev: railway-env dev ## Fetch Railway env vars and start development environment
	@echo "✅ Development environment started with Railway environment variables!"

# Docker Commands
build: ## Build Docker images
	@echo "🔨 Building Docker images..."
	docker-compose build

up: ## Start all services
	@echo "🚀 Starting all services..."
	@if [ ! -f .env ]; then \
		echo "⚠️  .env file not found. Using default environment variables."; \
		echo "   Run 'make railway-env' to fetch from Railway, or create .env manually."; \
	fi
	docker-compose up -d

down: ## Stop all services
	@echo "🛑 Stopping all services..."
	docker-compose down

restart: ## Restart all services
	@echo "🔄 Restarting all services..."
	docker-compose restart

logs: ## Show logs for all services
	@echo "📋 Showing logs..."
	docker-compose logs -f

logs-backend: ## Show backend logs only
	@echo "📋 Showing backend logs..."
	docker-compose logs -f backend

logs-frontend: ## Show frontend logs only
	@echo "📋 Showing frontend logs..."
	docker-compose logs -f frontend

logs-email: ## Show email-related logs only
	@echo "📧 Showing email logs..."
	docker-compose logs -f backend | grep -i -E "(email|smtp|mail|send.*email|test.*email|email.*test|email.*service|email.*error|email.*fail)"

# Database Commands
migrate: ## Run database migrations
	@echo "🗄️ Running database migrations..."
	docker-compose exec backend python manage.py migrate
	@echo "✅ Migrations applied successfully!"

migrate-all: ## Run migrations for all apps including new features
	@echo "🗄️ Running all database migrations..."
	@echo "   - Organizations (multi-tenancy)"
	@echo "   - Farms (flock management)"
	@echo "   - Reporting"
	@echo "   - Analytics"
	docker-compose exec backend python manage.py migrate organizations farms reporting analytics
	@echo "✅ All migrations applied successfully!"

migrate-create: ## Create new migration
	@echo "📝 Creating new migration..."
	@read -p "Enter migration name: " name; \
	docker-compose exec backend python manage.py makemigrations $$name

# Data Management
seed: ## Seed database with sample data
	@echo "🌱 Seeding database with sample data..."
	docker-compose exec backend python manage.py seed_data --clear
	@echo "✅ Database seeded!"

seed-variety: ## Seed database with variety of data
	@echo "🌱 Seeding database with variety of data..."
	docker-compose exec backend python manage.py seed_data --clear --variety
	@echo "✅ Database seeded with variety!"

seed-custom: ## Seed database with custom parameters
	@echo "🌱 Seeding database with custom parameters..."
	@read -p "Number of farms (default 3): " farms; \
	read -p "Houses per farm (default 5): " houses; \
	read -p "Workers per farm (default 3): " workers; \
	docker-compose exec backend python manage.py seed_data --clear --farms $${farms:-3} --houses-per-farm $${houses:-5} --workers-per-farm $${workers:-3}
	@echo "✅ Database seeded with custom data!"

# Email Commands
email-test: ## Send test email
	@echo "📧 Sending test email..."
	@read -p "Enter test email address: " email; \
	curl -X POST 'http://localhost:8000/api/tasks/send-test-email/' \
		-H 'Accept: application/json' \
		-H 'Authorization: Token 7a2656cc6d71b6ebdee0acba4f99f4d77c142511' \
		-H 'Content-Type: application/json' \
		-d "{\"farm_id\":1,\"test_email\":\"$$email\"}"

email-daily: ## Send daily task emails
	@echo "📧 Sending daily task emails..."
	docker-compose exec backend python manage.py send_daily_tasks

# Rotem Scraper Commands
rotem-test: ## Test Rotem scraper
	@echo "🔍 Testing Rotem scraper..."
	docker-compose exec backend python manage.py test_scraper

rotem-setup: ## Setup Rotem credentials
	@echo "⚙️ Setting up Rotem credentials..."
	@if [ ! -f .env ]; then \
		echo "📋 Creating .env file from template..."; \
		cp env.example .env; \
		echo "✅ .env file created!"; \
		echo "📝 Please edit .env file and add your Rotem credentials:"; \
		echo "   ROTEM_USERNAME=your-rotem-username"; \
		echo "   ROTEM_PASSWORD=your-rotem-password"; \
	else \
		echo "✅ .env file already exists"; \
		echo "📝 Current Rotem settings:"; \
		grep ROTEM .env || echo "   No Rotem credentials found in .env"; \
	fi

rotem-logs: ## Show Rotem scraper logs
	@echo "📋 Showing Rotem scraper logs..."
	docker-compose logs -f backend | grep -i rotem

# Testing Commands
test: ## Run tests
	@echo "🧪 Running tests..."
	docker-compose exec backend python manage.py test

test-email-config: ## Test email configuration
	@echo "📧 Testing email configuration..."
	python test_railway_email.py

# Cleanup Commands
clean: ## Clean up Docker containers and volumes
	@echo "🧹 Cleaning up..."
	docker-compose down -v
	docker system prune -f
	@echo "✅ Cleanup complete!"

clean-all: ## Clean up everything including images
	@echo "🧹 Deep cleaning..."
	docker-compose down -v --rmi all
	docker system prune -af
	@echo "✅ Deep cleanup complete!"

# Production Commands
prod-build: ## Build production images
	@echo "🏗️ Building production images..."
	docker-compose -f docker-compose.prod.yml build

prod-up: ## Start production environment
	@echo "🚀 Starting production environment..."
	docker-compose -f docker-compose.prod.yml up -d

prod-down: ## Stop production environment
	@echo "🛑 Stopping production environment..."
	docker-compose -f docker-compose.prod.yml down

# Railway Deployment
deploy-railway: ## Deploy to Railway
	@echo "🚀 Deploying to Railway..."
	@if ! command -v railway > /dev/null 2>&1; then \
		echo "❌ Railway CLI not found. Please install it first:"; \
		echo "   npm install -g @railway/cli"; \
		exit 1; \
	fi
	@if ! railway status > /dev/null 2>&1; then \
		echo "⚠️  Project not linked to Railway. Linking now..."; \
		railway link || (echo "❌ Failed to link project." && exit 1); \
	fi
	@echo "📋 Make sure these environment variables are set in Railway:"
	@echo "   - EMAIL_HOST_USER=your-email@gmail.com"
	@echo "   - EMAIL_HOST_PASSWORD=your-app-password"
	@echo "   - SECRET_KEY=your-secret-key"
	@echo "   - ADMIN_PASSWORD=your-admin-password"
	@echo ""
	@read -p "Press Enter to continue with Railway deployment..."
	railway up

# Utility Commands
shell-backend: ## Open backend shell
	@echo "🐚 Opening backend shell..."
	docker-compose exec backend bash

shell-db: ## Open database shell
	@echo "🐚 Opening database shell..."
	docker-compose exec db psql -U postgres -d chicken_management

status: ## Show service status
	@echo "📊 Service Status:"
	@echo "=================="
	@docker-compose ps

# Quick Commands
quick-start: install up migrate seed ## Quick start: install, start, migrate, and seed
	@echo "🎉 Quick start complete!"
	@echo "📱 Frontend: http://localhost:3002"
	@echo "🔧 Backend: http://localhost:8002"
	@echo "📊 Admin: http://localhost:8002/admin (admin/admin123)"

quick-reset: down clean up migrate seed ## Quick reset: clean, restart, and seed
	@echo "🔄 Quick reset complete!"

# Help for specific commands
help-dev: ## Show development help
	@echo "Development Commands:"
	@echo "====================="
	@echo "  make dev          - Start development environment"
	@echo "  make logs         - Show all logs"
	@echo "  make logs-backend - Show backend logs only"
	@echo "  make shell-backend - Open backend shell"
	@echo "  make migrate      - Run database migrations"
	@echo "  make seed         - Seed database with sample data"

help-email: ## Show email help
	@echo "Email Commands:"
	@echo "=============="
	@echo "  make email-test   - Send test email"
	@echo "  make email-daily  - Send daily task emails"
	@echo "  make test-email-config - Test email configuration"
	@echo "  make logs-email   - Monitor email-related logs"

help-rotem: ## Show Rotem scraper help
	@echo "Rotem Scraper Commands:"
	@echo "======================"
	@echo "  make rotem-setup  - Setup Rotem credentials"
	@echo "  make rotem-test   - Test Rotem scraper"
	@echo "  make rotem-logs   - Show Rotem scraper logs"

help-railway: ## Show Railway help
	@echo "Railway Commands:"
	@echo "================"
	@echo "  make railway-link  - Link project to Railway"
	@echo "  make railway-env   - Fetch env vars from Railway and save to .env"
	@echo "  make railway-up    - Fetch Railway env vars and start all services"
	@echo "  make railway-dev   - Fetch Railway env vars and start dev environment"
	@echo "  make deploy-railway - Deploy to Railway"

help-deploy: ## Show deployment help
	@echo "Deployment Commands:"
	@echo "==================="
	@echo "  make deploy-railway - Deploy to Railway"
	@echo "  make prod-build    - Build production images"
	@echo "  make prod-up       - Start production environment"
