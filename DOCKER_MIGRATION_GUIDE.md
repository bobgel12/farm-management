# Docker Migration Guide

## Overview

This guide explains how to apply database migrations using Docker and Make commands for the new features:
- Multi-tenancy (Organizations)
- Flock Management
- Business Intelligence (Analytics)
- Advanced Reporting

## Quick Start

### Option 1: Using Make Commands (Recommended)

```bash
# Start all services (this automatically runs migrations)
make dev

# Or if services are already running, apply migrations manually
make migrate

# Apply migrations for specific new apps
make migrate-all
```

### Option 2: Using Docker Compose Directly

```bash
# Start services (migrations run automatically on startup)
docker-compose up -d

# Or apply migrations manually if containers are running
docker-compose exec backend python manage.py migrate
```

## Migration Status Check

Check which migrations have been applied:

```bash
# Check migration status for all apps
docker-compose exec backend python manage.py showmigrations

# Check specific apps
docker-compose exec backend python manage.py showmigrations organizations farms reporting analytics
```

## Verify Data Migration

After migrations, verify that the data migration created the default organization:

```bash
# Check organization data
docker-compose exec backend python manage.py shell
```

Then in the shell:
```python
from organizations.models import Organization, OrganizationUser
from farms.models import Farm

# Check default organization
org = Organization.objects.first()
print(f"Organization: {org.name}")
print(f"Farms: {org.farms.count()}")
print(f"Users: {org.organization_users.count()}")

# Check farms are assigned
farms = Farm.objects.filter(organization=org)
print(f"Farms in organization: {farms.count()}")
```

## Testing API Endpoints

After migrations are applied, test the API endpoints:

```bash
# Test organizations endpoint
curl -H "Authorization: Token YOUR_TOKEN" http://localhost:8002/api/organizations/

# Test flocks endpoint
curl -H "Authorization: Token YOUR_TOKEN" http://localhost:8002/api/flocks/

# Test analytics endpoints
curl -H "Authorization: Token YOUR_TOKEN" http://localhost:8002/api/kpis/
curl -H "Authorization: Token YOUR_TOKEN" http://localhost:8002/api/dashboards/

# Test reporting endpoints
curl -H "Authorization: Token YOUR_TOKEN" http://localhost:8002/api/report-templates/
```

Or use the test script:
```bash
python3 test_new_features_api.py
```

## Migration Order

Migrations are automatically applied in the correct order by Django:
1. `organizations` - Creates Organization and OrganizationUser models
2. `farms` - Adds organization FK to Farm, creates Breed, Flock models
3. `farms` (data migration) - Assigns existing farms to default organization
4. `reporting` - Creates report models
5. `analytics` - Creates analytics models

## Troubleshooting

### Migrations Already Applied

If you see "No migrations to apply", the migrations are already in the database:
```bash
# Verify migrations are applied
docker-compose exec backend python manage.py showmigrations organizations farms reporting analytics
```

All should show `[X]` (applied).

### Database Connection Issues

If migrations fail due to database connection:
```bash
# Check database is running
docker-compose ps db

# Check database connection
docker-compose exec backend python manage.py dbshell
```

### Rebuild Containers

If you need to rebuild containers with new code:
```bash
# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d

# Migrations will run automatically on startup
```

### Manual Migration Application

If automatic migrations fail, apply manually:
```bash
# Apply specific app migrations
docker-compose exec backend python manage.py migrate organizations
docker-compose exec backend python manage.py migrate farms
docker-compose exec backend python manage.py migrate reporting
docker-compose exec backend python manage.py migrate analytics
```

## Data Migration Details

The data migration (`0007_assign_farms_to_default_org`) will:
1. Create a "Default Organization" (if it doesn't exist)
2. Assign all existing farms to this organization
3. Create OrganizationUser memberships for all existing users
   - Staff users → "owner" role
   - Regular users → "worker" role

This ensures backward compatibility - existing data is automatically assigned to an organization.

## Post-Migration Verification

After migrations, verify:

1. **Organization exists:**
   ```bash
   docker-compose exec backend python manage.py shell -c "from organizations.models import Organization; print(Organization.objects.count())"
   ```

2. **Farms are assigned:**
   ```bash
   docker-compose exec backend python manage.py shell -c "from farms.models import Farm; print(Farm.objects.filter(organization__isnull=False).count())"
   ```

3. **User memberships created:**
   ```bash
   docker-compose exec backend python manage.py shell -c "from organizations.models import OrganizationUser; print(OrganizationUser.objects.count())"
   ```

4. **API endpoints work:**
   ```bash
   curl -H "Authorization: Token YOUR_TOKEN" http://localhost:8002/api/organizations/
   ```

## Production Deployment

For production deployment:

1. **Build images:**
   ```bash
   make prod-build
   ```

2. **Apply migrations:**
   ```bash
   # Migrations will run automatically on container startup
   make prod-up
   ```

3. **Or manually:**
   ```bash
   docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate
   ```

## Rollback (if needed)

To rollback migrations (use with caution):

```bash
# Rollback specific migration
docker-compose exec backend python manage.py migrate farms 0005

# Rollback entire app
docker-compose exec backend python manage.py migrate organizations zero
```

**Warning:** Rolling back the data migration will remove organization assignments but won't delete the default organization.

---

**Status:** ✅ Migrations Ready  
**Last Updated:** 2025-11-21

