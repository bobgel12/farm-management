from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('houses', '0014_ml_feature_models'),
    ]

    operations = [
        migrations.AlterField(
            model_name='housemonitoringsnapshot',
            name='timestamp',
            field=models.DateTimeField(db_index=True, default=django.utils.timezone.now),
        ),
    ]
