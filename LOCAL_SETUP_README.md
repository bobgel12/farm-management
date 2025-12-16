# Local Development Setup with Railway

This guide explains how to set up and run the Chicken House Management System locally using Docker with Railway environment variables.

## Quick Start

Run the automated setup script:

```bash
./setup-local-railway.sh
```

This script will:
1. ✅ Check and install Colima (lightweight Docker runtime) and Docker CLI (if needed)
2. ✅ Check and install Node.js (if needed)
3. ✅ Check and install Railway CLI (if needed)
4. ✅ Login to Railway (if needed)
5. ✅ Link to your Railway project (if needed)
6. ✅ Fetch environment variables from Railway
7. ✅ Build and start Docker containers
8. ✅ Verify services are running

## Manual Setup

If you prefer to set up manually, follow these steps:

### 1. Install Colima and Docker CLI

**Using Homebrew (recommended on macOS):**
```bash
brew install colima docker docker-compose
colima start
```

**About Colima:**
- Colima is a lightweight, CLI-based Docker runtime alternative to Docker Desktop
- No GUI required - runs entirely from the command line
- Lower resource usage than Docker Desktop
- Full Docker compatibility

**Verify installation:**
```bash
colima status
docker --version
docker compose version
```

### 2. Install Node.js

**Using Homebrew (recommended on macOS):**
```bash
brew install node
```

**Or download from:** https://nodejs.org/

Verify installation:
```bash
node --version
npm --version
```

### 3. Install Railway CLI

```bash
npm install -g @railway/cli
```

Verify installation:
```bash
railway --version
```

### 4. Login to Railway

```bash
railway login
```

### 5. Link to Railway Project

```bash
railway link
```

Select your Railway project when prompted.

### 6. Fetch Environment Variables

**Option A: Using the Makefile (recommended):**
```bash
make railway-env
```

**Option B: Using the setup script:**
```bash
./setup-local-railway.sh
```

This will create a `.env` file with all your Railway environment variables.

### 7. Start Docker Containers

**Option A: Using Docker Compose:**
```bash
docker compose up -d
```

**Option B: Using Make:**
```bash
make dev
```

**Option C: Using the setup script:**
```bash
./setup-local-railway.sh
```

## Access the Application

Once services are running:

- **Frontend**: http://localhost:3002
- **Backend API**: http://localhost:8002/api
- **Admin Panel**: http://localhost:8002/admin
  - Username: `admin`
  - Password: `admin123`

## Common Commands

### Using Docker Compose

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# View logs
docker compose logs -f

# View backend logs only
docker compose logs -f backend

# View frontend logs only
docker compose logs -f frontend

# Restart services
docker compose restart

# Check status
docker compose ps

# Rebuild and restart
docker compose up -d --build
```

### Using Makefile

```bash
# Start development environment
make dev

# View logs
make logs
make logs-backend
make logs-frontend

# Stop services
make down

# Restart services
make restart

# Check status
make status

# Database operations
make migrate    # Run migrations
make seed       # Seed sample data

# Fetch Railway env vars
make railway-env

# Open shells
make shell-backend  # Backend shell
make shell-db       # Database shell
```

## Troubleshooting

### Docker/Colima Not Running

**Error:** `Cannot connect to the Docker daemon`

**Solution:**
```bash
# Check Colima status
colima status

# Start Colima if not running
colima start

# Verify Docker is working
docker info
```

### Railway CLI Not Found

**Error:** `command not found: railway`

**Solution:**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Verify installation
railway --version
```

### Not Logged in to Railway

**Error:** `not logged in`

**Solution:**
```bash
railway login
```

### Not Linked to Railway Project

**Error:** `not linked to a project`

**Solution:**
```bash
railway link
```

### Port Already in Use

**Error:** `port is already allocated`

**Solution:**
```bash
# Check what's using the port
lsof -i :8002
lsof -i :3002
lsof -i :5433

# Stop conflicting services or change ports in docker-compose.yml
```

### Services Won't Start

**Solution:**
```bash
# Check logs
docker compose logs backend
docker compose logs frontend

# Rebuild containers
docker compose down
docker compose up -d --build
```

### Environment Variables Not Loading

**Solution:**
```bash
# Re-fetch from Railway
make railway-env

# Or manually
railway variables --kv > .env
```

### Database Connection Issues

**Solution:**
```bash
# Check database container
docker compose ps db

# Check database logs
docker compose logs db

# Restart database
docker compose restart db
```

## Updating Environment Variables

To update environment variables from Railway:

```bash
make railway-env
```

This will merge Railway variables with your local `.env` file (Railway vars take precedence).

## Clean Slate Reset

To start completely fresh:

```bash
# Stop and remove all containers and volumes
docker compose down -v

# Remove Docker images (optional)
docker compose down --rmi all

# Run setup again
./setup-local-railway.sh
```

## Development Tips

- **Hot Reloading**: Both backend and frontend support hot reloading when you edit files
- **Database Access**: Use `make shell-db` to access PostgreSQL directly
- **Backend Shell**: Use `make shell-backend` to run Django management commands
- **Logs**: Always check logs first when troubleshooting: `make logs`
- **Environment**: Variables are loaded from `.env` file, which is merged from Railway

## Colima vs Docker Desktop

This setup uses **Colima** instead of Docker Desktop because:
- ✅ Lighter weight (no GUI application)
- ✅ Lower resource usage
- ✅ Faster startup time
- ✅ CLI-only (better for automation)
- ✅ Full Docker compatibility

To manage Colima:
```bash
colima start    # Start Colima
colima stop     # Stop Colima
colima restart  # Restart Colima
colima status   # Check status
colima delete   # Remove Colima VM
```

## Architecture

The application runs the following services:

- **PostgreSQL Database** (port 5433)
  - Database: `chicken_management`
  - User: `postgres`
  - Password: `password` (local only)

- **Redis** (port 6380)
  - Used for Celery task queue

- **Django Backend** (port 8002)
  - REST API
  - Admin panel
  - Celery workers

- **React Frontend** (port 3002)
  - Web interface
  - Material-UI components

## Next Steps

1. **Seed Sample Data** (optional):
   ```bash
   make seed
   ```

2. **Test the API**:
   ```bash
   curl http://localhost:8002/api/farms/
   ```

3. **Access Admin Panel**:
   Visit http://localhost:8002/admin

4. **Start Development**:
   Edit files in `backend/` or `frontend/` - changes will hot reload automatically!

## Support

For issues or questions:
- Check logs: `make logs`
- Review documentation: `README.md`
- Check Railway dashboard for environment variables

