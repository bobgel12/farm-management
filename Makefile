# Chicken House Management System
# Makefile for local development and deployment

.PHONY: help install dev build up down restart logs clean test seed email-test deploy-railway railway-env railway-up railway-dev railway-link logs-email

DOCKER_COMPOSE := $(shell if command -v docker-compose >/dev/null 2>&1; then echo docker-compose; else echo "docker compose"; fi)

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
	$(DOCKER_COMPOSE) up -d
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
	$(DOCKER_COMPOSE) build

up: ## Start all services
	@echo "🚀 Starting all services..."
	@if [ ! -f .env ]; then \
		echo "⚠️  .env file not found. Using default environment variables."; \
		echo "   Run 'make railway-env' to fetch from Railway, or create .env manually."; \
	fi
	$(DOCKER_COMPOSE) up -d

down: ## Stop all services
	@echo "🛑 Stopping all services..."
	$(DOCKER_COMPOSE) down

restart: ## Restart all services
	@echo "🔄 Restarting all services..."
	$(DOCKER_COMPOSE) restart

logs: ## Show logs for all services
	@echo "📋 Showing logs..."
	$(DOCKER_COMPOSE) logs -f

logs-backend: ## Show backend logs only
	@echo "📋 Showing backend logs..."
	$(DOCKER_COMPOSE) logs -f backend

logs-frontend: ## Show frontend logs only
	@echo "📋 Showing frontend logs..."
	$(DOCKER_COMPOSE) logs -f frontend

logs-email: ## Show email-related logs only
	@echo "📧 Showing email logs..."
	$(DOCKER_COMPOSE) logs -f backend | grep -i -E "(email|smtp|mail|send.*email|test.*email|email.*test|email.*service|email.*error|email.*fail)"

# Database Commands
migrate: ## Run database migrations
	@echo "🗄️ Running database migrations..."
	$(DOCKER_COMPOSE) exec backend python manage.py migrate
	@echo "✅ Migrations applied successfully!"

migrate-all: ## Run migrations for all apps including new features
	@echo "🗄️ Running all database migrations..."
	@echo "   - Organizations (multi-tenancy)"
	@echo "   - Farms (flock management)"
	@echo "   - Reporting"
	@echo "   - Analytics"
	$(DOCKER_COMPOSE) exec backend python manage.py migrate organizations farms reporting analytics
	@echo "✅ All migrations applied successfully!"

migrate-create: ## Create new migration
	@echo "📝 Creating new migration..."
	@read -p "Enter migration name: " name; \
	$(DOCKER_COMPOSE) exec backend python manage.py makemigrations $$name

# Data Management
seed: ## Seed database with sample data
	@echo "🌱 Seeding database with sample data..."
	$(DOCKER_COMPOSE) exec backend python manage.py seed_data --clear
	@echo "✅ Database seeded!"

seed-variety: ## Seed database with variety of data
	@echo "🌱 Seeding database with variety of data..."
	$(DOCKER_COMPOSE) exec backend python manage.py seed_data --clear --variety
	@echo "✅ Database seeded with variety!"

seed-custom: ## Seed database with custom parameters
	@echo "🌱 Seeding database with custom parameters..."
	@read -p "Number of farms (default 3): " farms; \
	read -p "Houses per farm (default 5): " houses; \
	read -p "Workers per farm (default 3): " workers; \
	$(DOCKER_COMPOSE) exec backend python manage.py seed_data --clear --farms $${farms:-3} --houses-per-farm $${houses:-5} --workers-per-farm $${workers:-3}
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
	$(DOCKER_COMPOSE) exec backend python manage.py send_daily_tasks

# Rotem Scraper Commands
rotem-test: ## Test Rotem scraper
	@echo "🔍 Testing Rotem scraper..."
	$(DOCKER_COMPOSE) exec backend python manage.py test_scraper

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
	$(DOCKER_COMPOSE) logs -f backend | grep -i rotem

rotem-seed: ## Seed Rotem test data for Playwright tests
	@echo "🌱 Seeding Rotem test data..."
	$(DOCKER_COMPOSE) exec backend python manage.py seed_rotem_data --days=7
	@echo "✅ Rotem test data seeded!"

rotem-seed-clear: ## Clear and re-seed Rotem test data
	@echo "🧹 Clearing and re-seeding Rotem test data..."
	$(DOCKER_COMPOSE) exec backend python manage.py seed_rotem_data --clear --days=7
	@echo "✅ Rotem test data re-seeded!"

issues-seed: ## Seed issues and mortality test data
	@echo "🌱 Seeding issues and mortality test data..."
	$(DOCKER_COMPOSE) exec backend python manage.py seed_issues_data --days=30
	@echo "✅ Issues and mortality test data seeded!"

issues-seed-clear: ## Clear and re-seed issues and mortality test data
	@echo "🧹 Clearing and re-seeding issues and mortality test data..."
	$(DOCKER_COMPOSE) exec backend python manage.py seed_issues_data --clear --days=30
	@echo "✅ Issues and mortality test data re-seeded!"

# Testing Commands
test: ## Run tests
	@echo "🧪 Running tests..."
	$(DOCKER_COMPOSE) exec backend python manage.py test

test-email-config: ## Test email configuration
	@echo "📧 Testing email configuration..."
	python test_railway_email.py

# Playwright E2E Tests
test-e2e: ## Run Playwright E2E tests (requires frontend running)
	@echo "🎭 Running Playwright E2E tests..."
	cd frontend && npx playwright test

test-e2e-ui: ## Run Playwright tests with UI
	@echo "🎭 Running Playwright tests with UI..."
	cd frontend && npx playwright test --ui

test-e2e-headed: ## Run Playwright tests in headed mode
	@echo "🎭 Running Playwright tests in headed mode..."
	cd frontend && npx playwright test --headed

test-e2e-rotem: ## Run Rotem integration E2E tests only
	@echo "🎭 Running Rotem integration tests..."
	cd frontend && npx playwright test rotem-integration.spec.ts

test-e2e-ml: ## Run ML analytics E2E tests only
	@echo "🎭 Running ML analytics tests..."
	cd frontend && npx playwright test ml-analytics.spec.ts

test-e2e-farm: ## Run Farm integration E2E tests only
	@echo "🎭 Running Farm integration tests..."
	cd frontend && npx playwright test farm-integration.spec.ts

test-e2e-mortality: ## Run Mortality tracking E2E tests only
	@echo "🎭 Running Mortality tracking tests..."
	cd frontend && npx playwright test mortality.spec.ts

test-e2e-issues: ## Run Issue reporting E2E tests only
	@echo "🎭 Running Issue reporting tests..."
	cd frontend && npx playwright test issues.spec.ts

test-e2e-setup: ## Setup Playwright and seed test data
	@echo "🔧 Setting up Playwright tests..."
	cd frontend && npm install @playwright/test playwright
	cd frontend && npx playwright install chromium
	$(MAKE) rotem-seed
	@echo "✅ Playwright setup complete!"

# Cleanup Commands
clean: ## Clean up Docker containers and volumes
	@echo "🧹 Cleaning up..."
	$(DOCKER_COMPOSE) down -v
	docker system prune -f
	@echo "✅ Cleanup complete!"

clean-all: ## Clean up everything including images
	@echo "🧹 Deep cleaning..."
	$(DOCKER_COMPOSE) down -v --rmi all
	docker system prune -af
	@echo "✅ Deep cleanup complete!"

# Production Commands
prod-build: ## Build production images
	@echo "🏗️ Building production images..."
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml build

prod-up: ## Start production environment
	@echo "🚀 Starting production environment..."
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml up -d

prod-down: ## Stop production environment
	@echo "🛑 Stopping production environment..."
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml down

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
	$(DOCKER_COMPOSE) exec backend bash

shell-db: ## Open database shell
	@echo "🐚 Opening database shell..."
	$(DOCKER_COMPOSE) exec db psql -U postgres -d chicken_management

status: ## Show service status
	@echo "📊 Service Status:"
	@echo "=================="
	@$(DOCKER_COMPOSE) ps

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
