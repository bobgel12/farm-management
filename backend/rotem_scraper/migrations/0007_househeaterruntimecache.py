from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("houses", "0009_water_alert_lifecycle_and_forecast"),
        ("rotem_scraper", "0006_expand_prediction_types"),
    ]

    operations = [
        migrations.CreateModel(
            name="HouseHeaterRuntimeCache",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("growth_day", models.IntegerField(help_text="House growth day from Rotem history record")),
                (
                    "record_date",
                    models.DateField(
                        blank=True,
                        help_text="Derived from house batch/chicken start date where available",
                        null=True,
                    ),
                ),
                (
                    "is_summary_row",
                    models.BooleanField(
                        default=False,
                        help_text="True when record represents summary row (growth_day = -1)",
                    ),
                ),
                ("total_runtime_minutes", models.IntegerField(default=0)),
                (
                    "total_computation_method",
                    models.CharField(
                        default="provided_total",
                        help_text="provided_total or sum_devices",
                        max_length=32,
                    ),
                ),
                ("per_device_json", models.JSONField(default=dict, help_text="Per heater device runtime map")),
                (
                    "source_timestamp",
                    models.DateTimeField(
                        blank=True,
                        help_text="Source timestamp from Rotem payload if present",
                        null=True,
                    ),
                ),
                ("last_synced_at", models.DateTimeField(auto_now=True)),
                ("raw_record_json", models.JSONField(default=dict, help_text="Raw Rotem row for traceability")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "house",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="heater_runtime_cache",
                        to="houses.house",
                    ),
                ),
            ],
            options={
                "verbose_name": "House Heater Runtime Cache",
                "verbose_name_plural": "House Heater Runtime Cache",
                "ordering": ["growth_day"],
                "unique_together": {("house", "growth_day")},
            },
        ),
        migrations.AddIndex(
            model_name="househeaterruntimecache",
            index=models.Index(fields=["house", "growth_day"], name="rotem_scrap_house_i_41ba61_idx"),
        ),
        migrations.AddIndex(
            model_name="househeaterruntimecache",
            index=models.Index(fields=["house", "record_date"], name="rotem_scrap_house_i_947dc3_idx"),
        ),
        migrations.AddIndex(
            model_name="househeaterruntimecache",
            index=models.Index(fields=["last_synced_at"], name="rotem_scrap_last_sy_ccf8d9_idx"),
        ),
    ]
