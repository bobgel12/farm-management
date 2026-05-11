from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('houses', '0010_farmmonitoringcache_housemonitoringcache_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='farmmonitoringcache',
            name='house_statuses',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
