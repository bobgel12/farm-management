# Database Migrations - Ready to Apply

## ✅ Migrations Generated Successfully

All database migrations have been generated and are ready to be applied. The migration files have been created for all new models and features.

## Migration Files Created

### 1. Organizations App (`organizations/migrations/0001_initial.py`)
- ✅ Organization model
- ✅ OrganizationUser model
- ✅ Indexes for slug, is_active, subscription_status

### 2. Farms App (`farms/migrations/0006_breed_flock_farm_organization_flockperformance_and_more.py`)
- ✅ Breed model
- ✅ Flock model
- ✅ Added organization FK to Farm model (nullable)
- ✅ FlockPerformance model
- ✅ FlockComparison model
- ✅ All indexes and constraints

### 3. Farms App Data Migration (`farms/migrations/0007_assign_farms_to_default_org.py`)
- ✅ Creates default organization
- ✅ Assigns existing farms to default organization
- ✅ Creates OrganizationUser memberships for existing users
- ✅ Handles reverse migration

### 4. Reporting App (`reporting/migrations/0001_initial.py`)
- ✅ ReportTemplate model
- ✅ ScheduledReport model
- ✅ ReportExecution model
- ✅ ReportBuilderQuery model
- ✅ All indexes

### 5. Analytics App (`analytics/migrations/0001_initial.py`)
- ✅ Dashboard model
- ✅ KPI model
- ✅ KPICalculation model
- ✅ AnalyticsQuery model
- ✅ Benchmark model
- ✅ All indexes

## Migration Status

Current migration status (before applying):
```
organizations
 [ ] 0001_initial
farms
 [X] 0001_initial (existing)
 [X] 0002_alter_farm_options... (existing)
 [X] 0003_program_farm_program... (existing)
 [X] 0004_programchangelog (existing)
 [X] 0005_farm_description... (existing)
 [ ] 0006_breed_flock_farm_organization... (NEW - ready to apply)
 [ ] 0007_assign_farms_to_default_org (NEW - ready to apply)
reporting
 [ ] 0001_initial (NEW - ready to apply)
analytics
 [ ] 0001_initial (NEW - ready to apply)
```

## How to Apply Migrations

### Option 1: Apply All Migrations at Once
```bash
cd backend
source venv/bin/activate
python manage.py migrate
```

### Option 2: Apply Migrations One App at a Time
```bash
cd backend
source venv/bin/activate

# Apply organizations migrations first (foundation)
python manage.py migrate organizations

# Apply farms migrations (includes data migration)
python manage.py migrate farms

# Apply reporting migrations
python manage.py migrate reporting

# Apply analytics migrations
python manage.py migrate analytics
```

## Data Migration Details

The data migration (`0007_assign_farms_to_default_org`) will:
1. **Create Default Organization:**
   - Name: "Default Organization"
   - Slug: "default"
   - Subscription tier: "standard"
   - Max limits: 1000 farms, 1000 users, 100 houses per farm

2. **Assign Existing Farms:**
   - All farms without an organization will be assigned to the default organization

3. **Create User Memberships:**
   - Staff users → "owner" role with all permissions
   - Regular users → "worker" role with basic permissions
   - All users get `can_view_reports: true`

## Migration Dependencies

Migrations must be applied in this order due to dependencies:
1. **organizations** (0001_initial) - Creates Organization and OrganizationUser models
2. **farms** (0006_breed_flock...) - Depends on organizations, creates Breed, Flock, etc.
3. **farms** (0007_assign_farms...) - Depends on 0006, assigns existing data
4. **reporting** (0001_initial) - Depends on organizations
5. **analytics** (0001_initial) - Depends on organizations

## Pre-Migration Checklist

Before running migrations, ensure:
- ✅ Database is backed up (if production)
- ✅ Django environment is set up
- ✅ All dependencies are installed
- ✅ Database connection is working
- ✅ No pending code changes that affect models

## Post-Migration Verification

After migrations are applied, verify:
1. Check migration status:
   ```bash
   python manage.py showmigrations
   ```
   All migrations should show `[X]` (applied).

2. Verify default organization exists:
   ```python
   from organizations.models import Organization
   default_org = Organization.objects.get(slug='default')
   print(f"Default org: {default_org.name}")
   ```

3. Verify farms are assigned:
   ```python
   from farms.models import Farm
   farms_with_org = Farm.objects.filter(organization__isnull=False).count()
   print(f"Farms with organization: {farms_with_org}")
   ```

4. Verify user memberships:
   ```python
   from organizations.models import OrganizationUser
   members = OrganizationUser.objects.count()
   print(f"Organization members: {members}")
   ```

5. Test API endpoints:
   - `/api/organizations/` - Should list organizations
   - `/api/flocks/` - Should list flocks (empty initially)
   - `/api/breeds/` - Should list breeds (empty initially)
   - `/api/dashboards/` - Should list dashboards (empty initially)

## Troubleshooting

### Migration Conflicts
If you encounter migration conflicts:
1. Check if migrations are already applied:
   ```bash
   python manage.py showmigrations
   ```
2. If partially applied, use `--fake` carefully:
   ```bash
   python manage.py migrate farms --fake 0006
   ```

### Foreign Key Errors
If you get foreign key errors:
1. Ensure organizations migrations are applied first
2. Check that organization FK in Farm model allows null initially

### Data Migration Errors
If data migration fails:
1. Check that default organization can be created
2. Verify existing farms exist in database
3. Check user model is accessible

## Rollback (if needed)

To rollback migrations:
```bash
# Rollback specific migration
python manage.py migrate farms 0005

# Rollback all new migrations (careful!)
python manage.py migrate farms 0005
python manage.py migrate reporting zero
python manage.py migrate analytics zero
python manage.py migrate organizations zero
```

**Note:** Rolling back the data migration will remove organization assignments but won't delete the default organization by default (safety measure).

## Next Steps After Migrations

Once migrations are successfully applied:
1. ✅ Database schema will be updated
2. ✅ All models will be available in Django admin
3. ✅ API endpoints will work with new models
4. ✅ Frontend can start integrating with APIs
5. ✅ You can create organizations, flocks, reports, etc.

---

**Status:** ✅ Ready to Apply  
**Generated:** 2025-11-21  
**Total New Migrations:** 5 files across 4 apps

