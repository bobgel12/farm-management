# Docker Local Setup Guide

This guide will help you set up and run the Chicken House Management System locally using Docker.

## Prerequisites

### 1. Install Colima (Docker Runtime for macOS)

Since you're on macOS, we use Colima - a lightweight Docker runtime alternative:

1. **Install Homebrew** (if not already installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install Colima and Docker CLI:**
   ```bash
   brew install colima docker docker-compose
   ```

3. **Start Colima:**
   ```bash
   colima start
   ```

4. **Verify Installation:**
   ```bash
   colima status
   docker --version
   docker compose version
   ```

**Why Colima instead of Docker Desktop?**
- Lighter weight (no GUI application)
- Lower resource usage
- Faster startup
- CLI-only interface
- Full Docker compatibility

## Quick Start

Once Docker is installed, follow these steps:

### Step 1: Create Environment File

The `.env` file has already been created from the template. You can customize it if needed, but the default values will work for local development.

### Step 2: Start All Services

```bash
# Build and start all containers
docker compose up -d

# Or using the Makefile (recommended)
make dev
```

This will start:
- **PostgreSQL Database** on port `5433`
- **Redis** on port `6380`
- **Django Backend** on port `8002`
- **React Frontend** on port `3002`

### Step 3: Wait for Services to Initialize

The first time you start, Docker will:
- Build the Docker images
- Run database migrations
- Create default admin user
- Set up default program and farm

This may take a few minutes. You can monitor the logs:

```bash
# View all logs
docker compose logs -f

# Or using Makefile
make logs

# View only backend logs
make logs-backend
```

### Step 4: Access the Application

Once all services are running, you can access:

- **Frontend**: http://localhost:3002
- **Backend API**: http://localhost:8002/api
- **Admin Panel**: http://localhost:8002/admin
  - Username: `admin`
  - Password: `admin123`

## Useful Commands

### Using Docker Compose

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# View logs
docker compose logs -f

# View logs for specific service
docker compose logs -f backend
docker compose logs -f frontend

# Restart services
docker compose restart

# Rebuild and start
docker compose up -d --build

# Check service status
docker compose ps
```

### Using Makefile (Recommended)

```bash
# Development commands
make dev          # Start development environment
make logs         # Show logs
make logs-backend # Show backend logs only
make logs-frontend # Show frontend logs only
make restart      # Restart services
make down         # Stop services
make status       # Show service status

# Database commands
make migrate      # Run migrations
make seed         # Seed with sample data

# Other commands
make shell-backend # Open backend shell
make shell-db      # Open database shell
make clean         # Clean up containers and volumes
make help          # Show all available commands
```

## Troubleshooting

### Port Already in Use

If you get port conflicts:

```bash
# Check what's using the ports
lsof -i :8002
lsof -i :3002
lsof -i :5433

# Stop services and clean up
docker compose down

# Or change ports in docker-compose.yml if needed
```

### Services Won't Start

1. **Check Docker is running:**
   ```bash
   docker ps
   ```

2. **Check logs for errors:**
   ```bash
   docker compose logs backend
   docker compose logs frontend
   ```

3. **Rebuild containers:**
   ```bash
   docker compose down
   docker compose up -d --build
   ```

### Database Connection Issues

The backend will automatically wait for the database to be ready. If you see connection errors:

```bash
# Check database container
docker compose ps db

# Check database logs
docker compose logs db

# Restart database
docker compose restart db
```

### Frontend Build Issues

If the frontend fails to build:

```bash
# Rebuild frontend container
docker compose build frontend
docker compose up -d frontend

# Check frontend logs
docker compose logs frontend
```

### Clean Slate Reset

If you want to start completely fresh:

```bash
# Stop and remove all containers and volumes
docker compose down -v

# Remove Docker images (optional)
docker compose down --rmi all

# Start fresh
docker compose up -d
```

## Environment Configuration

The `.env` file contains configuration for:
- Database connection
- Django secret key
- Admin credentials
- Email settings (optional for local dev)
- Rotem scraper credentials (optional)

For local development, the default values will work. You only need to customize:
- Email settings (if you want to test email functionality)
- Rotem credentials (if you want to use Rotem integration)

## Next Steps

1. **Test the API:**
   ```bash
   curl http://localhost:8002/api/farms/
   ```

2. **Access the Admin Panel:**
   Visit http://localhost:8002/admin and login with admin/admin123

3. **View the Frontend:**
   Visit http://localhost:3002

4. **Seed Sample Data (optional):**
   ```bash
   make seed
   # or
   docker compose exec backend python manage.py seed_data --clear
   ```

## Development Tips

- **Hot Reloading**: Both backend and frontend support hot reloading when you edit files
- **Database Access**: Use `make shell-db` to access PostgreSQL directly
- **Backend Shell**: Use `make shell-backend` to run Django management commands
- **Logs**: Always check logs first when troubleshooting: `make logs`

## Production vs Development

The `docker-compose.yml` file is configured for **development** with:
- Volume mounts for live code reloading
- Debug mode enabled
- Development-friendly settings

For production, use `docker-compose.prod.yml` instead.

