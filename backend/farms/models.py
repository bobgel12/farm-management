from django.db import models
from django.core.validators import EmailValidator
from django.core.validators import MinValueValidator, MaxValueValidator


class Farm(models.Model):
    # Multi-tenancy
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='farms',
        null=True,
        blank=True,
        help_text="Organization this farm belongs to"
    )
    
    # Basic farm information
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=300)
    description = models.TextField(blank=True, help_text="Optional description of the farm")
    contact_person = models.CharField(max_length=100)
    contact_phone = models.CharField(max_length=20)
    contact_email = models.EmailField()
    program = models.ForeignKey('Program', on_delete=models.SET_NULL, null=True, blank=True, related_name='farms')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # System integration fields
    has_system_integration = models.BooleanField(default=False, help_text="Whether this farm has system integration")
    integration_type = models.CharField(
        max_length=50,
        choices=[
            ('none', 'No Integration'),
            ('rotem', 'Rotem System'),
            ('future_system', 'Future System'),
        ],
        default='none',
        help_text="Type of system integration"
    )
    integration_status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('inactive', 'Inactive'),
            ('error', 'Error'),
            ('not_configured', 'Not Configured'),
        ],
        default='not_configured',
        help_text="Current status of the integration"
    )
    last_sync = models.DateTimeField(null=True, blank=True, help_text="Last successful data sync")
    
    # Rotem-specific fields (only used if integration_type='rotem')
    rotem_farm_id = models.CharField(max_length=100, null=True, blank=True, help_text="Rotem system farm ID")
    rotem_username = models.CharField(max_length=200, null=True, blank=True, help_text="Rotem system username")
    rotem_password = models.CharField(max_length=200, null=True, blank=True, help_text="Rotem system password")
    rotem_gateway_name = models.CharField(max_length=100, null=True, blank=True, help_text="Rotem gateway name")
    rotem_gateway_alias = models.CharField(max_length=200, null=True, blank=True, help_text="Rotem gateway alias")

    def __str__(self):
        return self.name

    @property
    def total_houses(self):
        return self.houses.count()

    @property
    def active_houses(self):
        return self.houses.filter(is_active=True).count()
    
    @property
    def is_integrated(self):
        """Check if farm has active system integration"""
        return self.has_system_integration and self.integration_status == 'active'
    
    @property
    def integration_display_name(self):
        """Get human-readable integration type"""
        return dict(self._meta.get_field('integration_type').choices)[self.integration_type]
    
    def save(self, *args, **kwargs):
        # Auto-set has_system_integration based on integration_type
        self.has_system_integration = self.integration_type != 'none'
        super().save(*args, **kwargs)


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


class ProgramChangeLog(models.Model):
    """Track changes to programs and their impact on farms"""
    CHANGE_TYPES = [
        ('task_added', 'Task Added'),
        ('task_modified', 'Task Modified'),
        ('task_deleted', 'Task Deleted'),
        ('program_modified', 'Program Modified'),
    ]
    
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='change_logs')
    change_type = models.CharField(max_length=20, choices=CHANGE_TYPES)
    affected_farms = models.ManyToManyField(Farm, related_name='program_changes', blank=True)
    change_description = models.TextField()
    old_data = models.JSONField(null=True, blank=True, help_text="Previous state of the changed item")
    new_data = models.JSONField(null=True, blank=True, help_text="New state of the changed item")
    user_choice = models.CharField(
        max_length=20,
        choices=[
            ('retroactive', 'Apply to Current Flock'),
            ('next_flock', 'Apply to Next Flock'),
        ],
        null=True,
        blank=True,
        help_text="User's choice for handling existing farm tasks"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.program.name} - {self.get_change_type_display()} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
    
    @property
    def is_processed(self):
        return self.processed_at is not None


class Breed(models.Model):
    """Chicken breed information"""
    name = models.CharField(max_length=100, unique=True, help_text="Breed name (e.g., Cobb 500, Ross 308)")
    code = models.CharField(max_length=50, unique=True, help_text="Breed code/identifier")
    description = models.TextField(blank=True, help_text="Breed description and characteristics")
    
    # Breed characteristics
    average_weight_gain_per_week = models.FloatField(
        null=True, blank=True,
        help_text="Average weight gain per week in grams"
    )
    average_feed_conversion_ratio = models.FloatField(
        null=True, blank=True,
        help_text="Average FCR (Feed Conversion Ratio)"
    )
    average_mortality_rate = models.FloatField(
        null=True, blank=True,
        help_text="Average mortality rate as percentage (0-100)"
    )
    typical_harvest_age_days = models.IntegerField(
        null=True, blank=True,
        help_text="Typical harvest age in days"
    )
    typical_harvest_weight_grams = models.FloatField(
        null=True, blank=True,
        help_text="Typical harvest weight in grams"
    )
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Breed'
        verbose_name_plural = 'Breeds'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name


class Flock(models.Model):
    """Flock/Batch tracking for houses"""
    FLOCK_STATUS_CHOICES = [
        ('setup', 'Setup'),
        ('arrival', 'Arrival'),
        ('growing', 'Growing'),
        ('production', 'Production'),
        ('harvesting', 'Harvesting'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Relationships
    house = models.ForeignKey(
        'houses.House',
        on_delete=models.CASCADE,
        related_name='flocks',
        help_text="House where this flock is located"
    )
    breed = models.ForeignKey(
        Breed,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='flocks',
        help_text="Breed of chickens in this flock"
    )
    
    # Flock identification
    batch_number = models.CharField(max_length=100, help_text="Batch/flock number")
    flock_code = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique flock identifier code"
    )
    
    # Dates
    arrival_date = models.DateField(help_text="Date chickens arrived at the house")
    expected_harvest_date = models.DateField(null=True, blank=True, help_text="Expected harvest date")
    actual_harvest_date = models.DateField(null=True, blank=True, help_text="Actual harvest date")
    start_date = models.DateField(null=True, blank=True, help_text="Flock start date")
    end_date = models.DateField(null=True, blank=True, help_text="Flock end date")
    
    # Initial counts
    initial_chicken_count = models.IntegerField(
        help_text="Initial number of chickens placed"
    )
    current_chicken_count = models.IntegerField(
        null=True, blank=True,
        help_text="Current number of chickens (updated over time)"
    )
    
    # Flock status
    status = models.CharField(
        max_length=20,
        choices=FLOCK_STATUS_CHOICES,
        default='setup',
        help_text="Current flock status"
    )
    is_active = models.BooleanField(default=True, help_text="Whether this flock is currently active")
    
    # Additional metadata
    supplier = models.CharField(max_length=200, blank=True, help_text="Chicken supplier name")
    notes = models.TextField(blank=True, help_text="Additional notes about this flock")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_flocks'
    )
    
    class Meta:
        ordering = ['-arrival_date', 'batch_number']
        verbose_name = 'Flock'
        verbose_name_plural = 'Flocks'
        unique_together = ['house', 'batch_number']
        indexes = [
            models.Index(fields=['flock_code']),
            models.Index(fields=['house', '-arrival_date']),
            models.Index(fields=['status', 'is_active']),
            models.Index(fields=['breed', '-arrival_date']),
        ]
    
    def __str__(self):
        return f"{self.house} - {self.batch_number} ({self.arrival_date})"
    
    @property
    def current_age_days(self):
        """Calculate current flock age in days"""
        from django.utils import timezone
        if not self.arrival_date:
            return None
        
        today = timezone.now().date()
        if self.end_date and today > self.end_date:
            return None  # Flock is completed
        
        return (today - self.arrival_date).days
    
    @property
    def days_until_harvest(self):
        """Calculate days until expected harvest"""
        if not self.expected_harvest_date:
            return None
        
        from django.utils import timezone
        today = timezone.now().date()
        if today > self.expected_harvest_date:
            return 0
        
        return (self.expected_harvest_date - today).days
    
    @property
    def mortality_count(self):
        """Calculate total mortality"""
        if not self.current_chicken_count:
            return None
        return self.initial_chicken_count - self.current_chicken_count
    
    @property
    def mortality_rate(self):
        """Calculate mortality rate as percentage"""
        mortality = self.mortality_count
        if mortality is None or self.initial_chicken_count == 0:
            return None
        return (mortality / self.initial_chicken_count) * 100
    
    @property
    def livability(self):
        """Calculate livability percentage"""
        mortality_rate = self.mortality_rate
        if mortality_rate is None:
            return None
        return 100 - mortality_rate


class FlockPerformance(models.Model):
    """Performance metrics for a flock at a specific point in time"""
    flock = models.ForeignKey(
        Flock,
        on_delete=models.CASCADE,
        related_name='performance_records',
        help_text="Flock this performance record belongs to"
    )
    
    # Date and age
    record_date = models.DateField(help_text="Date of this performance record")
    flock_age_days = models.IntegerField(help_text="Flock age in days at record date")
    
    # Weight metrics
    average_weight_grams = models.FloatField(
        null=True, blank=True,
        help_text="Average weight per chicken in grams"
    )
    total_weight_kg = models.FloatField(
        null=True, blank=True,
        help_text="Total flock weight in kg"
    )
    
    # Feed metrics
    feed_consumed_kg = models.FloatField(
        null=True, blank=True,
        help_text="Total feed consumed in kg (cumulative or for period)"
    )
    daily_feed_consumption_kg = models.FloatField(
        null=True, blank=True,
        help_text="Daily feed consumption in kg"
    )
    feed_conversion_ratio = models.FloatField(
        null=True, blank=True,
        help_text="Feed Conversion Ratio (FCR)"
    )
    
    # Water metrics
    daily_water_consumption_liters = models.FloatField(
        null=True, blank=True,
        help_text="Daily water consumption in liters"
    )
    
    # Counts
    current_chicken_count = models.IntegerField(
        help_text="Current number of chickens"
    )
    mortality_count = models.IntegerField(
        default=0,
        help_text="Number of deaths (cumulative or for period)"
    )
    
    # Health metrics
    mortality_rate = models.FloatField(
        null=True, blank=True,
        help_text="Mortality rate as percentage"
    )
    livability = models.FloatField(
        null=True, blank=True,
        help_text="Livability percentage"
    )
    
    # Environmental metrics (if available)
    average_temperature = models.FloatField(null=True, blank=True)
    average_humidity = models.FloatField(null=True, blank=True)
    
    # Additional notes
    notes = models.TextField(blank=True, help_text="Additional notes for this record")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    recorded_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_flock_performance'
    )
    
    class Meta:
        ordering = ['flock', 'record_date', 'flock_age_days']
        verbose_name = 'Flock Performance'
        verbose_name_plural = 'Flock Performance Records'
        unique_together = ['flock', 'record_date', 'flock_age_days']
        indexes = [
            models.Index(fields=['flock', '-record_date']),
            models.Index(fields=['flock', 'flock_age_days']),
            models.Index(fields=['record_date']),
        ]
    
    def __str__(self):
        return f"{self.flock} - Day {self.flock_age_days} ({self.record_date})"
    
    def calculate_fcr(self):
        """Calculate FCR if data is available"""
        if self.feed_consumed_kg and self.total_weight_kg and self.total_weight_kg > 0:
            # FCR = Feed consumed / Weight gain
            # Weight gain = Total weight - initial weight
            # For simplicity, we'll calculate based on total weight
            # More accurate would be to track weight gain
            pass  # FCR calculation can be complex, handle in service layer
    
    def save(self, *args, **kwargs):
        """Calculate derived metrics before saving"""
        # Calculate mortality rate if possible
        if self.flock and self.current_chicken_count:
            initial_count = self.flock.initial_chicken_count
            if initial_count > 0:
                self.mortality_rate = ((initial_count - self.current_chicken_count) / initial_count) * 100
                self.livability = 100 - self.mortality_rate
        
        super().save(*args, **kwargs)


class FlockComparison(models.Model):
    """Saved comparison between multiple flocks"""
    name = models.CharField(max_length=200, help_text="Comparison name")
    description = models.TextField(blank=True)
    
    # Flocks being compared
    flocks = models.ManyToManyField(
        Flock,
        related_name='comparisons',
        help_text="Flocks included in this comparison"
    )
    
    # Comparison criteria
    comparison_metrics = models.JSONField(
        default=list,
        help_text="List of metrics to compare (e.g., ['fcr', 'mortality_rate', 'weight_gain'])"
    )
    
    # Results (cached)
    comparison_results = models.JSONField(
        null=True, blank=True,
        help_text="Cached comparison results"
    )
    
    # Metadata
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='flock_comparisons'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Flock Comparison'
        verbose_name_plural = 'Flock Comparisons'
    
    def __str__(self):
        return f"{self.name} ({self.flocks.count()} flocks)"