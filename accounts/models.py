from django.contrib.auth.models import AbstractUser
from django.db import models
from core.models import Location

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("receptionist", "Receptionist"),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    assigned_location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name='assigned_users')
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True, help_text="Upload your profile picture")

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
