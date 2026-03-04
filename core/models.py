from django.db import models

class Location(models.Model):
    name = models.CharField(max_length=50)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
