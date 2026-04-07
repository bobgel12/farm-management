from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('houses', '0007_waterconsumptionalert_expected_consumption'),
    ]

    operations = [
        migrations.AddField(
            model_name='waterconsumptionalert',
            name='anomaly_direction',
            field=models.CharField(
                choices=[('high', 'High'), ('low', 'Low')],
                default='high',
                help_text='Direction of anomaly compared to baseline',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='waterconsumptionalert',
            name='anomaly_reason',
            field=models.CharField(
                default='possible_leak',
                help_text='Reason code (e.g., possible_leak, possible_under_drinking)',
                max_length=50,
            ),
        ),
        migrations.AlterUniqueTogether(
            name='waterconsumptionalert',
            unique_together={('house', 'alert_date', 'anomaly_direction')},
        ),
    ]
