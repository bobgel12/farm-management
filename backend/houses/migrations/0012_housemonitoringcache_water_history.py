from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("houses", "0011_farmmonitoringcache_house_statuses"),
    ]

    operations = [
        migrations.AddField(
            model_name="housemonitoringcache",
            name="water_history_payload",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="housemonitoringcache",
            name="water_history_fetched_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
