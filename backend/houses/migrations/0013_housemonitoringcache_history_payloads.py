from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("houses", "0012_housemonitoringcache_water_history"),
    ]

    operations = [
        migrations.AddField(
            model_name="housemonitoringcache",
            name="feed_history_payload",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="housemonitoringcache",
            name="feed_history_fetched_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="housemonitoringcache",
            name="temperature_history_payload",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="housemonitoringcache",
            name="temperature_history_fetched_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
