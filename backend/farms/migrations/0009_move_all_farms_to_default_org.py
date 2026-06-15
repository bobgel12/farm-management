from django.conf import settings
from django.db import migrations
import uuid


def move_all_farms_to_default_org(apps, schema_editor):
    Organization = apps.get_model('organizations', 'Organization')
    Farm = apps.get_model('farms', 'Farm')
    Dashboard = apps.get_model('analytics', 'Dashboard')
    AutomationWorkflow = apps.get_model('integrations', 'AutomationWorkflow')

    default_org, created = Organization.objects.get_or_create(
        slug='default',
        defaults={
            'id': uuid.uuid4(),
            'name': 'Default Organization',
            'description': 'Default organization for all farms',
            'contact_email': 'admin@example.com',
            'is_active': True,
            'is_trial': False,
            'subscription_tier': 'standard',
            'subscription_status': 'active',
            'max_farms': 1000,
            'max_users': 1000,
            'max_houses_per_farm': 100,
        },
    )

    if created:
        print(f'Created default organization: {default_org.name}')
    else:
        print(f'Using default organization: {default_org.name}')

    farms_moved = Farm.objects.exclude(organization_id=default_org.id).update(
        organization_id=default_org.id,
    )

    dashboards_updated = Dashboard.objects.filter(
        farm__isnull=False,
        dashboard_type='farm',
    ).exclude(
        organization_id=default_org.id,
    ).update(organization_id=default_org.id)

    workflows_updated = AutomationWorkflow.objects.filter(
        farm__isnull=False,
    ).exclude(
        organization_id=default_org.id,
    ).update(organization_id=default_org.id)

    print(
        f'Moved {farms_moved} farm(s), updated {dashboards_updated} dashboard(s), '
        f'and {workflows_updated} automation workflow(s) to {default_org.name}.'
    )


def noop_reverse(apps, schema_editor):
    print(
        'Reverse skipped: previous per-farm organization assignments cannot be restored.'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0002_organizationinvite'),
        ('analytics', '0002_dashboard_farm_link'),
        ('integrations', '0002_automation_workflow'),
        ('farms', '0008_mortalityrecord'),
    ]

    operations = [
        migrations.RunPython(move_all_farms_to_default_org, noop_reverse),
    ]
