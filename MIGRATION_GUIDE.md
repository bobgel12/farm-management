# Database Migration Guide

## Overview

This guide explains how to create and run database migrations for the new features:
- Multi-tenancy (Organization models)
- Flock Management (Breed, Flock, FlockPerformance, FlockComparison)
- Reporting (ReportTemplate, ScheduledReport, ReportExecution, ReportBuilderQuery)
- Analytics (Dashboard, KPI, KPICalculation, AnalyticsQuery, Benchmark)

## Step 1: Generate Migrations

Run the following commands to generate migrations for all new apps:

```bash
cd backend

# Generate migrations for organizations app
python manage.py makemigrations organizations

# Generate migrations for new flock models in farms app
python manage.py makemigrations farms

# Generate migrations for reporting app
python manage.py makemigrations reporting

# Generate migrations for analytics app
python manage.py makemigrations analytics
```

## Step 2: Review Migration Files

After generating migrations, review the files to ensure:
1. All models are included
2. Foreign key relationships are correct
3. Indexes are created
4. Default values are set appropriately

## Step 3: Create Data Migration for Existing Farms

We need to assign existing farms to a default organization. Create a data migration:

```bash
python manage.py makemigrations farms --empty --name assign_farms_to_default_org
```

Then edit the migration file to include logic that:
1. Creates a default organization (if it doesn't exist)
2. Assigns all existing farms to this organization
3. Creates an OrganizationUser for each existing user

## Step 4: Run Migrations

```bash
# Run all migrations
python manage.py migrate

# Or run migrations for specific apps
python manage.py migrate organizations
python manage.py migrate farms
python manage.py migrate reporting
python manage.py migrate analytics
```

## Step 5: Verify Migration Success

After running migrations, verify:
1. All tables are created in the database
2. Foreign key constraints are in place
3. Indexes are created
4. Default organization exists
5. Existing farms are assigned to an organization

## Troubleshooting

### Migration Conflicts
If you encounter migration conflicts:
1. Review the migration dependencies
2. Merge conflicts if needed
3. Consider squashing migrations if there are too many

### Data Loss Warning
If Django warns about data loss:
- Review the migration operations
- Ensure nullable fields are set correctly
- Test migrations on a copy of production data first

### Foreign Key Errors
If you get foreign key errors:
- Ensure organizations app is migrated before farms
- Check that organization_id field allows null initially
- Run migrations in order: organizations → farms → reporting → analytics

## Migration Order

Migrations should be run in this order:
1. `organizations` (Organization and OrganizationUser)
2. `farms` (add organization FK to Farm, then Breed, Flock models)
3. `reporting` (depends on organizations)
4. `analytics` (depends on organizations)

## Post-Migration Steps

1. **Create Default Organization:**
   ```python
   from organizations.models import Organization
   default_org = Organization.objects.get_or_create(
       name='Default Organization',
       slug='default',
       defaults={
           'contact_email': 'admin@example.com',
           'subscription_tier': 'standard'
       }
   )
   ```

2. **Assign Existing Users:**
   ```python
   from organizations.models import Organization, OrganizationUser
   from django.contrib.auth.models import User
   
   org = Organization.objects.first()
   for user in User.objects.all():
       OrganizationUser.objects.get_or_create(
           organization=org,
           user=user,
           defaults={'role': 'owner' if user.is_staff else 'worker'}
       )
   ```

3. **Verify Data:**
   - Check that all farms have an organization
   - Verify organization users are created
   - Test API endpoints with organization filtering

