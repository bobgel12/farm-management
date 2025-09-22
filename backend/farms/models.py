from django.db import models
from django.core.validators import EmailValidator
from django.core.validators import MinValueValidator, MaxValueValidator


class Farm(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    contact_phone = models.CharField(max_length=20)
    contact_email = models.EmailField()
    program = models.ForeignKey('Program', on_delete=models.SET_NULL, null=True, blank=True, related_name='farms')
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


class Program(models.Model):
    """Task program template that defines what tasks to perform on which days"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, help_text="Description of this task program")
    duration_days = models.PositiveIntegerField(
        default=40,
        validators=[MinValueValidator(1), MaxValueValidator(365)],
        help_text="Total duration of the program in days"
    )
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False, help_text="Default program for new farms")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def total_tasks(self):
        return self.tasks.count()

    def save(self, *args, **kwargs):
        # Ensure only one default program exists
        if self.is_default:
            Program.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class ProgramTask(models.Model):
    """Individual task within a program"""
    TASK_TYPES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('one_time', 'One Time'),
        ('recurring', 'Recurring'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='tasks')
    day = models.IntegerField(
        validators=[MinValueValidator(-1), MaxValueValidator(365)],
        help_text="Day of the program when this task should be performed (-1 for setup day)"
    )
    task_type = models.CharField(max_length=20, choices=TASK_TYPES, default='daily')
    title = models.CharField(max_length=200)
    description = models.TextField(help_text="Detailed description of the task")
    instructions = models.TextField(blank=True, help_text="Step-by-step instructions")
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS, default='medium')
    estimated_duration = models.PositiveIntegerField(
        default=30,
        help_text="Estimated duration in minutes"
    )
    is_required = models.BooleanField(default=True, help_text="Is this task required or optional")
    requires_confirmation = models.BooleanField(default=False, help_text="Requires worker confirmation")
    recurring_days = models.JSONField(
        default=list,
        blank=True,
        help_text="For recurring tasks: list of days (0=Monday, 6=Sunday)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['day', 'priority', 'title']
        unique_together = ['program', 'day', 'title']

    def __str__(self):
        return f"Day {self.day}: {self.title}"

    @property
    def is_recurring(self):
        return self.task_type == 'recurring' and bool(self.recurring_days)

    @property
    def is_setup_task(self):
        return self.day == -1