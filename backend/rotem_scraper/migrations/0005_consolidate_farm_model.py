# Comprehensive migration to consolidate RotemController to use Farm model
# This migration handles the full transition from RotemFarm FK to Farm FK

from django.db import migrations, models
import django.db.models.deletion


def copy_old_farm_to_legacy(apps, schema_editor):
    """Step 1: Copy existing farm FK values to legacy_rotem_farm"""
    # We use raw SQL here because we're working with the old schema
    # where 'farm_id' points to RotemFarm
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE rotem_scraper_rotemcontroller 
            SET legacy_rotem_farm_id = farm_id 
            WHERE farm_id IS NOT NULL
        """)
        print(f"  ✅ Copied {cursor.rowcount} farm references to legacy_rotem_farm")


def migrate_to_new_farm(apps, schema_editor):
    """Step 2: Migrate controllers to reference Farm model"""
    RotemController = apps.get_model('rotem_scraper', 'RotemController')
    RotemFarm = apps.get_model('rotem_scraper', 'RotemFarm')
    Farm = apps.get_model('farms', 'Farm')
    Organization = apps.get_model('organizations', 'Organization')
    
    # Get default organization
    default_org = Organization.objects.filter(slug='default').first()
    
    migrated_count = 0
    created_farms = 0
    
    for controller in RotemController.objects.all():
        rotem_farm = controller.legacy_rotem_farm
        
        if not rotem_farm:
            print(f"  ⚠️  Controller {controller.controller_id} has no legacy_rotem_farm")
            continue
        
        # Try to find matching Farm
        farm = None
        
        # Strategy 1: Match by rotem_farm_id
        farm = Farm.objects.filter(rotem_farm_id=rotem_farm.farm_id).first()
        
        # Strategy 2: Match by name
        if not farm:
            farm = Farm.objects.filter(name=rotem_farm.farm_name).first()
        
        # Strategy 3: Create new Farm
        if not farm:
            farm = Farm.objects.create(
                organization=default_org,
                name=rotem_farm.farm_name,
                location='Migrated from Rotem',
                contact_person='Admin',
                contact_phone='',
                contact_email='admin@example.com',
                has_system_integration=True,
                integration_type='rotem',
                integration_status='active',
                rotem_farm_id=rotem_farm.farm_id,
                rotem_username=rotem_farm.rotem_username or '',
                rotem_password=rotem_farm.rotem_password or '',
                rotem_gateway_name=rotem_farm.gateway_name,
                rotem_gateway_alias=rotem_farm.gateway_alias,
                is_active=rotem_farm.is_active
            )
            created_farms += 1
            print(f"  ✅ Created Farm '{farm.name}' from RotemFarm")
        
        # Link controller to farm
        controller.farm = farm
        controller.save()
        migrated_count += 1
    
    print(f"\n=== Migration Summary ===")
    print(f"Controllers migrated: {migrated_count}")
    print(f"Farms created: {created_farms}")


def reverse_migration(apps, schema_editor):
    """Reverse: Copy legacy_rotem_farm back to farm (as RotemFarm FK)"""
    # This is complex - we'd need to restore the old schema first
    print("  ⚠️  Reverse migration not fully implemented - manual intervention may be needed")


class Migration(migrations.Migration):
    """
    This migration consolidates RotemController to use the Farm model.
    
    Steps:
    1. Add legacy_rotem_farm field (to preserve old RotemFarm FK)
    2. Copy old farm data to legacy_rotem_farm (raw SQL, before schema change)
    3. Change farm field to nullable FK to farms.Farm
    4. Migrate data: find/create Farm records and link controllers
    """

    dependencies = [
        ('farms', '0007_assign_farms_to_default_org'),
        ('organizations', '0002_organizationinvite'),
        ('rotem_scraper', '0004_rotemdailysummary'),
    ]

    operations = [
        # Step 1: Add legacy_rotem_farm field
        migrations.AddField(
            model_name='rotemcontroller',
            name='legacy_rotem_farm',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='legacy_controllers',
                to='rotem_scraper.rotemfarm',
                help_text='Legacy RotemFarm reference - for migration only'
            ),
        ),
        
        # Step 2: Copy old farm FK to legacy_rotem_farm (before changing farm field)
        migrations.RunPython(copy_old_farm_to_legacy, migrations.RunPython.noop),
        
        # Step 3: Change farm field to FK to farms.Farm (nullable)
        migrations.AlterField(
            model_name='rotemcontroller',
            name='farm',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='rotem_controllers',
                to='farms.farm',
                help_text='Farm this controller belongs to'
            ),
        ),
        
        # Step 4: Migrate data to new farm FK
        migrations.RunPython(migrate_to_new_farm, reverse_migration),
    ]

