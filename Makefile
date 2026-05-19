# Chicken House Management System
# Makefile for local development and deployment

.PHONY: help install dev frontend-prod-docker frontend-prod-host frontend-prod-logs frontend-prod-down local-up local-logs local-down local-reset build up down restart logs clean test seed email-test deploy-railway railway-env railway-up railway-dev railway-link logs-email

DOCKER_COMPOSE := $(shell if command -v docker-compose >/dev/null 2>&1; then echo docker-compose; else echo "docker compose"; fi)
LOCAL_BACKEND_ENV := $(shell if [ -f .env.local-backend ]; then echo .env.local-backend; else echo env.local-backend.example; fi)
FRONTEND_PROD_ENV := $(shell if [ -f .env.frontend-prod ]; then echo .env.frontend-prod; else echo env.frontend-prod.example; fi)
LOCAL_COMPOSE := $(DOCKER_COMPOSE) --env-file $(LOCAL_BACKEND_ENV) -f docker-compose.yml
FRONTEND_PROD_COMPOSE := $(DOCKER_COMPOSE) -p farm-management-frontend-prod --env-file $(FRONTEND_PROD_ENV) -f docker-compose.frontend-prod.yml

# Default target
help: ## Show this help message
	@echo "Chicken House Management System"
	@echo "=============================="
	@echo ""
	@echo "Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development Setup
install: ## Verify Docker and Compose are available
	@command -v docker >/dev/null 2>&1 || (echo "❌ Docker is required. Install Docker Desktop or Colima." && exit 1)
	@$(DOCKER_COMPOSE) version >/dev/null 2>&1 || (echo "❌ Docker Compose is required." && exit 1)
	@echo "✅ Prerequisites OK (Docker + Compose)"

wait-backend: ## Wait until the local backend health check passes
	@echo "⏳ Waiting for backend (http://localhost:8002/api/health/)..."
	@for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30; do \
		curl -sf http://localhost:8002/api/health/ >/dev/null 2>&1 && echo "✅ Backend is ready" && exit 0; \
		sleep 2; \
	done; \
	echo "❌ Backend did not become healthy. Run: make local-logs"; exit 1

dev: local-up ## Alias for the full local stack

frontend-prod-docker: ## Start the local frontend in Docker against the production backend
	@echo "🌐 Starting local frontend against production backend..."
	@echo "   Env: $(FRONTEND_PROD_ENV)"
	$(FRONTEND_PROD_COMPOSE) up -d --build
	@echo "✅ Frontend started!"
	@echo "📱 Frontend: http://localhost:3002"

frontend-prod-host: ## Start the host npm frontend against the production backend
	@echo "🌐 Starting host frontend against production backend..."
	@echo "   Env: $(FRONTEND_PROD_ENV)"
	@set -a; . ./$(FRONTEND_PROD_ENV); set +a; export PORT=$${FRONTEND_HOST_PORT:-3002}; cd frontend && npm start

frontend-prod-logs: ## Show frontend logs for the production-backend mode
	$(FRONTEND_PROD_COMPOSE) logs -f frontend

frontend-prod-down: ## Stop the Dockerized frontend production-backend mode
	$(FRONTEND_PROD_COMPOSE) down

local-up: ## Start the full local stack with production-style backend settings
	@echo "🔧 Starting full local stack..."
	@echo "   Env: $(LOCAL_BACKEND_ENV)"
	$(LOCAL_COMPOSE) up -d --build
	@echo "✅ Full local stack started!"
	@echo "📱 Frontend: http://localhost:3002"
	@echo "🔧 Backend: http://localhost:8002"
	@echo "📊 Admin: http://localhost:8002/admin (admin/admin123)"

local-logs: ## Show logs for the full local stack
	$(LOCAL_COMPOSE) logs -f

local-down: ## Stop the full local stack
	$(LOCAL_COMPOSE) down

local-reset: ## Reset the full local stack and its volumes
	$(LOCAL_COMPOSE) down -v
	$(LOCAL_COMPOSE) up -d --build

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

railway-up: railway-env ## Fetch Railway env vars for deployment workflows
	@echo "ℹ️ Railway env vars were refreshed in .env."
	@echo "ℹ️ Local development now uses explicit local env files; see make local-up or make frontend-prod-docker."

railway-dev: railway-env ## Fetch Railway env vars for deployment workflows
	@echo "ℹ️ Local development now uses explicit local env files; see make local-up or make frontend-prod-docker."

# Docker Commands
build: ## Build Docker images for the full local stack
	@echo "🔨 Building Docker images..."
	$(LOCAL_COMPOSE) build

up: local-up ## Alias for the full local stack

down: local-down ## Alias for stopping the full local stack

restart: ## Restart all services
	@echo "🔄 Restarting all services..."
	$(LOCAL_COMPOSE) restart

logs: ## Show logs for all services
	@echo "📋 Showing logs..."
	$(LOCAL_COMPOSE) logs -f

logs-backend: ## Show backend logs only
	@echo "📋 Showing backend logs..."
	$(LOCAL_COMPOSE) logs -f backend

logs-frontend: ## Show frontend logs only
	@echo "📋 Showing frontend logs..."
	$(LOCAL_COMPOSE) logs -f frontend

logs-email: ## Show email-related logs only
	@echo "📧 Showing email logs..."
	$(LOCAL_COMPOSE) logs -f backend | grep -i -E "(email|smtp|mail|send.*email|test.*email|email.*test|email.*service|email.*error|email.*fail)"

# Database Commands
migrate: ## Run database migrations
	@echo "🗄️ Running database migrations..."
	$(LOCAL_COMPOSE) exec backend python manage.py migrate
	@echo "✅ Migrations applied successfully!"

migrate-all: ## Run migrations for all apps including new features
	@echo "🗄️ Running all database migrations..."
	@echo "   - Organizations (multi-tenancy)"
	@echo "   - Farms (flock management)"
	@echo "   - Reporting"
	@echo "   - Analytics"
	$(LOCAL_COMPOSE) exec backend python manage.py migrate organizations farms reporting analytics
	@echo "✅ All migrations applied successfully!"

migrate-create: ## Create new migration
	@echo "📝 Creating new migration..."
	@read -p "Enter migration name: " name; \
	$(LOCAL_COMPOSE) exec backend python manage.py makemigrations $$name

# Data Management
seed: ## Seed database with sample data
	@echo "🌱 Seeding database with sample data..."
	$(LOCAL_COMPOSE) exec backend python manage.py seed_data --clear
	@echo "✅ Database seeded!"

seed-variety: ## Seed database with variety of data
	@echo "🌱 Seeding database with variety of data..."
	$(LOCAL_COMPOSE) exec backend python manage.py seed_data --clear --variety
	@echo "✅ Database seeded with variety!"

seed-custom: ## Seed database with custom parameters
	@echo "🌱 Seeding database with custom parameters..."
	@read -p "Number of farms (default 3): " farms; \
	read -p "Houses per farm (default 5): " houses; \
	read -p "Workers per farm (default 3): " workers; \
	$(LOCAL_COMPOSE) exec backend python manage.py seed_data --clear --farms $${farms:-3} --houses-per-farm $${houses:-5} --workers-per-farm $${workers:-3}
	@echo "✅ Database seeded with custom data!"

# Email Commands
email-test: ## Send test email
	@echo "📧 Sending test email..."
	@read -p "Enter test email address: " email; \
	curl -X POST 'http://localhost:8002/api/tasks/send-test-email/' \
		-H 'Accept: application/json' \
		-H 'Authorization: Token 7a2656cc6d71b6ebdee0acba4f99f4d77c142511' \
		-H 'Content-Type: application/json' \
		-d "{\"farm_id\":1,\"test_email\":\"$$email\"}"

email-daily: ## Send daily task emails
	@echo "📧 Sending daily task emails..."
	$(LOCAL_COMPOSE) exec backend python manage.py send_daily_tasks

# Rotem Scraper Commands
rotem-test: ## Test Rotem scraper
	@echo "🔍 Testing Rotem scraper..."
	$(LOCAL_COMPOSE) exec backend python manage.py test_scraper

rotem-setup: ## Setup Rotem credentials
	@echo "⚙️ Setting up Rotem credentials..."
	@if [ ! -f .env.local-backend ]; then \
		echo "📋 Creating .env.local-backend file from local template..."; \
		cp env.local-backend.example .env.local-backend; \
		echo "✅ .env.local-backend file created!"; \
		echo "📝 Please edit .env.local-backend and add your Rotem credentials:"; \
		echo "   ROTEM_USERNAME=your-rotem-username"; \
		echo "   ROTEM_PASSWORD=your-rotem-password"; \
	else \
		echo "✅ .env.local-backend file already exists"; \
		echo "📝 Current Rotem settings:"; \
		grep ROTEM .env.local-backend || echo "   No Rotem credentials found in .env.local-backend"; \
	fi

rotem-logs: ## Show Rotem scraper logs
	@echo "📋 Showing Rotem scraper logs..."
	$(LOCAL_COMPOSE) logs -f backend | grep -i rotem

rotem-seed: ## Seed Rotem test data for Playwright tests
	@echo "🌱 Seeding Rotem test data..."
	$(LOCAL_COMPOSE) exec backend python manage.py seed_rotem_data --days=7
	@echo "✅ Rotem test data seeded!"

rotem-seed-clear: ## Clear and re-seed Rotem test data
	@echo "🧹 Clearing and re-seeding Rotem test data..."
	$(LOCAL_COMPOSE) exec backend python manage.py seed_rotem_data --clear --days=7
	@echo "✅ Rotem test data re-seeded!"

issues-seed: ## Seed issues and mortality test data
	@echo "🌱 Seeding issues and mortality test data..."
	$(LOCAL_COMPOSE) exec backend python manage.py seed_issues_data --days=30
	@echo "✅ Issues and mortality test data seeded!"

issues-seed-clear: ## Clear and re-seed issues and mortality test data
	@echo "🧹 Clearing and re-seeding issues and mortality test data..."
	$(LOCAL_COMPOSE) exec backend python manage.py seed_issues_data --clear --days=30
	@echo "✅ Issues and mortality test data re-seeded!"

# Testing Commands
test: ## Run tests
	@echo "🧪 Running tests..."
	$(LOCAL_COMPOSE) exec backend python manage.py test

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
	$(LOCAL_COMPOSE) down -v
	docker system prune -f
	@echo "✅ Cleanup complete!"

clean-all: ## Clean up everything including images
	@echo "🧹 Deep cleaning..."
	$(LOCAL_COMPOSE) down -v --rmi all
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
	$(LOCAL_COMPOSE) exec backend bash

shell-db: ## Open database shell
	@echo "🐚 Opening database shell..."
	$(LOCAL_COMPOSE) exec db psql -U postgres -d chicken_management

status: ## Show service status
	@echo "📊 Service Status:"
	@echo "=================="
	@$(LOCAL_COMPOSE) ps

# Quick Commands
quick-start: install local-up wait-backend migrate seed ## Quick start: verify Docker, start stack, migrate, seed
	@echo "🎉 Quick start complete!"
	@echo "📱 Frontend: http://localhost:3002"
	@echo "🔧 Backend: http://localhost:8002"
	@echo "📊 Admin: http://localhost:8002/admin (admin/admin123)"

quick-reset: local-down clean local-up wait-backend migrate seed ## Quick reset: clean, restart, migrate, and seed
	@echo "🔄 Quick reset complete!"

# Help for specific commands
help-dev: ## Show development help
	@echo "Development Commands:"
	@echo "====================="
	@echo "  make quick-start          - Start stack, migrate, seed (first-time setup)"
	@echo "  make quick-reset          - Reset volumes, restart, migrate, seed"
	@echo "  make local-up             - Start full local stack"
	@echo "  make local-down           - Stop full local stack"
	@echo "  make frontend-prod-docker - Start Docker frontend against production backend"
	@echo "  make frontend-prod-host   - Start host frontend against production backend"
	@echo "  make wait-backend         - Wait for http://localhost:8002/api/health/"
	@echo "  make logs                 - Show all logs"
	@echo "  make logs-backend         - Show backend logs only"
	@echo "  make shell-backend        - Open backend shell"
	@echo "  make migrate              - Run database migrations"
	@echo "  make seed                 - Seed database with sample data"
	@echo ""
	@echo "  Frontend: http://localhost:3002  Backend: http://localhost:8002"

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
