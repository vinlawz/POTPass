from django.db import models

class Location(models.Model):
    name = models.CharField(max_length=50, unique=True, help_text="Branch name (e.g., Swahilipot Hub, Swahilipot FM)")
    code = models.CharField(max_length=10, unique=True, help_text="Branch code (e.g., HUB, FM)", default="")
    is_active = models.BooleanField(default=True, help_text="Whether this branch is active")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        ordering = ['name']
        verbose_name = "Branch"
        verbose_name_plural = "Branches"
