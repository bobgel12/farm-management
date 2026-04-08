from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rotem_scraper', '0005_consolidate_farm_model'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mlprediction',
            name='prediction_type',
            field=models.CharField(
                choices=[
                    ('anomaly', 'Anomaly Detection'),
                    ('failure', 'Equipment Failure'),
                    ('optimization', 'Environmental Optimization'),
                    ('performance', 'Performance Analysis'),
                    ('water_forecast', 'Water Forecast'),
                ],
                max_length=50,
            ),
        ),
    ]

