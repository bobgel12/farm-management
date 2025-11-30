from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Issue(models.Model):
    """Issue/problem reporting per house"""
    CATEGORY_CHOICES = [
        ('equipment', 'Equipment'),
        ('health', 'Bird Health'),
        ('environment', 'Environmental'),
        ('maintenance', 'Maintenance'),
        ('other', 'Other'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    # Relationships
    house = models.ForeignKey(
        'houses.House',
        on_delete=models.CASCADE,
        related_name='issues',
        help_text="House where the issue occurred"
    )
    
    # Issue details
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        help_text="Category of the issue"
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        help_text="Priority level of the issue"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open',
        help_text="Current status of the issue"
    )
    title = models.CharField(
        max_length=200,
        help_text="Brief title describing the issue"
    )
    description = models.TextField(
        help_text="Detailed description of the issue"
    )
    location_in_house = models.CharField(
        max_length=200,
        blank=True,
        help_text="Specific location within the house (e.g., 'Near feeder line 3')"
    )
    
    # Task creation from issue
    created_task = models.ForeignKey(
        'tasks.Task',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='source_issues',
        help_text="Task created from this issue"
    )
    
    # User tracking
    reported_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reported_issues',
        help_text="User who reported the issue"
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_issues',
        help_text="User assigned to resolve the issue"
    )
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_issues',
        help_text="User who resolved the issue"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Resolution details
    resolution_notes = models.TextField(
        blank=True,
        help_text="Notes about how the issue was resolved"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Issue'
        verbose_name_plural = 'Issues'
        indexes = [
            models.Index(fields=['house', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['priority', '-created_at']),
            models.Index(fields=['reported_by', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.house} ({self.get_status_display()})"
    
    @property
    def is_open(self):
        """Check if issue is still open"""
        return self.status in ['open', 'in_progress']
    
    @property
    def photo_count(self):
        """Get number of photos attached"""
        return self.photos.count()
    
    @property
    def age_hours(self):
        """Get age of issue in hours"""
        delta = timezone.now() - self.created_at
        return delta.total_seconds() / 3600
    
    @property
    def age_display(self):
        """Get human-readable age"""
        hours = self.age_hours
        if hours < 1:
            return f"{int(hours * 60)} minutes ago"
        elif hours < 24:
            return f"{int(hours)} hours ago"
        elif hours < 48:
            return "Yesterday"
        else:
            return f"{int(hours / 24)} days ago"
    
    def resolve(self, resolved_by=None, resolution_notes=''):
        """Mark issue as resolved"""
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        self.resolved_by = resolved_by
        if resolution_notes:
            self.resolution_notes = resolution_notes
        self.save()
    
    def close(self):
        """Close the issue"""
        self.status = 'closed'
        self.save()
    
    def reopen(self):
        """Reopen a resolved/closed issue"""
        self.status = 'open'
        self.resolved_at = None
        self.resolved_by = None
        self.save()


class IssuePhoto(models.Model):
    """Photos attached to issues via Cloudinary"""
    issue = models.ForeignKey(
        Issue,
        on_delete=models.CASCADE,
        related_name='photos',
        help_text="Issue this photo is attached to"
    )
    
    # Cloudinary fields
    cloudinary_url = models.URLField(
        help_text="URL of the image on Cloudinary"
    )
    cloudinary_public_id = models.CharField(
        max_length=255,
        help_text="Cloudinary public ID for the image"
    )
    
    # Photo metadata
    caption = models.CharField(
        max_length=200,
        blank=True,
        help_text="Optional caption for the photo"
    )
    
    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_photos',
        help_text="User who uploaded the photo"
    )
    
    class Meta:
        ordering = ['uploaded_at']
        verbose_name = 'Issue Photo'
        verbose_name_plural = 'Issue Photos'
    
    def __str__(self):
        return f"Photo for {self.issue.title} ({self.uploaded_at})"


class IssueComment(models.Model):
    """Comments on issues for discussion and updates"""
    issue = models.ForeignKey(
        Issue,
        on_delete=models.CASCADE,
        related_name='comments',
        help_text="Issue this comment belongs to"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='issue_comments',
        help_text="User who made the comment"
    )
    content = models.TextField(help_text="Comment content")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Issue Comment'
        verbose_name_plural = 'Issue Comments'
    
    def __str__(self):
        return f"Comment by {self.user} on {self.issue.title}"

