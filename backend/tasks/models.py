from django.db import models
from django.utils import timezone
from houses.models import House


class Task(models.Model):
    house = models.ForeignKey(House, on_delete=models.CASCADE)
    day_offset = models.IntegerField()  # -1 to 41
    task_name = models.CharField(max_length=200)
    description = models.TextField()
    task_type = models.CharField(max_length=50, default='general')
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['day_offset', 'task_name']
        unique_together = ['house', 'day_offset', 'task_name']

    def __str__(self):
        return f"{self.house} - Day {self.day_offset}: {self.task_name}"

    def mark_completed(self, completed_by='', notes=''):
        self.is_completed = True
        self.completed_at = timezone.now()
        self.completed_by = completed_by
        self.notes = notes
        self.save()


class RecurringTask(models.Model):
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='weekly')
    day_of_week = models.IntegerField(choices=DAY_CHOICES, null=True, blank=True)
    time = models.TimeField(default='09:00')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class EmailTask(models.Model):
    """Track sent email notifications for task reminders"""
    farm = models.ForeignKey('farms.Farm', on_delete=models.CASCADE)
    sent_date = models.DateField(default=timezone.now)
    sent_time = models.TimeField(default=timezone.now)
    recipients = models.JSONField(help_text="List of email addresses that received the notification")
    subject = models.CharField(max_length=200)
    houses_included = models.JSONField(help_text="List of house IDs included in the email")
    tasks_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['farm', 'sent_date']
        ordering = ['-sent_date', '-sent_time']

    def __str__(self):
        return f"{self.farm.name} - {self.sent_date} ({self.tasks_count} tasks)"