from django.db import models
from django.conf import settings
from core.models import Location

class Pass(models.Model):
    """Represents a visitor pass with strict location isolation"""
    
    PASS_STATUS_CHOICES = (
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    VISITOR_TYPE_CHOICES = (
        ('guest', 'Guest'),
        ('contractor', 'Contractor'),
        ('delivery', 'Delivery'),
        ('staff', 'Staff'),
        ('other', 'Other'),
    )
    
    # Pass Information
    pass_number = models.CharField(max_length=20, unique=True, help_text="Unique pass identifier")
    visitor_name = models.CharField(max_length=100, help_text="Full name of visitor")
    visitor_email = models.EmailField(blank=True, null=True, help_text="Visitor email (optional)")
    visitor_phone = models.CharField(max_length=20, blank=True, null=True, help_text="Visitor phone (optional)")
    visitor_type = models.CharField(max_length=20, choices=VISITOR_TYPE_CHOICES, default='guest')
    
    # Company/Organization (optional)
    company_name = models.CharField(max_length=100, blank=True, null=True, help_text="Company or organization (optional)")
    
    # Purpose of Visit
    purpose = models.TextField(help_text="Purpose of visit")
    
    # Person Being Visited
    host_name = models.CharField(max_length=100, help_text="Person being visited")
    host_department = models.CharField(max_length=50, blank=True, null=True, help_text="Department of host (optional)")
    
    # Timing Information
    check_in_time = models.DateTimeField(auto_now_add=True, help_text="Time of check-in")
    check_out_time = models.DateTimeField(blank=True, null=True, help_text="Time of check-out")
    expected_departure = models.DateTimeField(blank=True, null=True, help_text="Expected departure time")
    
    # Status
    status = models.CharField(max_length=20, choices=PASS_STATUS_CHOICES, default='active')
    
    # Location (automatically inherited from creating user)
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name='passes', help_text="Branch location (auto-inherited)")
    
    # Created by
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_passes', help_text="User who created this pass")
    
    # Notes
    notes = models.TextField(blank=True, null=True, help_text="Additional notes (optional)")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Pass #{self.pass_number} - {self.visitor_name} ({self.location.code})"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Visitor Pass"
        verbose_name_plural = "Visitor Passes"
        indexes = [
            models.Index(fields=['location', 'status']),
            models.Index(fields=['pass_number']),
            models.Index(fields=['created_by']),
        ]

    def save(self, *args, **kwargs):
        # Auto-generate pass number if not provided
        if not self.pass_number:
            last_pass = Pass.objects.filter(location=self.location).order_by('-id').first()
            if last_pass:
                last_number = int(last_pass.pass_number.split('-')[-1]) if '-' in last_pass.pass_number else 0
                self.pass_number = f"{self.location.code}-{last_number + 1:04d}"
            else:
                self.pass_number = f"{self.location.code}-0001"
        
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        return self.status == 'active' and self.check_out_time is None

    @property
    def duration(self):
        if self.check_out_time:
            return self.check_out_time - self.check_in_time
        return None
