# Generated for ML roadmap: HouseDailySummary, HouseFeatureSnapshot, FlockRiskScore

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('farms', '0008_mortalityrecord'),
        ('houses', '0013_housemonitoringcache_history_payloads'),
    ]

    operations = [
        migrations.CreateModel(
            name='HouseDailySummary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(db_index=True)),
                ('growth_day', models.IntegerField(blank=True, null=True)),
                ('temperature_avg', models.FloatField(blank=True, null=True)),
                ('temperature_min', models.FloatField(blank=True, null=True)),
                ('temperature_max', models.FloatField(blank=True, null=True)),
                ('humidity_avg', models.FloatField(blank=True, null=True)),
                ('static_pressure_avg', models.FloatField(blank=True, null=True)),
                ('water_consumption_avg', models.FloatField(blank=True, null=True)),
                ('water_consumption_max', models.FloatField(blank=True, null=True)),
                ('feed_consumption_avg', models.FloatField(blank=True, null=True)),
                ('feed_consumption_max', models.FloatField(blank=True, null=True)),
                ('ventilation_avg', models.FloatField(blank=True, null=True)),
                ('heater_runtime_minutes', models.FloatField(blank=True, null=True)),
                ('snapshot_count', models.IntegerField(default=0)),
                ('expected_snapshots', models.IntegerField(default=0)),
                ('completeness_ratio', models.FloatField(default=0.0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('house', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='daily_summaries', to='houses.house')),
            ],
            options={
                'ordering': ['-date', 'house'],
                'unique_together': {('house', 'date')},
            },
        ),
        migrations.AddIndex(
            model_name='housedailysummary',
            index=models.Index(fields=['house', 'date'], name='houses_hous_house_i_dsum_idx'),
        ),
        migrations.AddIndex(
            model_name='housedailysummary',
            index=models.Index(fields=['house', 'growth_day'], name='houses_hous_house_gd_idx'),
        ),
        migrations.CreateModel(
            name='HouseFeatureSnapshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(db_index=True)),
                ('growth_day', models.IntegerField(blank=True, null=True)),
                ('bird_count', models.IntegerField(blank=True, null=True)),
                ('avg_temp', models.FloatField(blank=True, null=True)),
                ('humidity', models.FloatField(blank=True, null=True)),
                ('static_pressure', models.FloatField(blank=True, null=True)),
                ('vent_level', models.FloatField(blank=True, null=True)),
                ('outside_temp', models.FloatField(blank=True, null=True)),
                ('water_24h', models.FloatField(blank=True, null=True)),
                ('feed_24h', models.FloatField(blank=True, null=True)),
                ('water_delta_1h', models.FloatField(blank=True, null=True)),
                ('temp_std_6h', models.FloatField(blank=True, null=True)),
                ('heater_runtime_24h', models.FloatField(blank=True, null=True)),
                ('features', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('house', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feature_snapshots', to='houses.house')),
            ],
            options={
                'ordering': ['-timestamp'],
                'unique_together': {('house', 'timestamp')},
            },
        ),
        migrations.AddIndex(
            model_name='housefeaturesnapshot',
            index=models.Index(fields=['house', '-timestamp'], name='houses_hous_feat_ts_idx'),
        ),
        migrations.CreateModel(
            name='FlockRiskScore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('risk_type', models.CharField(choices=[('mortality_3d', 'Mortality Risk (3 days)'), ('mortality_7d', 'Mortality Risk (7 days)'), ('fcr_35d', 'FCR at Day 35'), ('livability_harvest', 'Livability at Harvest')], max_length=32)),
                ('score', models.FloatField(help_text='Probability or predicted value depending on risk_type')),
                ('confidence', models.FloatField(default=0.5)),
                ('model_version', models.CharField(default='mortality_risk_v1', max_length=64)),
                ('top_features', models.JSONField(default=dict)),
                ('scored_at', models.DateTimeField(auto_now_add=True)),
                ('flock_age_days', models.IntegerField(blank=True, null=True)),
                ('flock', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='risk_scores', to='farms.flock')),
                ('house', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='flock_risk_scores', to='houses.house')),
            ],
            options={
                'ordering': ['-scored_at'],
            },
        ),
        migrations.AddIndex(
            model_name='flockriskscore',
            index=models.Index(fields=['flock', 'risk_type', '-scored_at'], name='houses_flk_risk_idx'),
        ),
        migrations.AddIndex(
            model_name='flockriskscore',
            index=models.Index(fields=['house', 'risk_type', '-scored_at'], name='houses_hse_risk_idx'),
        ),
    ]
