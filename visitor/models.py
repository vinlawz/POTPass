from django.db import models
from django.conf import settings
from django.utils import timezone

class Visitor(models.Model):
    """Visitor model representing people who can visit locations"""
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    full_name = models.CharField(max_length=100, help_text="Visitor's full name")
    phone = models.CharField(max_length=20, help_text="Primary phone number")
    id_number = models.CharField(max_length=50, blank=True, null=True, help_text="National ID or passport number")
    organization = models.CharField(max_length=100, blank=True, null=True, help_text="Company or organization")
    email = models.EmailField(blank=True, null=True, help_text="Email address")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True, help_text="Date of birth")
    address = models.TextField(blank=True, null=True, help_text="Physical address")
    
    # System fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Visitor"
        verbose_name_plural = "Visitors"
    
    def __str__(self):
        return f"{self.full_name} ({self.phone})"
    
    @property
    def active_visit(self):
        """Get the currently active visit for this visitor"""
        return self.visits.filter(status='ACTIVE').first()

class Visit(models.Model):
    """Visit model tracking visitor check-ins and check-outs"""
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    visitor = models.ForeignKey(Visitor, on_delete=models.PROTECT, related_name='visits')
    location = models.ForeignKey('core.Location', on_delete=models.PROTECT, related_name='visits')
    purpose = models.CharField(max_length=200, help_text="Purpose of visit")
    host = models.CharField(max_length=100, blank=True, null=True, help_text="Person being visited")
    host_department = models.CharField(max_length=100, blank=True, null=True, help_text="Department of host")
    
    # Timing fields
    check_in_time = models.DateTimeField(help_text="Time of check-in")
    check_out_time = models.DateTimeField(null=True, blank=True, help_text="Time of check-out")
    
    # Status and metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    notes = models.TextField(blank=True, null=True, help_text="Additional notes about the visit")
    
    # System fields
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_visits')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-check_in_time']
        verbose_name = "Visit"
        verbose_name_plural = "Visits"
        indexes = [
            models.Index(fields=['visitor', 'location', 'status']),
            models.Index(fields=['visitor', 'status']),
            models.Index(fields=['check_in_time']),
        ]
    
    def __str__(self):
        return f"{self.visitor.full_name} - {self.check_in_time.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def duration(self):
        """Calculate visit duration"""
        if self.check_out_time:
            duration = self.check_out_time - self.check_in_time
            hours = duration.total_seconds() / 3600
            if hours < 1:
                minutes = duration.total_seconds() / 60
                return f"{int(minutes)} minutes"
            else:
                return f"{hours:.1f} hours"
        else:
            # Active visit - show duration from check-in to now
            duration = timezone.now() - self.check_in_time
            hours = duration.total_seconds() / 3600
            if hours < 1:
                minutes = duration.total_seconds() / 60
                return f"{int(minutes)} minutes"
            else:
                return f"{int(hours)}h {int((hours % 1) * 60)}m"
    
    @property
    def is_active(self):
        """Check if visit is currently active"""
        return self.status == 'ACTIVE' and self.check_out_time is None
    
    def check_out(self):
        """Check out the visitor"""
        self.check_out_time = timezone.now()
        self.status = 'COMPLETED'
        self.save()

class AuditLog(models.Model):
    """Optional audit log for tracking all visitor management actions"""
    
    ACTION_CHOICES = [
        ('CHECK_IN', 'Check In'),
        ('CHECK_OUT', 'Check Out'),
        ('CREATE_VISITOR', 'Create Visitor'),
        ('UPDATE_VISITOR', 'Update Visitor'),
        ('CANCEL_VISIT', 'Cancel Visit'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='audit_logs', null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    visit = models.ForeignKey(Visit, on_delete=models.PROTECT, related_name='audit_logs', null=True, blank=True)
    visitor = models.ForeignKey(Visitor, on_delete=models.PROTECT, related_name='audit_logs', null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True, help_text="Additional context about the action")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
