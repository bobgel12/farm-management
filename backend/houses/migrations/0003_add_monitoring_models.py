# Generated manually for monitoring models
# Migration for HouseMonitoringSnapshot and HouseAlarm models

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('houses', '0002_house_batch_start_date_house_capacity_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='HouseMonitoringSnapshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('average_temperature', models.FloatField(blank=True, null=True)),
                ('outside_temperature', models.FloatField(blank=True, null=True)),
                ('humidity', models.FloatField(blank=True, null=True)),
                ('static_pressure', models.FloatField(blank=True, null=True)),
                ('target_temperature', models.FloatField(blank=True, null=True)),
                ('ventilation_level', models.FloatField(blank=True, null=True)),
                ('growth_day', models.IntegerField(blank=True, null=True)),
                ('bird_count', models.IntegerField(blank=True, null=True)),
                ('livability', models.FloatField(blank=True, null=True)),
                ('water_consumption', models.FloatField(blank=True, null=True)),
                ('feed_consumption', models.FloatField(blank=True, null=True)),
                ('airflow_cfm', models.FloatField(blank=True, null=True)),
                ('airflow_percentage', models.FloatField(blank=True, null=True)),
                ('connection_status', models.IntegerField(blank=True, help_text='0=disconnected, 1=connected', null=True)),
                ('alarm_status', models.CharField(choices=[('normal', 'Normal'), ('warning', 'Warning'), ('critical', 'Critical')], default='normal', max_length=20)),
                ('raw_data', models.JSONField(default=dict, help_text='Complete raw data from Rotem API')),
                ('sensor_data', models.JSONField(default=dict, help_text='Structured sensor data (temp sensors, etc.)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('house', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='monitoring_snapshots', to='houses.house')),
            ],
            options={
                'verbose_name': 'House Monitoring Snapshot',
                'verbose_name_plural': 'House Monitoring Snapshots',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='HouseAlarm',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alarm_type', models.CharField(choices=[('temperature', 'Temperature'), ('humidity', 'Humidity'), ('pressure', 'Pressure'), ('connection', 'Connection'), ('consumption', 'Consumption'), ('equipment', 'Equipment'), ('other', 'Other')], max_length=50)),
                ('severity', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], default='medium', max_length=20)),
                ('message', models.TextField()),
                ('parameter_name', models.CharField(blank=True, max_length=100, null=True)),
                ('parameter_value', models.FloatField(blank=True, null=True)),
                ('threshold_value', models.FloatField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_resolved', models.BooleanField(default=False)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('resolved_by', models.CharField(blank=True, max_length=100, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('house', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alarms', to='houses.house')),
                ('snapshot', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='alarms', to='houses.housemonitoringsnapshot')),
            ],
            options={
                'verbose_name': 'House Alarm',
                'verbose_name_plural': 'House Alarms',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='housemonitoringsnapshot',
            index=models.Index(fields=['house', '-timestamp'], name='houses_hous_house_t_idx'),
        ),
        migrations.AddIndex(
            model_name='housemonitoringsnapshot',
            index=models.Index(fields=['timestamp'], name='houses_hous_timesta_idx'),
        ),
        migrations.AddIndex(
            model_name='housemonitoringsnapshot',
            index=models.Index(fields=['house', 'alarm_status', '-timestamp'], name='houses_hous_house_i_alarm_idx'),
        ),
        migrations.AddIndex(
            model_name='housealarm',
            index=models.Index(fields=['house', '-timestamp'], name='houses_hous_house_a_idx'),
        ),
        migrations.AddIndex(
            model_name='housealarm',
            index=models.Index(fields=['is_active', '-timestamp'], name='houses_hous_is_acti_idx'),
        ),
        migrations.AddIndex(
            model_name='housealarm',
            index=models.Index(fields=['severity', '-timestamp'], name='houses_hous_severit_idx'),
        ),
    ]

