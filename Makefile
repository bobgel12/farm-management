# Chicken House Management System
# Makefile for local development and deployment

.PHONY: help install dev build up down restart logs clean test seed email-test deploy-railway

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
	@echo "📱 Frontend: http://localhost:3000"
	@echo "🔧 Backend: http://localhost:8000"
	@echo "📊 Admin: http://localhost:8000/admin (admin/admin123)"

# Docker Commands
build: ## Build Docker images
	@echo "🔨 Building Docker images..."
	docker-compose build

up: ## Start all services
	@echo "🚀 Starting all services..."
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

# Database Commands
migrate: ## Run database migrations
	@echo "🗄️ Running database migrations..."
	docker-compose exec backend python manage.py migrate

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
	@if [ ! -f .env ]; then \
		echo "❌ .env file not found. Please create one first."; \
		exit 1; \
	fi
	@echo "📋 Make sure to set these environment variables in Railway:"
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
	@echo "📱 Frontend: http://localhost:3000"
	@echo "🔧 Backend: http://localhost:8000"
	@echo "📊 Admin: http://localhost:8000/admin (admin/admin123)"

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

help-rotem: ## Show Rotem scraper help
	@echo "Rotem Scraper Commands:"
	@echo "======================"
	@echo "  make rotem-setup  - Setup Rotem credentials"
	@echo "  make rotem-test   - Test Rotem scraper"
	@echo "  make rotem-logs   - Show Rotem scraper logs"

help-deploy: ## Show deployment help
	@echo "Deployment Commands:"
	@echo "==================="
	@echo "  make deploy-railway - Deploy to Railway"
	@echo "  make prod-build    - Build production images"
	@echo "  make prod-up       - Start production environment"
