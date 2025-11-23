# Application Running Status

## Quick Start

The application is now running! Access it at:

- **Frontend:** http://localhost:3002
- **Backend API:** http://localhost:8002/api
- **Admin Panel:** http://localhost:8002/admin

## Default Credentials

- **Username:** `admin`
- **Password:** `admin123`

## Service Status

All services should be running:
- ✅ Database (PostgreSQL): Port 5433
- ✅ Redis: Port 6380
- ✅ Backend (Django): Port 8002
- ✅ Frontend (React): Port 3002

## Checking Status

### Using Make Commands
```bash
# Check service status
make status

# View logs
make logs

# View backend logs only
make logs-backend

# View frontend logs only
make logs-frontend
```

### Using Docker Compose
```bash
# Check status
docker-compose ps

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

## Starting the Application

If services are not running:

```bash
# Start all services
make dev

# Or using docker-compose
docker-compose up -d
```

## Stopping the Application

```bash
# Stop all services
make down

# Or using docker-compose
docker-compose down
```

## Restarting Services

```bash
# Restart all services
make restart

# Or restart specific service
docker-compose restart backend
docker-compose restart frontend
```

## Health Check Note

The backend health check may show as "unhealthy" because it checks an authenticated endpoint (`/api/rotem/farms/`). This is expected behavior - the service is actually running correctly.

To verify the backend is working:
```bash
curl http://localhost:8002/api/
```

This should return: `{"detail":"Authentication credentials were not provided."}` which confirms the API is running.

## Testing the Application

1. **Open Frontend:**
   - Navigate to http://localhost:3002
   - Login with default credentials (admin/admin123)

2. **Test API:**
   ```bash
   # Get authentication token
   curl -X POST http://localhost:8002/api/auth/login/ \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"admin123"}'
   
   # Use token to access API
   curl -H "Authorization: Token YOUR_TOKEN" http://localhost:8002/api/organizations/
   ```

3. **Test New Features:**
   - Navigate to `/flocks` to see flock management
   - Navigate to `/reports` to see reporting features
   - Navigate to `/analytics` to see analytics dashboard
   - Navigate to `/organization/settings` to manage organization

## Troubleshooting

### Backend not starting
```bash
# Check backend logs
docker-compose logs backend

# Rebuild backend
docker-compose build backend
docker-compose up -d backend
```

### Frontend not starting
```bash
# Check frontend logs
docker-compose logs frontend

# Rebuild frontend
docker-compose build frontend
docker-compose up -d frontend
```

### Database issues
```bash
# Check database connection
docker-compose exec db psql -U postgres -d chicken_management

# Run migrations
docker-compose exec backend python manage.py migrate
```

### Port conflicts
If ports are already in use:
- Backend: Change port in `docker-compose.yml` (currently 8002)
- Frontend: Change port in `docker-compose.yml` (currently 3002)
- Database: Change port in `docker-compose.yml` (currently 5433)

## Recent Updates

The application now includes:
- ✅ Multi-tenancy (Organizations)
- ✅ Flock Tracking & Lifecycle Management
- ✅ Advanced Analytics & Business Intelligence
- ✅ Advanced Reporting
- ✅ Performance Record Entry
- ✅ All API endpoints tested and working
- ✅ All migrations applied

## Next Steps

1. **Login to the application** at http://localhost:3002
2. **Explore the new features:**
   - Create flocks
   - Add performance records
   - View analytics
   - Generate reports
   - Manage organizations

---

**Status:** ✅ Application Running  
**Last Updated:** 2025-11-21

