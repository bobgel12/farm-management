# Troubleshooting Guide

This guide covers common issues encountered when setting up and running the Chicken House Management System.

## 🐳 Docker Issues

### Port Already in Use
**Error**: `Bind for 0.0.0.0:5432 failed: port is already allocated`

**Solution**:
```bash
# Check what's using the port
lsof -i :5432

# Kill the process (replace PID with actual process ID)
kill <PID>

# Or restart Colima (macOS)
colima restart
```

### Docker Not Running (macOS)
**Error**: `Cannot connect to the Docker daemon`

**Solution**:
```bash
# Start Colima
colima start

# Check status
colima status
```

## 🔧 Backend Issues

### CSRF Token Issues
**Error**: `CSRF Failed: CSRF token missing` or `CSRF Failed: Origin checking failed`

**Solution**: The application now uses token-based authentication which bypasses CSRF requirements. The setup script automatically:
- Configures `CSRF_TRUSTED_ORIGINS` to include `http://localhost:3000`
- Sets up token authentication with `rest_framework.authtoken`
- Uses `@csrf_exempt` decorator on login endpoint
- Stores authentication tokens in localStorage for API requests

The Django settings include:
```python
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

### Database Table Missing
**Error**: `OperationalError: no such table: farms_farm`

**Solution**: Run migrations:
```bash
# Create migrations directories
docker-compose exec backend mkdir -p farms/migrations houses/migrations tasks/migrations
docker-compose exec backend touch farms/migrations/__init__.py houses/migrations/__init__.py tasks/migrations/__init__.py

# Generate migrations
docker-compose exec backend python manage.py makemigrations

# Apply migrations
docker-compose exec backend python manage.py migrate
```

### Authentication Required
**Error**: `Authentication credentials were not provided`

**Solution**: The API requires authentication. Use the default admin credentials:
- Username: `admin`
- Password: `admin123`

## ⚛️ Frontend Issues

### Module Not Found Errors
**Error**: `Module not found: Error: Can't resolve './App'`

**Solution**: This was caused by missing `.tsx` file extensions in import statements. All imports have been updated to include proper file extensions.

### Material-UI Icon Not Found
**Error**: `export 'Farm' (imported as 'FarmIcon') was not found in '@mui/icons-material'`

**Solution**: The `Farm` icon doesn't exist in Material-UI. It has been replaced with `Agriculture` icon:
```typescript
import { Agriculture as FarmIcon } from '@mui/icons-material';
```

### Element Type Invalid
**Error**: `Element type is invalid: expected a string (for built-in components) or a class/function`

**Solution**: This was caused by undefined components due to import issues. All import statements have been fixed with proper file extensions.

### Frontend Runtime Errors
**Error**: `farms.map is not a function` or similar array errors

**Solution**: The API returns paginated responses with data in the `results` property. The frontend context has been updated to handle this:
```typescript
// Handle paginated response - farms are in the 'results' property
const farmsData = response.data.results || response.data;
setFarms(Array.isArray(farmsData) ? farmsData : []);
```

**Error**: Missing fields in farm data (contact_person, contact_phone, etc.)

**Solution**: The backend serializer has been updated to return all required fields. The API now includes:
- `contact_person`, `contact_phone`, `contact_email`
- `created_at`, `updated_at`
- `total_houses`, `active_houses`

**Error**: No tasks visible for houses

**Solution**: Tasks are automatically generated when houses are created. For existing houses without tasks, run:
```bash
docker-compose exec backend python manage.py shell -c "
from houses.models import House
from tasks.task_scheduler import TaskScheduler
for house in House.objects.all():
    TaskScheduler.generate_tasks_for_house(house)
"
```

**Error**: All tasks show as pending when they should be completed

**Solution**: Tasks up to today are automatically marked as completed. To update existing tasks, run:
```bash
docker-compose exec backend python manage.py shell -c "
from houses.models import House
from tasks.models import Task
for house in House.objects.all():
    current_day = house.current_day
    if current_day and current_day > 0:
        Task.objects.filter(
            house=house,
            day_offset__lte=current_day,
            is_completed=False
        ).update(is_completed=True)
"
```

## 🗄️ Database Issues

### PostgreSQL Connection Failed
**Error**: `FATAL: password authentication failed for user "postgres"`

**Solution**: Check the database credentials in your `.env` file:
```
DB_NAME=chicken_management
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=db
DB_PORT=5432
```

### Migration Errors
**Error**: `No migrations to apply` but tables don't exist

**Solution**: Create and apply migrations manually:
```bash
# Generate migrations for all apps
docker-compose exec backend python manage.py makemigrations

# Apply all migrations
docker-compose exec backend python manage.py migrate
```

## 🔄 Container Issues

### Container Won't Start
**Error**: Container exits immediately

**Solution**: Check logs and restart:
```bash
# Check logs
docker-compose logs <service_name>

# Restart specific service
docker-compose restart <service_name>

# Rebuild and restart
docker-compose up --build -d <service_name>
```

### Volume Mount Issues
**Error**: Changes not reflected in container

**Solution**: Rebuild the container to pick up changes:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 🌐 Network Issues

### CORS Errors
**Error**: `Access to fetch at 'http://localhost:8000' from origin 'http://localhost:3000' has been blocked by CORS policy`

**Solution**: CORS is already configured in Django settings:
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CORS_ALLOW_CREDENTIALS = True
```

### API Not Responding
**Error**: `Connection refused` or timeout

**Solution**: Check if services are running:
```bash
# Check container status
docker-compose ps

# Check logs
docker-compose logs backend

# Test API directly
curl http://localhost:8000/api/auth/login/
```

## 🚀 Quick Fixes

### Complete Reset
If you encounter persistent issues, try a complete reset:

```bash
# Stop all containers
docker-compose down

# Remove all containers and volumes
docker-compose down -v

# Remove images (optional)
docker-compose down --rmi all

# Run setup script
./setup.sh
```

### Check Service Health
```bash
# Check all services
docker-compose ps

# Check specific service logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs db

# Test API
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### Verify Frontend
```bash
# Check if frontend is accessible
curl http://localhost:3000

# Check frontend compilation
docker-compose logs frontend | grep -E "(ERROR|Failed|webpack compiled)"
```

## 📞 Getting Help

If you continue to experience issues:

1. Check the logs: `docker-compose logs`
2. Verify all services are running: `docker-compose ps`
3. Test API connectivity: `curl http://localhost:8000/api/`
4. Check the setup script output for any errors
5. Ensure all ports (3000, 8000, 5432) are available

## 🔧 Environment Variables

Make sure your `.env` file contains all required variables:

```env
# Django Settings
SECRET_KEY=django-insecure-change-this-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Settings
DB_NAME=chicken_management
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=db
DB_PORT=5432

# Admin Settings
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@chickenmanagement.com
```

## 📝 Common Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild and start
docker-compose up --build -d

# Execute commands in containers
docker-compose exec backend python manage.py shell
docker-compose exec frontend npm install

# Check service status
docker-compose ps
```
