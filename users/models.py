from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # Additional fields for KG Portal
    designation = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., Student, Faculty, Security")
    contact_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.username
