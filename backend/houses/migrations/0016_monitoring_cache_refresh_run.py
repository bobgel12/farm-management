import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("houses", "0015_alter_housemonitoringsnapshot_timestamp"),
    ]

    operations = [
        migrations.CreateModel(
            name="MonitoringCacheRefreshRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("run_id", models.UUIDField(db_index=True, unique=True)),
                (
                    "trigger_type",
                    models.CharField(
                        choices=[("scheduled", "Scheduled"), ("manual", "Manual")],
                        max_length=16,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("queued", "Queued"),
                            ("running", "Running"),
                            ("success", "Success"),
                            ("partial", "Partial"),
                            ("failed", "Failed"),
                        ],
                        db_index=True,
                        default="queued",
                        max_length=16,
                    ),
                ),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("farms_processed", models.IntegerField(default=0)),
                ("houses_processed", models.IntegerField(default=0)),
                ("result_payload", models.JSONField(blank=True, default=dict)),
                ("error_summary", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "requested_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="monitoring_cache_refresh_runs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="monitoringcacherefreshrun",
            index=models.Index(fields=["trigger_type", "-created_at"], name="houses_moni_trigger_bdbf61_idx"),
        ),
        migrations.AddIndex(
            model_name="monitoringcacherefreshrun",
            index=models.Index(fields=["status", "created_at"], name="houses_moni_status_4d6cda_idx"),
        ),
    ]
