from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('farms', '0008_mortalityrecord'),
        ('houses', '0008_water_alert_direction_reason'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='waterconsumptionalert',
            name='is_resolved',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='waterconsumptionalert',
            name='resolved_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='waterconsumptionalert',
            name='resolved_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='resolved_water_alerts',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='waterconsumptionalert',
            name='snoozed_until',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='WaterConsumptionForecast',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('forecast_date', models.DateTimeField(db_index=True)),
                ('horizon_hours', models.IntegerField(default=24)),
                ('predicted_consumption', models.FloatField(help_text='Predicted water consumption (L/day)')),
                ('lower_bound', models.FloatField(blank=True, null=True)),
                ('upper_bound', models.FloatField(blank=True, null=True)),
                ('confidence_score', models.FloatField(default=0.6)),
                ('model_version', models.CharField(default='water_forecast_v1', max_length=50)),
                ('features', models.JSONField(default=dict)),
                ('source_date', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('farm', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='water_forecasts', to='farms.farm')),
                ('house', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='water_forecasts', to='houses.house')),
            ],
            options={
                'ordering': ['-forecast_date'],
                'unique_together': {('house', 'forecast_date', 'horizon_hours')},
            },
        ),
        migrations.AddIndex(
            model_name='waterconsumptionforecast',
            index=models.Index(fields=['house', '-forecast_date'], name='houses_water_house_id_8dd4cb_idx'),
        ),
        migrations.AddIndex(
            model_name='waterconsumptionforecast',
            index=models.Index(fields=['farm', '-forecast_date'], name='houses_water_farm_id_890ff2_idx'),
        ),
        migrations.AddIndex(
            model_name='waterconsumptionforecast',
            index=models.Index(fields=['horizon_hours', '-forecast_date'], name='houses_water_horizon_8bc54f_idx'),
        ),
    ]

