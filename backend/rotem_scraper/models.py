from django.db import models
from django.contrib.auth.models import User
import uuid


class RotemFarm(models.Model):
    """Farm information from Rotem API"""
    farm_id = models.CharField(max_length=100, unique=True)
    farm_name = models.CharField(max_length=200)
    gateway_name = models.CharField(max_length=100)
    gateway_alias = models.CharField(max_length=200)
    # Rotem credentials for this specific farm
    rotem_username = models.CharField(max_length=200, blank=True)
    rotem_password = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.farm_name

    class Meta:
        verbose_name = "Rotem Farm"
        verbose_name_plural = "Rotem Farms"


class RotemUser(models.Model):
    """User information from Rotem API"""
    user_id = models.IntegerField(unique=True)
    username = models.CharField(max_length=200)
    display_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True)
    is_farm_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.display_name

    class Meta:
        verbose_name = "Rotem User"
        verbose_name_plural = "Rotem Users"


class RotemController(models.Model):
    """Controller hardware information"""
    controller_id = models.CharField(max_length=100, unique=True)
    farm = models.ForeignKey(RotemFarm, on_delete=models.CASCADE, related_name='controllers')
    controller_name = models.CharField(max_length=200)
    controller_type = models.CharField(max_length=50)
    is_connected = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.controller_name} ({self.controller_id})"

    class Meta:
        verbose_name = "Rotem Controller"
        verbose_name_plural = "Rotem Controllers"


class RotemDataPoint(models.Model):
    """Time-series data points from controllers"""
    controller = models.ForeignKey(RotemController, on_delete=models.CASCADE, related_name='data_points')
    timestamp = models.DateTimeField()
    data_type = models.CharField(max_length=50)  # temperature, humidity, etc.
    value = models.FloatField()
    unit = models.CharField(max_length=20)
    quality = models.CharField(max_length=20, default='good')  # good, warning, error
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['controller', 'timestamp', 'data_type']
        indexes = [
            models.Index(fields=['controller', 'timestamp']),
            models.Index(fields=['data_type', 'timestamp']),
        ]
        verbose_name = "Rotem Data Point"
        verbose_name_plural = "Rotem Data Points"

    def __str__(self):
        return f"{self.controller.controller_name} - {self.data_type}: {self.value}"


class RotemScrapeLog(models.Model):
    """Log of scraping operations"""
    STATUS_CHOICES = [
        ('running', 'Running'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('partial', 'Partial Success'),
    ]
    
    scrape_id = models.UUIDField(default=uuid.uuid4, unique=True)
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='running')
    data_points_collected = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    raw_data = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"Scrape {self.scrape_id} - {self.status}"

    class Meta:
        verbose_name = "Rotem Scrape Log"
        verbose_name_plural = "Rotem Scrape Logs"


class MLPrediction(models.Model):
    """ML model predictions"""
    PREDICTION_TYPE_CHOICES = [
        ('anomaly', 'Anomaly Detection'),
        ('failure', 'Equipment Failure'),
        ('optimization', 'Environmental Optimization'),
    ]
    
    controller = models.ForeignKey(RotemController, on_delete=models.CASCADE, related_name='predictions')
    prediction_type = models.CharField(max_length=50, choices=PREDICTION_TYPE_CHOICES)
    predicted_at = models.DateTimeField()
    confidence_score = models.FloatField()
    prediction_data = models.JSONField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.controller.controller_name} - {self.prediction_type}"

    class Meta:
        verbose_name = "ML Prediction"
        verbose_name_plural = "ML Predictions"


class MLModel(models.Model):
    """ML model metadata"""
    name = models.CharField(max_length=100)
    version = models.CharField(max_length=20)
    model_type = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    accuracy_score = models.FloatField(null=True, blank=True)
    training_data_size = models.IntegerField(null=True, blank=True)
    last_trained = models.DateTimeField(null=True, blank=True)
    model_file_path = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} v{self.version}"

    class Meta:
        verbose_name = "ML Model"
        verbose_name_plural = "ML Models"