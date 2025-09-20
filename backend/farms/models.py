from django.db import models
from django.core.validators import EmailValidator


class Farm(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    contact_phone = models.CharField(max_length=20)
    contact_email = models.EmailField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def total_houses(self):
        return self.houses.count()

    @property
    def active_houses(self):
        return self.houses.filter(is_active=True).count()


class Worker(models.Model):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='workers')
    name = models.CharField(max_length=100)
    email = models.EmailField(validators=[EmailValidator()])
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=50, blank=True, help_text="e.g., Manager, Supervisor, Worker")
    is_active = models.BooleanField(default=True)
    receive_daily_tasks = models.BooleanField(default=True, help_text="Receive daily task reminders")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['farm', 'email']

    def __str__(self):
        return f"{self.name} ({self.farm.name})"